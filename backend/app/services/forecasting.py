"""
Blood Demand Forecasting Service using Machine Learning

This module implements ML-based demand forecasting for blood donations,
including seasonal pattern detection, shortage prediction, and alert generation.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
import os

from app.models.models import DemandHistory, DemandForecast, InventoryLevel, Hospital


class BloodDemandForecaster:
    """ML-based blood demand forecasting system"""
    
    def __init__(self):
        self.model = None
        self.blood_type_encoder = LabelEncoder()
        self.region_encoder = LabelEncoder()
        self.season_encoder = LabelEncoder()
        self.model_path = "/tmp/blood_demand_model.pkl"
        self.is_trained = False
        
    def determine_season(self, date: datetime) -> str:
        """
        Determine season based on date (Indian climate context)
        
        Args:
            date: Date to determine season for
            
        Returns:
            Season name: Winter, Summer, Monsoon, Post-Monsoon
        """
        month = date.month
        
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Summer"
        elif month in [6, 7, 8, 9]:
            return "Monsoon"
        else:  # 10, 11
            return "Post-Monsoon"
    
    def generate_training_data(self, db: Session, days_back: int = 365) -> pd.DataFrame:
        """
        Generate synthetic training data based on real patterns for demonstration
        
        In production, this would use actual historical data from demand_history table.
        For now, we generate realistic patterns including:
        - Seasonal variations (monsoon spikes for malaria/dengue)
        - Blood type distribution
        - Regional patterns
        
        Args:
            db: Database session
            days_back: Number of days of historical data to generate
            
        Returns:
            DataFrame with training data
        """
        # Blood types with realistic distribution
        blood_types = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
        blood_type_weights = [0.35, 0.30, 0.20, 0.05, 0.05, 0.03, 0.015, 0.005]  # Realistic distribution
        
        # Regions
        regions = ["South Delhi", "North Delhi", "East Delhi", "West Delhi", 
                   "Central Delhi", "Noida", "Gurgaon", "Dwarka"]
        
        data = []
        start_date = datetime.now() - timedelta(days=days_back)
        
        for day in range(days_back):
            current_date = start_date + timedelta(days=day)
            season = self.determine_season(current_date)
            
            # Base demand varies by season
            # Post-Monsoon (Oct-Nov) sees spike due to dengue/malaria aftermath
            season_multiplier = {
                "Winter": 1.0,
                "Summer": 0.9,
                "Monsoon": 1.3,  # Rainy season increase
                "Post-Monsoon": 1.8  # Highest spike after monsoon (diseases)
            }
            
            for region in regions:
                # Regional population factor
                region_factor = np.random.uniform(0.8, 1.2)
                
                for blood_type, weight in zip(blood_types, blood_type_weights):
                    # Base demand for blood type
                    base_demand = weight * 100
                    
                    # Apply seasonal multiplier
                    seasonal_demand = base_demand * season_multiplier[season]
                    
                    # Apply regional factor
                    demand = seasonal_demand * region_factor
                    
                    # Add random variation (±20%)
                    demand = demand * np.random.uniform(0.8, 1.2)
                    
                    # Disease outbreak simulation (10% chance during/after monsoon)
                    disease_outbreak = False
                    if season in ["Monsoon", "Post-Monsoon"]:
                        if np.random.random() < 0.1:
                            disease_outbreak = True
                            demand *= 1.5  # 50% spike during outbreak
                    
                    # Weekend effect (slightly lower demand)
                    if current_date.weekday() >= 5:
                        demand *= 0.9
                    
                    data.append({
                        "blood_type": blood_type,
                        "region": region,
                        "demand_units": int(demand),
                        "date": current_date,
                        "season": season,
                        "disease_outbreak": disease_outbreak,
                        "day_of_week": current_date.weekday(),
                        "month": current_date.month,
                        "is_monsoon": 1 if season in ["Monsoon", "Post-Monsoon"] else 0
                    })
        
        return pd.DataFrame(data)
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features for ML model
        
        Args:
            df: Input DataFrame with demand data
            
        Returns:
            Tuple of (X_features, y_target)
        """
        # Encode categorical variables
        df['blood_type_encoded'] = self.blood_type_encoder.fit_transform(df['blood_type'])
        df['region_encoded'] = self.region_encoder.fit_transform(df['region'])
        df['season_encoded'] = self.season_encoder.fit_transform(df['season'])
        
        # Feature engineering
        features = [
            'blood_type_encoded',
            'region_encoded',
            'season_encoded',
            'day_of_week',
            'month',
            'disease_outbreak',
            'is_monsoon'
        ]
        
        X = df[features].values
        y = df['demand_units'].values
        
        return X, y
    
    def train_model(self, db: Session, force_retrain: bool = False):
        """
        Train the demand forecasting model
        
        Args:
            db: Database session
            force_retrain: Whether to force retraining even if model exists
        """
        # Check if model already exists and is trained
        if os.path.exists(self.model_path) and not force_retrain:
            try:
                self.load_model()
                print("✅ Loaded existing demand forecasting model")
                return
            except:
                print("⚠️  Could not load existing model, retraining...")
        
        print("🤖 Training demand forecasting model...")
        
        # Generate training data
        df = self.generate_training_data(db, days_back=365)
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        # Train Random Forest model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X, y)
        self.is_trained = True
        
        # Save model
        self.save_model()
        
        print(f"✅ Model trained on {len(df)} historical records")
        print(f"   Training score: {self.model.score(X, y):.3f}")
    
    def save_model(self):
        """Save trained model to disk"""
        model_data = {
            'model': self.model,
            'blood_type_encoder': self.blood_type_encoder,
            'region_encoder': self.region_encoder,
            'season_encoder': self.season_encoder,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, self.model_path)
        print(f"💾 Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from disk"""
        model_data = joblib.load(self.model_path)
        self.model = model_data['model']
        self.blood_type_encoder = model_data['blood_type_encoder']
        self.region_encoder = model_data['region_encoder']
        self.season_encoder = model_data['season_encoder']
        self.is_trained = model_data['is_trained']
    
    def predict_demand(
        self, 
        blood_type: str, 
        region: str, 
        forecast_date: datetime
    ) -> Tuple[float, float]:
        """
        Predict blood demand for specific parameters
        
        Args:
            blood_type: Blood type to predict (e.g., "O+")
            region: Geographic region
            forecast_date: Date to predict for
            
        Returns:
            Tuple of (predicted_demand, confidence_score)
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features for prediction
        season = self.determine_season(forecast_date)
        
        # Check if blood type and region are in encoders
        try:
            blood_type_encoded = self.blood_type_encoder.transform([blood_type])[0]
        except:
            blood_type_encoded = 0  # Default to first category
            
        try:
            region_encoded = self.region_encoder.transform([region])[0]
        except:
            region_encoded = 0  # Default to first category
            
        try:
            season_encoded = self.season_encoder.transform([season])[0]
        except:
            season_encoded = 0  # Default to first category
        
        # Disease outbreak probability (higher during/after monsoon)
        disease_outbreak = 1 if season in ["Monsoon", "Post-Monsoon"] and np.random.random() < 0.1 else 0
        is_monsoon = 1 if season in ["Monsoon", "Post-Monsoon"] else 0
        
        features = np.array([[
            blood_type_encoded,
            region_encoded,
            season_encoded,
            forecast_date.weekday(),
            forecast_date.month,
            disease_outbreak,
            is_monsoon
        ]])
        
        # Make prediction
        prediction = self.model.predict(features)[0]
        
        # Estimate confidence (simplified - using tree variance)
        # In production, use proper uncertainty quantification
        predictions_per_tree = np.array([tree.predict(features)[0] for tree in self.model.estimators_])
        std_dev = np.std(predictions_per_tree)
        
        # Confidence: higher when predictions are consistent across trees
        confidence = max(0.5, min(0.95, 1.0 - (std_dev / prediction) if prediction > 0 else 0.7))
        
        return prediction, confidence
    
    def assess_shortage_risk(
        self, 
        predicted_demand: float, 
        current_inventory: int
    ) -> str:
        """
        Assess shortage risk based on predicted demand vs current inventory
        
        Args:
            predicted_demand: Predicted demand in units
            current_inventory: Current inventory level
            
        Returns:
            Risk level: "Low", "Medium", "High", "Critical"
        """
        if current_inventory <= 0:
            return "Critical"
        
        # Calculate coverage ratio (days of supply)
        coverage_ratio = current_inventory / predicted_demand if predicted_demand > 0 else 10
        
        if coverage_ratio >= 3.0:
            return "Low"
        elif coverage_ratio >= 2.0:
            return "Medium"
        elif coverage_ratio >= 1.0:
            return "High"
        else:
            return "Critical"
    
    def generate_forecasts(
        self, 
        db: Session, 
        hours_ahead: int = 48,
        regions: Optional[List[str]] = None
    ) -> List[DemandForecast]:
        """
        Generate demand forecasts for next hours_ahead hours
        
        Args:
            db: Database session
            hours_ahead: Hours to forecast ahead (default 24-48)
            regions: List of regions to forecast for (None = all)
            
        Returns:
            List of DemandForecast objects
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before generating forecasts")
        
        if regions is None:
            regions = ["South Delhi", "North Delhi", "East Delhi", "West Delhi", 
                      "Central Delhi", "Noida", "Gurgaon", "Dwarka"]
        
        blood_types = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
        
        forecast_date = datetime.now() + timedelta(hours=hours_ahead)
        forecasts = []
        
        for region in regions:
            for blood_type in blood_types:
                # Get current inventory for this region/blood type
                # For demo, we'll use a default value
                current_inventory = 50  # In production, query from InventoryLevel table
                
                try:
                    # Make prediction
                    predicted_demand, confidence = self.predict_demand(
                        blood_type, region, forecast_date
                    )
                    
                    # Assess shortage risk
                    shortage_risk = self.assess_shortage_risk(
                        predicted_demand, current_inventory
                    )
                    
                    # Create forecast object
                    forecast = DemandForecast(
                        blood_type=blood_type,
                        region=region,
                        forecast_date=forecast_date,
                        predicted_demand=predicted_demand,
                        confidence=confidence,
                        shortage_risk=shortage_risk,
                        alert_sent=False
                    )
                    
                    forecasts.append(forecast)
                    
                except Exception as e:
                    print(f"⚠️  Error generating forecast for {blood_type} in {region}: {e}")
                    continue
        
        return forecasts


# Global forecaster instance
_forecaster = None

def get_forecaster() -> BloodDemandForecaster:
    """Get or create global forecaster instance"""
    global _forecaster
    if _forecaster is None:
        _forecaster = BloodDemandForecaster()
    return _forecaster
