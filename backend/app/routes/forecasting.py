"""
Blood Demand Forecasting API Routes

Endpoints for ML-based demand forecasting, alerts, and redistribution
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.models import (
    DemandForecast, DemandHistory, InventoryLevel, 
    Hospital, Donor, Request, RequestStatus
)
from app.schemas.schemas import (
    DemandForecastResponse, InventoryLevelResponse, 
    InventoryUpdate, DemandHistoryCreate
)
from app.services.forecasting import get_forecaster, BloodDemandForecaster
from app.services.redistribution import BloodRedistributor

router = APIRouter()


# ============ Pydantic Models ============

class ForecastRequest(BaseModel):
    """Request model for generating forecasts"""
    hours_ahead: int = Field(default=48, ge=1, le=168, description="Hours to forecast ahead (1-168)")
    regions: Optional[List[str]] = Field(None, description="Specific regions to forecast (None = all)")
    retrain: bool = Field(default=False, description="Force model retraining")


class AlertRequest(BaseModel):
    """Request model for generating alerts"""
    forecast_id: Optional[int] = Field(None, description="Specific forecast ID to alert on")
    min_risk_level: str = Field(default="High", description="Minimum risk level to alert on")


class RedistributionRequest(BaseModel):
    """Request model for redistribution"""
    from_hospital_id: int
    to_hospital_id: int
    blood_type: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$")
    units: int = Field(..., ge=1)


class TrainingStatus(BaseModel):
    """Model training status"""
    is_trained: bool
    model_exists: bool
    last_trained: Optional[str] = None


class ForecastSummary(BaseModel):
    """Summary of forecast results"""
    total_forecasts: int
    critical_risk_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    regions_covered: List[str]
    blood_types_covered: List[str]


# ============ Helper Functions ============

def send_alert_to_volunteers(
    db: Session, 
    forecast: DemandForecast
) -> Dict:
    """
    Send alert to volunteers about predicted shortage
    
    In production, this would:
    - Send push notifications
    - Send SMS/email alerts
    - Broadcast via Socket.IO
    
    For now, returns alert details
    """
    # Get available donors for this blood type
    available_donors = db.query(Donor).filter(
        and_(
            Donor.blood_group == forecast.blood_type,
            Donor.available == True
        )
    ).limit(10).all()
    
    alert_data = {
        "alert_type": "blood_shortage_prediction",
        "blood_type": forecast.blood_type,
        "region": forecast.region,
        "predicted_demand": forecast.predicted_demand,
        "shortage_risk": forecast.shortage_risk,
        "forecast_date": forecast.forecast_date.isoformat(),
        "message": (
            f"⚠️ {forecast.shortage_risk} risk of {forecast.blood_type} shortage "
            f"in {forecast.region} predicted for {forecast.forecast_date.strftime('%Y-%m-%d %H:%M')}. "
            f"Expected demand: {int(forecast.predicted_demand)} units."
        ),
        "notified_donors": len(available_donors),
        "call_to_action": "Please schedule a donation appointment if you are available."
    }
    
    # Mark alert as sent
    forecast.alert_sent = True
    db.commit()
    
    return alert_data


# ============ API Endpoints ============

@router.post(
    "/train",
    status_code=status.HTTP_200_OK,
    summary="Train demand forecasting model",
    description="Train or retrain the ML model for blood demand forecasting using historical data."
)
async def train_model(
    force_retrain: bool = False,
    db: Session = Depends(get_db)
):
    """
    Train the demand forecasting model.
    
    **Query Parameters:**
    - `force_retrain` (optional): Force retraining even if model exists (default: False)
    
    **Returns:**
    - Training status and metrics
    
    **Example:**
    - `POST /forecasting/train?force_retrain=true`
    """
    try:
        forecaster = get_forecaster()
        forecaster.train_model(db, force_retrain=force_retrain)
        
        return {
            "success": True,
            "message": "Model trained successfully",
            "is_trained": forecaster.is_trained,
            "model_path": forecaster.model_path
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error training model: {str(e)}"
        )


@router.get(
    "/training-status",
    response_model=TrainingStatus,
    status_code=status.HTTP_200_OK,
    summary="Get model training status",
    description="Check if the forecasting model is trained and ready."
)
async def get_training_status():
    """
    Get training status of the forecasting model.
    
    **Returns:**
    - Model training status information
    """
    try:
        forecaster = get_forecaster()
        
        import os
        model_exists = os.path.exists(forecaster.model_path)
        
        return TrainingStatus(
            is_trained=forecaster.is_trained,
            model_exists=model_exists,
            last_trained=None  # Could be enhanced to track this
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking training status: {str(e)}"
        )


@router.post(
    "/generate",
    response_model=List[DemandForecastResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate demand forecasts",
    description="Generate blood demand forecasts for the next 24-48 hours using ML model."
)
async def generate_forecasts(
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate demand forecasts.
    
    **Request Body:**
    - `hours_ahead` (optional): Hours to forecast ahead (default: 48, max: 168)
    - `regions` (optional): List of regions to forecast for (default: all)
    - `retrain` (optional): Force model retraining (default: false)
    
    **Returns:**
    - List of demand forecasts with predictions and risk levels
    
    **Example Request:**
    ```json
    {
        "hours_ahead": 48,
        "regions": ["South Delhi", "Noida"],
        "retrain": false
    }
    ```
    """
    try:
        forecaster = get_forecaster()
        
        # Train model if needed
        if request.retrain or not forecaster.is_trained:
            forecaster.train_model(db, force_retrain=request.retrain)
        
        # Generate forecasts
        forecasts = forecaster.generate_forecasts(
            db, 
            hours_ahead=request.hours_ahead,
            regions=request.regions
        )
        
        # Save forecasts to database
        for forecast in forecasts:
            db.add(forecast)
        
        db.commit()
        
        # Refresh to get IDs
        for forecast in forecasts:
            db.refresh(forecast)
        
        return forecasts
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating forecasts: {str(e)}"
        )


