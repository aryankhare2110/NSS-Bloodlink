#!/usr/bin/env python3
"""
Blood Demand Forecasting Demo Script

This script demonstrates the complete workflow of the forecasting system:
1. Train the ML model
2. Generate forecasts
3. Identify high-risk situations
4. Send alerts to volunteers
5. Plan and execute redistribution

Usage:
    python forecasting_demo.py
"""

import requests
import json
from typing import Dict, List
import time

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_json(data: Dict):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))


def train_model():
    """Train the forecasting model"""
    print_section("Step 1: Training ML Model")
    
    response = requests.post(f"{BASE_URL}/forecasting/train")
    result = response.json()
    
    print_json(result)
    
    if result.get("success"):
        print("\n✅ Model trained successfully!")
    else:
        print("\n❌ Model training failed")
        exit(1)
    
    return result


def generate_forecasts():
    """Generate demand forecasts"""
    print_section("Step 2: Generating Demand Forecasts")
    
    payload = {
        "hours_ahead": 48,
        "regions": ["South Delhi", "Noida"],
        "retrain": False
    }
    
    print(f"\nRequest: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/forecasting/generate",
        json=payload
    )
    forecasts = response.json()
    
    print(f"\n✅ Generated {len(forecasts)} forecasts")
    
    # Show summary
    print("\nForecast Summary:")
    risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for forecast in forecasts:
        risk_counts[forecast["shortage_risk"]] += 1
    
    for risk, count in risk_counts.items():
        if count > 0:
            print(f"  {risk}: {count} forecasts")
    
    # Show high-risk forecasts
    high_risk = [f for f in forecasts if f["shortage_risk"] in ["Critical", "High"]]
    if high_risk:
        print(f"\n⚠️  {len(high_risk)} HIGH-RISK FORECASTS:")
        for f in high_risk[:5]:  # Show first 5
            print(f"  - {f['blood_type']} in {f['region']}: "
                  f"{f['shortage_risk']} risk "
                  f"(demand: {f['predicted_demand']:.1f} units)")
    
    return forecasts


def get_forecast_summary():
    """Get forecast summary statistics"""
    print_section("Step 3: Analyzing Forecast Summary")
    
    response = requests.get(f"{BASE_URL}/forecasting/forecasts/summary")
    summary = response.json()
    
    print_json(summary)
    
    total = summary["total_forecasts"]
    critical = summary["critical_risk_count"]
    high = summary["high_risk_count"]
    
    print(f"\n📊 {critical + high}/{total} forecasts indicate potential shortage")
    
    return summary


def send_alerts():
    """Send alerts to volunteers"""
    print_section("Step 4: Sending Alerts to Volunteers")
    
    payload = {
        "min_risk_level": "High"
    }
    
    response = requests.post(
        f"{BASE_URL}/forecasting/alerts/send",
        json=payload
    )
    result = response.json()
    
    alerts = result.get("alerts_sent", [])
    
    print(f"\n✅ Sent {len(alerts)} alerts")
    
    if alerts:
        print("\nAlert Examples:")
        for alert in alerts[:3]:  # Show first 3
            print(f"\n  Blood Type: {alert['blood_type']}")
            print(f"  Region: {alert['region']}")
            print(f"  Risk: {alert['shortage_risk']}")
            print(f"  Message: {alert['message']}")
            print(f"  Donors Notified: {alert['notified_donors']}")
    
    return result


def check_inventory():
    """Check current inventory levels"""
    print_section("Step 5: Checking Inventory Levels")
    
    response = requests.get(f"{BASE_URL}/forecasting/inventory")
    inventory = response.json()
    
    print(f"\n✅ Retrieved {len(inventory)} inventory records")
    
    # Analyze inventory status
    critical = []
    low = []
    
    for inv in inventory:
        shortage = max(0, inv["min_required"] - inv["current_units"])
        if shortage > 0:
            status = "Critical" if inv["current_units"] < inv["min_required"] * 0.5 else "Low"
            item = {
                "hospital": inv["hospital"]["name"],
                "blood_type": inv["blood_type"],
                "current": inv["current_units"],
                "needed": inv["min_required"],
                "shortage": shortage
            }
            if status == "Critical":
                critical.append(item)
            else:
                low.append(item)
    
    if critical:
        print(f"\n🚨 {len(critical)} CRITICAL SHORTAGES:")
        for item in critical[:5]:
            print(f"  - {item['hospital']}: {item['blood_type']} "
                  f"({item['current']}/{item['needed']} units, "
                  f"shortage: {item['shortage']})")
    
    if low:
        print(f"\n⚠️  {len(low)} LOW INVENTORY:")
        for item in low[:5]:
            print(f"  - {item['hospital']}: {item['blood_type']} "
                  f"({item['current']}/{item['needed']} units)")
    
    return inventory


