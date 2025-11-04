# Blood Demand Forecasting & Redistribution Guide

## Overview

The Blood Demand Forecasting system uses Machine Learning to predict blood shortages 24-48 hours in advance. This allows NSS BloodLink to proactively alert volunteers and redistribute blood inventory before critical shortages occur.

## Key Features

### 1. Predictive Forecasting
- **ML Model**: Random Forest Regressor trained on historical demand patterns
- **Forecast Window**: 24-168 hours ahead (configurable)
- **Accuracy**: Confidence scoring for each prediction (0.5-0.95)
- **Seasonal Awareness**: Detects patterns like post-monsoon dengue/malaria spikes

### 2. Risk Assessment
Four risk levels based on demand vs inventory:
- **Low**: 3+ days of supply available
- **Medium**: 2-3 days of supply
- **High**: 1-2 days of supply
- **Critical**: Less than 1 day of supply

### 3. Intelligent Redistribution
- Identifies surplus and shortage hospitals
- Priority-based matching algorithm
- Considers geographic proximity
- Forecast-driven planning

### 4. Auto-Alerting
- Alerts volunteers when high/critical risk is detected
- Sends notifications to matching blood group donors
- Includes predicted demand and timeframe

## API Usage

### Setup and Training

#### 1. Train the ML Model
```bash
POST /forecasting/train
```

First-time setup or retrain with new data:
```bash
curl -X POST "http://localhost:8000/forecasting/train?force_retrain=true"
```

Response:
```json
{
  "success": true,
  "message": "Model trained successfully",
  "is_trained": true,
  "model_path": "/tmp/blood_demand_model.pkl"
}
```

#### 2. Check Training Status
```bash
GET /forecasting/training-status
```

Example:
```bash
curl http://localhost:8000/forecasting/training-status
```

Response:
```json
{
  "is_trained": true,
  "model_exists": true,
  "last_trained": null
}
```

### Generating Forecasts

#### Generate New Forecasts
```bash
POST /forecasting/generate
```

Generate forecasts for specific regions:
```bash
curl -X POST http://localhost:8000/forecasting/generate \
  -H "Content-Type: application/json" \
  -d '{
    "hours_ahead": 48,
    "regions": ["South Delhi", "Noida"],
    "retrain": false
  }'
```

Generate for all regions with default settings (48 hours):
```bash
curl -X POST http://localhost:8000/forecasting/generate \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response (partial):
```json
[
  {
    "id": 1,
    "blood_type": "O+",
    "region": "South Delhi",
    "forecast_date": "2025-11-06T20:23:24",
    "predicted_demand": 61.99,
    "confidence": 0.95,
    "shortage_risk": "Critical",
    "alert_sent": false,
    "created_at": "2025-11-04T20:23:24"
  }
]
```

#### Retrieve Forecasts
```bash
GET /forecasting/forecasts
```

Filter by blood type and risk level:
```bash
curl "http://localhost:8000/forecasting/forecasts?blood_type=O%2B&min_risk=High&limit=10"
```

#### Get Forecast Summary
```bash
GET /forecasting/forecasts/summary
```

Example:
```bash
curl "http://localhost:8000/forecasting/forecasts/summary?hours_back=24"
```

Response:
```json
{
  "total_forecasts": 16,
  "critical_risk_count": 4,
  "high_risk_count": 2,
  "medium_risk_count": 0,
  "low_risk_count": 10,
  "regions_covered": ["Noida", "South Delhi"],
  "blood_types_covered": ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
}
```

### Alerting System

#### Send Shortage Alerts
```bash
POST /forecasting/alerts/send
```

Alert on all high-risk forecasts:
```bash
curl -X POST http://localhost:8000/forecasting/alerts/send \
  -H "Content-Type: application/json" \
  -d '{
    "min_risk_level": "High"
  }'
```

Alert on specific forecast:
```bash
curl -X POST http://localhost:8000/forecasting/alerts/send \
  -H "Content-Type: application/json" \
  -d '{
    "forecast_id": 1
  }'