@router.get(
    "/forecasts",
    response_model=List[DemandForecastResponse],
    status_code=status.HTTP_200_OK,
    summary="Get demand forecasts",
    description="Retrieve saved demand forecasts, optionally filtered by risk level, blood type, or region."
)
async def get_forecasts(
    blood_type: Optional[str] = None,
    region: Optional[str] = None,
    min_risk: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get saved demand forecasts.
    
    **Query Parameters:**
    - `blood_type` (optional): Filter by blood type
    - `region` (optional): Filter by region
    - `min_risk` (optional): Minimum risk level (Low, Medium, High, Critical)
    - `limit` (optional): Maximum number of results (default: 50)
    
    **Returns:**
    - List of demand forecasts
    
    **Example:**
    - `GET /forecasting/forecasts?blood_type=O+&min_risk=High`
    """
    try:
        query = db.query(DemandForecast)
        
        if blood_type:
            query = query.filter(DemandForecast.blood_type == blood_type)
        
        if region:
            query = query.filter(DemandForecast.region == region)
        
        if min_risk:
            risk_levels = ["Low", "Medium", "High", "Critical"]
            if min_risk in risk_levels:
                min_index = risk_levels.index(min_risk)
                allowed_risks = risk_levels[min_index:]
                query = query.filter(DemandForecast.shortage_risk.in_(allowed_risks))
        
        # Get most recent forecasts first
        forecasts = query.order_by(
            DemandForecast.created_at.desc()
        ).limit(limit).all()
        
        return forecasts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving forecasts: {str(e)}"
        )


@router.get(
    "/forecasts/summary",
    response_model=ForecastSummary,
    status_code=status.HTTP_200_OK,
    summary="Get forecast summary",
    description="Get summary statistics of recent demand forecasts."
)
async def get_forecast_summary(
    hours_back: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get summary of recent forecasts.
    
    **Query Parameters:**
    - `hours_back` (optional): Hours to look back (default: 24)
    
    **Returns:**
    - Summary statistics of forecasts
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        forecasts = db.query(DemandForecast).filter(
            DemandForecast.created_at >= cutoff_time
        ).all()
        
        risk_counts = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0
        }
        
        for forecast in forecasts:
            risk_counts[forecast.shortage_risk] = risk_counts.get(forecast.shortage_risk, 0) + 1
        
        return ForecastSummary(
            total_forecasts=len(forecasts),
            critical_risk_count=risk_counts["Critical"],
            high_risk_count=risk_counts["High"],
            medium_risk_count=risk_counts["Medium"],
            low_risk_count=risk_counts["Low"],
            regions_covered=list(set(f.region for f in forecasts)),
            blood_types_covered=list(set(f.blood_type for f in forecasts))
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )


@router.post(
    "/alerts/send",
    status_code=status.HTTP_200_OK,
    summary="Send shortage alerts",
    description="Send alerts to volunteers about predicted blood shortages."
)
async def send_alerts(
    request: AlertRequest,
    db: Session = Depends(get_db)
):
    """
    Send alerts to volunteers about predicted shortages.
    
    **Request Body:**
    - `forecast_id` (optional): Specific forecast to alert on
    - `min_risk_level` (optional): Minimum risk level to alert on (default: High)
    
    **Returns:**
    - List of alerts sent
    
    **Example Request:**
    ```json
    {
        "min_risk_level": "High"
    }
    ```
    """
    try:
        if request.forecast_id:
            # Alert on specific forecast
            forecast = db.query(DemandForecast).filter(
                DemandForecast.id == request.forecast_id
            ).first()
            
            if not forecast:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Forecast with ID {request.forecast_id} not found"
                )
            
            alert = send_alert_to_volunteers(db, forecast)
            return {"alerts_sent": [alert]}
        
        else:
            # Alert on all high-risk forecasts that haven't been alerted yet
            risk_levels = ["Low", "Medium", "High", "Critical"]
            min_index = risk_levels.index(request.min_risk_level)
            allowed_risks = risk_levels[min_index:]
            
            forecasts = db.query(DemandForecast).filter(
                and_(
                    DemandForecast.shortage_risk.in_(allowed_risks),
                    DemandForecast.alert_sent == False,
                    DemandForecast.forecast_date > datetime.now()  # Only future forecasts
                )
            ).all()
            
            alerts = []
            for forecast in forecasts:
                alert = send_alert_to_volunteers(db, forecast)
                alerts.append(alert)
            
            return {
                "alerts_sent": alerts,
                "total_alerts": len(alerts)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending alerts: {str(e)}"
        )


@router.get(
    "/inventory",
    response_model=List[InventoryLevelResponse],
    status_code=status.HTTP_200_OK,
    summary="Get inventory levels",
    description="Get current blood inventory levels across hospitals."
)
async def get_inventory(
    blood_type: Optional[str] = None,
    hospital_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get current inventory levels.
    
    **Query Parameters:**
    - `blood_type` (optional): Filter by blood type
    - `hospital_id` (optional): Filter by hospital ID
    
    **Returns:**
    - List of inventory levels
    """
    try:
        query = db.query(InventoryLevel)
        
        if blood_type:
            query = query.filter(InventoryLevel.blood_type == blood_type)
        
        if hospital_id:
            query = query.filter(InventoryLevel.hospital_id == hospital_id)
        
        inventories = query.all()
        return inventories
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving inventory: {str(e)}"
        )