def find_redistribution_opportunities():
    """Find redistribution opportunities"""
    print_section("Step 6: Finding Redistribution Opportunities")
    
    response = requests.get(f"{BASE_URL}/forecasting/redistribution/opportunities")
    result = response.json()
    
    opportunities = result.get("opportunities", [])
    
    print(f"\n✅ Found {len(opportunities)} redistribution opportunities")
    
    if opportunities:
        print("\nTop Opportunities:")
        for opp in opportunities[:5]:
            print(f"\n  Priority: {opp['priority']:.1f}")
            print(f"  Transfer: {opp['transfer_units']} units of {opp['blood_type']}")
            print(f"  From: {opp['from_hospital_name']}")
            print(f"  To: {opp['to_hospital_name']}")
            print(f"  Reason: {opp['reason']}")
    
    return opportunities


def get_forecast_based_plan():
    """Get forecast-based redistribution plan"""
    print_section("Step 7: Creating Forecast-Based Redistribution Plan")
    
    response = requests.post(
        f"{BASE_URL}/forecasting/redistribution/forecast-based",
        params={"threshold_risk": "High"}
    )
    result = response.json()
    
    plan = result.get("plan", [])
    
    print(f"\n✅ Generated plan with {len(plan)} actions")
    
    if plan:
        print("\nRecommended Actions:")
        for action in plan[:5]:
            print(f"\n  Priority: {action['priority']:.1f}")
            print(f"  Transfer: {action['transfer_units']} units of {action['blood_type']}")
            print(f"  From: {action['from_hospital_name']}")
            print(f"  To: {action['to_hospital_name']}")
            print(f"  Predicted shortage regions: {', '.join(action['predicted_shortage_regions'])}")
    
    return plan


def get_redistribution_summary():
    """Get overall redistribution summary"""
    print_section("Step 8: Overall System Summary")
    
    response = requests.get(f"{BASE_URL}/forecasting/redistribution/summary")
    summary = response.json()
    
    print_json(summary)
    
    print(f"\n📊 System Status:")
    print(f"  Total hospitals: {summary['total_hospitals']}")
    print(f"  Critical shortages: {summary['critical_count']}")
    print(f"  Low inventory: {summary['low_count']}")
    print(f"  Total shortage: {summary['total_shortage_units']} units")
    print(f"  Total surplus: {summary['total_surplus_units']:.0f} units")
    print(f"  Redistribution potential: {summary['redistribution_potential']} units")
    
    return summary


def main():
    """Main demo workflow"""
    print("\n" + "=" * 70)
    print("  Blood Demand Forecasting System - Complete Demo")
    print("=" * 70)
    print("\nThis demo will walk through the complete forecasting workflow.")
    print("Make sure the FastAPI server is running at http://localhost:8000")
    
    input("\nPress Enter to start...")
    
    try:
        # Step 1: Train model
        train_model()
        time.sleep(1)
        
        # Step 2: Generate forecasts
        forecasts = generate_forecasts()
        time.sleep(1)
        
        # Step 3: Get summary
        get_forecast_summary()
        time.sleep(1)
        
        # Step 4: Send alerts
        send_alerts()
        time.sleep(1)
        
        # Step 5: Check inventory
        check_inventory()
        time.sleep(1)
        
        # Step 6: Find opportunities
        find_redistribution_opportunities()
        time.sleep(1)
        
        # Step 7: Get forecast-based plan
        plan = get_forecast_based_plan()
        time.sleep(1)
        
        # Step 8: Get overall summary
        get_redistribution_summary()
        
        print("\n" + "=" * 70)
        print("  Demo completed successfully! ✅")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. View the API documentation at http://localhost:8000/docs")
        print("  2. Read the forecasting guide at docs/forecasting_guide.md")
        print("  3. Integrate with your frontend application")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Make sure the server is running: uvicorn app.main:app")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