```

Response:
```json
{
  "alerts_sent": [
    {
      "alert_type": "blood_shortage_prediction",
      "blood_type": "O+",
      "region": "South Delhi",
      "predicted_demand": 61.99,
      "shortage_risk": "Critical",
      "forecast_date": "2025-11-06T20:23:24",
      "message": "⚠️ Critical risk of O+ shortage in South Delhi predicted for 2025-11-06 20:23. Expected demand: 61 units.",
      "notified_donors": 10,
      "call_to_action": "Please schedule a donation appointment if you are available."
    }
  ],
  "total_alerts": 1
}
```

### Inventory Management

#### View Inventory Levels
```bash
GET /forecasting/inventory
```

View all inventory:
```bash
curl http://localhost:8000/forecasting/inventory
```

Filter by blood type or hospital:
```bash
curl "http://localhost:8000/forecasting/inventory?blood_type=O%2B&hospital_id=1"
```

Response:
```json
[
  {
    "id": 1,
    "hospital_id": 1,
    "blood_type": "O+",
    "current_units": 42,
    "min_required": 20,
    "max_capacity": 100,
    "last_updated": "2025-11-04T20:22:32",
    "hospital": {
      "name": "Apollo Hospital",
      "location": "Delhi"
    }
  }
]
```

#### Update Inventory
```bash
POST /forecasting/inventory/update
```

Example:
```bash
curl -X POST http://localhost:8000/forecasting/inventory/update \
  -H "Content-Type: application/json" \
  -d '{
    "hospital_id": 1,
    "blood_type": "O+",
    "current_units": 50
  }'
```

### Redistribution System

#### Get Redistribution Opportunities
```bash
GET /forecasting/redistribution/opportunities
```

Find all opportunities:
```bash
curl http://localhost:8000/forecasting/redistribution/opportunities
```

Filter by blood type:
```bash
curl "http://localhost:8000/forecasting/redistribution/opportunities?blood_type=O%2B"
```

Response:
```json
{
  "opportunities": [
    {
      "from_hospital_id": 2,
      "from_hospital_name": "AIIMS",
      "to_hospital_id": 6,
      "to_hospital_name": "BLK Hospital",
      "blood_type": "O+",
      "transfer_units": 14,
      "priority": 140.0,
      "reason": "BLK Hospital has 14 unit shortage while AIIMS has 24 unit surplus"
    }
  ],
  "total_opportunities": 1
}
```

#### Execute Redistribution
```bash
POST /forecasting/redistribution/execute
```

Transfer blood between hospitals:
```bash
curl -X POST http://localhost:8000/forecasting/redistribution/execute \
  -H "Content-Type: application/json" \
  -d '{
    "from_hospital_id": 2,
    "to_hospital_id": 6,
    "blood_type": "O+",
    "units": 10
  }'
```

Response:
```json
{
  "success": true,
  "from_hospital_id": 2,
  "to_hospital_id": 6,
  "blood_type": "O+",
  "units_transferred": 10,
  "source_remaining": 44,
  "dest_new_level": 16
}
```

#### Get Forecast-Based Redistribution Plan
```bash
POST /forecasting/redistribution/forecast-based
```

Generate redistribution plan based on predictions:
```bash
curl -X POST "http://localhost:8000/forecasting/redistribution/forecast-based?threshold_risk=High"
```

Response:
```json
{
  "plan": [
    {
      "from_hospital_id": 2,
      "from_hospital_name": "AIIMS",
      "to_hospital_id": 6,
      "to_hospital_name": "BLK Hospital",
      "blood_type": "O+",
      "transfer_units": 14,
      "priority": 140.0,
      "reason": "BLK Hospital has 14 unit shortage while AIIMS has 24 unit surplus",
      "forecast_based": true,
      "predicted_shortage_regions": ["South Delhi", "Noida"]
    }
  ],
  "total_actions": 1,
  "threshold_risk": "High"
}
```

#### Get Redistribution Summary
```bash
GET /forecasting/redistribution/summary
```

Example:
```bash
curl http://localhost:8000/forecasting/redistribution/summary
```

Response:
```json
{
  "total_hospitals": 6,
  "total_inventory_records": 48,
  "critical_count": 5,
  "low_count": 6,
  "adequate_count": 37,
  "excess_count": 0,
  "total_shortage_units": 85,
  "total_surplus_units": 818,
  "redistribution_potential": 85,
  "blood_types_tracked": 8
}
```

## Seasonal Patterns

The forecasting model recognizes four seasons based on Indian climate:

### Winter (Dec-Feb)
- Base demand (1.0x multiplier)
- Lower disease incidence

### Summer (Mar-May)
- Slightly lower demand (0.9x multiplier)
- Reduced outdoor activities

### Monsoon (Jun-Sep)
- Increased demand (1.3x multiplier)
- Higher accident rates
- Beginning of disease season

### Post-Monsoon (Oct-Nov)
- **Highest demand** (1.8x multiplier)
- Peak dengue and malaria cases
- Critical period for blood shortage

## Use Cases

### 1. Proactive Blood Collection Drives
Before monsoon season:
```bash
# Generate 7-day forecast
curl -X POST http://localhost:8000/forecasting/generate \
  -d '{"hours_ahead": 168}'

