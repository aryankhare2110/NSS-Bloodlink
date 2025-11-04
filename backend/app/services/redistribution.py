"""
Blood Redistribution Service

This module implements intelligent blood redistribution logic based on:
- Demand forecasts
- Current inventory levels
- Hospital priorities
- Geographic proximity
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.models import (
    InventoryLevel, Hospital, DemandForecast, 
    Donor, Request, RequestStatus, UrgencyLevel
)


class BloodRedistributor:
    """Intelligent blood redistribution system"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_inventory_status(
        self, 
        blood_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Dict]:
        """
        Get current inventory status across hospitals
        
        Args:
            blood_type: Filter by blood type
            region: Filter by region
            
        Returns:
            List of inventory status dictionaries
        """
        query = self.db.query(InventoryLevel).join(Hospital)
        
        if blood_type:
            query = query.filter(InventoryLevel.blood_type == blood_type)
        
        if region:
            query = query.filter(Hospital.location.like(f"%{region}%"))
        
        inventories = query.all()
        
        result = []
        for inv in inventories:
            result.append({
                "hospital_id": inv.hospital_id,
                "hospital_name": inv.hospital.name,
                "location": inv.hospital.location,
                "blood_type": inv.blood_type,
                "current_units": inv.current_units,
                "min_required": inv.min_required,
                "max_capacity": inv.max_capacity,
                "shortage": max(0, inv.min_required - inv.current_units),
                "surplus": max(0, inv.current_units - inv.min_required * 1.5),
                "status": self._get_inventory_status_level(inv)
            })
        
        return result
    
    def _get_inventory_status_level(self, inventory: InventoryLevel) -> str:
        """Determine inventory status level"""
        if inventory.current_units < inventory.min_required * 0.5:
            return "Critical"
        elif inventory.current_units < inventory.min_required:
            return "Low"
        elif inventory.current_units > inventory.max_capacity * 0.9:
            return "Excess"
        else:
            return "Adequate"
    
    def identify_redistribution_opportunities(
        self,
        blood_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Identify opportunities for blood redistribution
        
        Matches hospitals with surplus against those with shortages
        
        Args:
            blood_type: Filter by specific blood type
            
        Returns:
            List of redistribution recommendations
        """
        inventory_status = self.get_inventory_status(blood_type=blood_type)
        
        # Separate surplus and shortage hospitals
        surplus_hospitals = [
            inv for inv in inventory_status 
            if inv['surplus'] > 0
        ]
        
        shortage_hospitals = [
            inv for inv in inventory_status 
            if inv['shortage'] > 0
        ]
        
        recommendations = []
        
        # Match surplus with shortages
        for shortage in shortage_hospitals:
            for surplus in surplus_hospitals:
                # Only match same blood type
                if shortage['blood_type'] != surplus['blood_type']:
                    continue
                
                # Calculate transfer amount
                transfer_units = min(
                    shortage['shortage'],
                    surplus['surplus']
                )
                
                if transfer_units > 0:
                    recommendations.append({
                        "from_hospital_id": surplus['hospital_id'],
                        "from_hospital_name": surplus['hospital_name'],
                        "to_hospital_id": shortage['hospital_id'],
                        "to_hospital_name": shortage['hospital_name'],
                        "blood_type": shortage['blood_type'],
                        "transfer_units": transfer_units,
                        "priority": self._calculate_priority(shortage, surplus),
                        "reason": self._generate_reason(shortage, surplus)
                    })
        
        # Sort by priority (highest first)
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations
    
    def _calculate_priority(
        self, 
        shortage: Dict, 
        surplus: Dict
    ) -> float:
        """
        Calculate priority score for redistribution
        
        Higher score = higher priority
        """
        priority = 0.0
        
        # Critical shortage gets highest priority
        if shortage['status'] == 'Critical':
            priority += 100
        elif shortage['status'] == 'Low':
            priority += 50
        
        # Larger shortage increases priority
        priority += shortage['shortage'] * 2
        
        # Larger surplus from donor hospital increases feasibility
        priority += surplus['surplus'] * 0.5
        
        return priority
    
    def _generate_reason(self, shortage: Dict, surplus: Dict) -> str:
        """Generate human-readable reason for redistribution"""
        return (
            f"{shortage['hospital_name']} has {shortage['shortage']} unit shortage "
            f"while {surplus['hospital_name']} has {int(surplus['surplus'])} unit surplus"
        )
    
    def apply_forecast_based_redistribution(
        self,
        forecasts: List[DemandForecast],
        threshold_risk: str = "High"
    ) -> List[Dict]:
        """
        Generate redistribution plan based on demand forecasts
        
        Args:
            forecasts: List of demand forecasts
            threshold_risk: Minimum risk level to trigger redistribution
            
        Returns:
            List of redistribution actions
        """
        risk_levels = ["Low", "Medium", "High", "Critical"]
        threshold_index = risk_levels.index(threshold_risk)
        
        # Filter high-risk forecasts
        high_risk_forecasts = [
            f for f in forecasts 
            if risk_levels.index(f.shortage_risk) >= threshold_index
        ]
        
        redistribution_plan = []
        
        # Group forecasts by blood type
        by_blood_type = defaultdict(list)
        for forecast in high_risk_forecasts:
            by_blood_type[forecast.blood_type].append(forecast)
        
        # For each blood type with predicted shortage
        for blood_type, type_forecasts in by_blood_type.items():
            # Get current redistribution opportunities
            opportunities = self.identify_redistribution_opportunities(
                blood_type=blood_type
            )
            
            if opportunities:
                # Add forecast context to recommendations
                for opp in opportunities:
                    opp['forecast_based'] = True
                    opp['predicted_shortage_regions'] = [
                        f.region for f in type_forecasts
                    ]
                    redistribution_plan.append(opp)
        
        return redistribution_plan
    
    def execute_redistribution(
        self,
        from_hospital_id: int,
        to_hospital_id: int,
        blood_type: str,
        units: int
    ) -> Dict:
        """
        Execute a redistribution transaction
        
        Args:
            from_hospital_id: Source hospital ID
            to_hospital_id: Destination hospital ID
            blood_type: Blood type to transfer
            units: Number of units to transfer
            
        Returns:
            Transaction result dictionary
        """
        try:
            # Get source inventory
            source_inv = self.db.query(InventoryLevel).filter(
                and_(
                    InventoryLevel.hospital_id == from_hospital_id,
                    InventoryLevel.blood_type == blood_type
                )
            ).first()
            
            if not source_inv or source_inv.current_units < units:
                return {
                    "success": False,
                    "error": "Insufficient inventory at source hospital"
                }
            
            # Get destination inventory
            dest_inv = self.db.query(InventoryLevel).filter(
                and_(
                    InventoryLevel.hospital_id == to_hospital_id,
                    InventoryLevel.blood_type == blood_type
                )
            ).first()
            
            if not dest_inv:
                # Create new inventory entry if doesn't exist
                dest_inv = InventoryLevel(
                    hospital_id=to_hospital_id,
                    blood_type=blood_type,
                    current_units=0,
                    min_required=10,
                    max_capacity=100
                )
                self.db.add(dest_inv)
            
            # Check capacity
            if dest_inv.current_units + units > dest_inv.max_capacity:
                return {
                    "success": False,
                    "error": "Destination hospital at capacity"
                }
            
            # Execute transfer
            source_inv.current_units -= units
            dest_inv.current_units += units
            
            self.db.commit()
            
            return {
                "success": True,
                "from_hospital_id": from_hospital_id,
                "to_hospital_id": to_hospital_id,
                "blood_type": blood_type,
                "units_transferred": units,
                "source_remaining": source_inv.current_units,
                "dest_new_level": dest_inv.current_units
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_redistribution_summary(self) -> Dict:
        """
        Get overall redistribution summary statistics
        
        Returns:
            Summary dictionary with key metrics
        """
        all_inventory = self.get_inventory_status()
        
        total_hospitals = len(set(inv['hospital_id'] for inv in all_inventory))
        
        critical = [inv for inv in all_inventory if inv['status'] == 'Critical']
        low = [inv for inv in all_inventory if inv['status'] == 'Low']
        adequate = [inv for inv in all_inventory if inv['status'] == 'Adequate']
        excess = [inv for inv in all_inventory if inv['status'] == 'Excess']
        
        total_shortage_units = sum(inv['shortage'] for inv in all_inventory)
        total_surplus_units = sum(inv['surplus'] for inv in all_inventory)
        
        return {
            "total_hospitals": total_hospitals,
            "total_inventory_records": len(all_inventory),
            "critical_count": len(critical),
            "low_count": len(low),
            "adequate_count": len(adequate),
            "excess_count": len(excess),
            "total_shortage_units": total_shortage_units,
            "total_surplus_units": total_surplus_units,
            "redistribution_potential": min(total_shortage_units, total_surplus_units),
            "blood_types_tracked": len(set(inv['blood_type'] for inv in all_inventory))
        }