@router.post(
    "/inventory/update",
    response_model=InventoryLevelResponse,
    status_code=status.HTTP_200_OK,
    summary="Update inventory level",
    description="Update blood inventory level for a hospital."
)
async def update_inventory(
    update: InventoryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update inventory level.
    
    **Request Body:**
    - `hospital_id` (required): Hospital ID
    - `blood_type` (required): Blood type
    - `current_units` (required): New inventory level
    
    **Returns:**
    - Updated inventory level
    """
    try:
        # Find or create inventory record
        inventory = db.query(InventoryLevel).filter(
            and_(
                InventoryLevel.hospital_id == update.hospital_id,
                InventoryLevel.blood_type == update.blood_type
            )
        ).first()
        
        if inventory:
            inventory.current_units = update.current_units
        else:
            inventory = InventoryLevel(
                hospital_id=update.hospital_id,
                blood_type=update.blood_type,
                current_units=update.current_units,
                min_required=10,
                max_capacity=100
            )
            db.add(inventory)
        
        db.commit()
        db.refresh(inventory)
        
        return inventory
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating inventory: {str(e)}"
        )


@router.get(
    "/redistribution/opportunities",
    status_code=status.HTTP_200_OK,
    summary="Get redistribution opportunities",
    description="Identify opportunities for blood redistribution based on current inventory."
)
async def get_redistribution_opportunities(
    blood_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get redistribution opportunities.
    
    **Query Parameters:**
    - `blood_type` (optional): Filter by blood type
    
    **Returns:**
    - List of redistribution recommendations
    """
    try:
        redistributor = BloodRedistributor(db)
        opportunities = redistributor.identify_redistribution_opportunities(
            blood_type=blood_type
        )
        
        return {
            "opportunities": opportunities,
            "total_opportunities": len(opportunities)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error identifying opportunities: {str(e)}"
        )


@router.post(
    "/redistribution/execute",
    status_code=status.HTTP_200_OK,
    summary="Execute redistribution",
    description="Execute a blood redistribution between hospitals."
)
async def execute_redistribution(
    request: RedistributionRequest,
    db: Session = Depends(get_db)
):
    """
    Execute blood redistribution.
    
    **Request Body:**
    - `from_hospital_id` (required): Source hospital ID
    - `to_hospital_id` (required): Destination hospital ID
    - `blood_type` (required): Blood type to transfer
    - `units` (required): Number of units to transfer
    
    **Returns:**
    - Redistribution result
    
    **Example Request:**
    ```json
    {
        "from_hospital_id": 1,
        "to_hospital_id": 2,
        "blood_type": "O+",
        "units": 10
    }
    ```
    """
    try:
        redistributor = BloodRedistributor(db)
        result = redistributor.execute_redistribution(
            from_hospital_id=request.from_hospital_id,
            to_hospital_id=request.to_hospital_id,
            blood_type=request.blood_type,
            units=request.units
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing redistribution: {str(e)}"
        )


@router.get(
    "/redistribution/summary",
    status_code=status.HTTP_200_OK,
    summary="Get redistribution summary",
    description="Get overall redistribution summary and statistics."
)
async def get_redistribution_summary(
    db: Session = Depends(get_db)
):
    """
    Get redistribution summary.
    
    **Returns:**
    - Summary statistics and metrics
    """
    try:
        redistributor = BloodRedistributor(db)
        summary = redistributor.get_redistribution_summary()
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )


@router.post(
    "/redistribution/forecast-based",
    status_code=status.HTTP_200_OK,
    summary="Get forecast-based redistribution plan",
    description="Generate redistribution plan based on demand forecasts."
)
async def get_forecast_based_redistribution(
    threshold_risk: str = "High",
    db: Session = Depends(get_db)
):
    """
    Get forecast-based redistribution recommendations.
    
    **Query Parameters:**
    - `threshold_risk` (optional): Minimum risk level to consider (default: High)
    
    **Returns:**
    - Redistribution plan based on forecasts
    """
    try:
        # Get recent forecasts
        recent_forecasts = db.query(DemandForecast).filter(
            DemandForecast.forecast_date > datetime.now()
        ).all()
        
        if not recent_forecasts:
            return {
                "plan": [],
                "message": "No forecasts available. Generate forecasts first."
            }
        
        redistributor = BloodRedistributor(db)
        plan = redistributor.apply_forecast_based_redistribution(
            forecasts=recent_forecasts,
            threshold_risk=threshold_risk
        )
        
        return {
            "plan": plan,
            "total_actions": len(plan),
            "threshold_risk": threshold_risk
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating redistribution plan: {str(e)}"
        )