# Check for high-risk forecasts
curl "http://localhost:8000/forecasting/forecasts?min_risk=High"

# Send alerts to donors
curl -X POST http://localhost:8000/forecasting/alerts/send \
  -d '{"min_risk_level": "Medium"}'
```

### 2. Emergency Response
During disease outbreak:
```bash
# Generate immediate forecast
curl -X POST http://localhost:8000/forecasting/generate \
  -d '{"hours_ahead": 24}'

# Get redistribution plan
curl -X POST http://localhost:8000/forecasting/redistribution/forecast-based

# Execute critical transfers
curl -X POST http://localhost:8000/forecasting/redistribution/execute \
  -d '{"from_hospital_id": 1, "to_hospital_id": 2, "blood_type": "O+", "units": 20}'
```

### 3. Regular Monitoring
Daily operations:
```bash
# Update inventory levels
curl -X POST http://localhost:8000/forecasting/inventory/update \
  -d '{"hospital_id": 1, "blood_type": "O+", "current_units": 45}'

# Check redistribution opportunities
curl http://localhost:8000/forecasting/redistribution/opportunities

# View summary statistics
curl http://localhost:8000/forecasting/redistribution/summary
```

## Integration with Existing Features

### With Donor Management
Forecasts automatically notify available donors matching predicted shortage blood types.

### With Request System
High-risk forecasts can trigger automatic request creation for hospitals.

### With Real-time Updates
Alerts are broadcast via Socket.IO to connected clients.

## Best Practices

1. **Train regularly**: Retrain the model weekly or after significant data changes
2. **Monitor forecasts**: Check summary daily for early warning signs
3. **Act on Critical risks**: Immediately alert and redistribute for Critical forecasts
4. **Update inventory**: Keep inventory levels current for accurate redistribution
5. **Validate predictions**: Compare actual vs predicted demand to improve model

## Technical Details

### ML Model Specifications
- **Algorithm**: Random Forest Regressor
- **Features**: Blood type, region, season, day of week, month, disease outbreak flag
- **Training data**: 365 days of synthetic historical patterns
- **Evaluation**: R² score on training data

### Data Models
- **DemandHistory**: Historical demand records
- **DemandForecast**: Predicted demand with risk assessment
- **InventoryLevel**: Current blood stock by hospital

### Performance
- Training time: ~5-10 seconds
- Forecast generation: <1 second for all blood types and regions
- API response time: <100ms for most endpoints

## Troubleshooting

### Model not trained
```bash
# Error: "Model must be trained before making predictions"
# Solution: Train the model
curl -X POST http://localhost:8000/forecasting/train
```

### No forecasts available
```bash
# Error: "No forecasts available"
# Solution: Generate forecasts
curl -X POST http://localhost:8000/forecasting/generate -d '{}'
```

### Insufficient inventory
```bash
# Error: "Insufficient inventory at source hospital"
# Solution: Check inventory levels and choose different source
curl http://localhost:8000/forecasting/inventory
```

## Future Enhancements

- Real-time model retraining with actual demand data
- Weather data integration
- Disease outbreak API integration
- Geographic distance optimization for redistribution
- Mobile push notifications
- Email/SMS alert integration
- Historical accuracy tracking
- Multi-model ensemble predictions
