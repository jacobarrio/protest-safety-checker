#!/usr/bin/env python3
import pandas as pd
from datetime import datetime

def load_data():
    """Load ICE incidents data"""
    return pd.read_csv('protest_data_oversight.csv')

def calculate_city_risk(city_name, df):
    """
    Calculate risk score for a city based on ICE incident data
    
    Returns: dict with risk_level, score, stats, recent_incidents
    """
    
    # Normalize city name for matching
    city_lower = city_name.lower()
    
    # Filter incidents for this city (fuzzy match on location)
    city_incidents = df[df['location'].str.lower().str.contains(city_lower, na=False)]
    
    if len(city_incidents) == 0:
        return {
            'risk_level': 'Unknown',
            'score': 0,
            'total_incidents': 0,
            'message': f'No incidents found for "{city_name}"'
        }
    
    total_incidents = len(city_incidents)
    
    # Count incident types
    force_incidents = city_incidents[
        city_incidents['category'].str.contains('Use of Force', na=False, case=False)
    ]
    
    arrest_incidents = city_incidents[
        city_incidents['category'].str.contains('Arrest|Detention', na=False, case=False)
    ]
    
    citizen_incidents = city_incidents[
        city_incidents['category'].str.contains('U.S. Citizen', na=False, case=False)
    ]
    
    sensitive_location = city_incidents[
        city_incidents['category'].str.contains('Sensitive Location', na=False, case=False)
    ]
    
    # Calculate percentages
    force_pct = (len(force_incidents) / total_incidents) * 100 if total_incidents > 0 else 0
    citizen_pct = (len(citizen_incidents) / total_incidents) * 100 if total_incidents > 0 else 0
    sensitive_pct = (len(sensitive_location) / total_incidents) * 100 if total_incidents > 0 else 0
    
    # Risk scoring
    risk_score = 0
    
    # Base score: number of incidents
    if total_incidents >= 20:
        risk_score += 40
    elif total_incidents >= 10:
        risk_score += 30
    elif total_incidents >= 5:
        risk_score += 20
    else:
        risk_score += 10
    
    # Force incidents increase risk significantly
    if force_pct >= 50:
        risk_score += 30
    elif force_pct >= 30:
        risk_score += 20
    elif force_pct >= 10:
        risk_score += 10
    
    # US citizen targeting is alarming
    if citizen_pct >= 30:
        risk_score += 20
    elif citizen_pct >= 15:
        risk_score += 10
    
    # Sensitive locations (schools, hospitals, etc.)
    if sensitive_pct >= 20:
        risk_score += 10
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = 'High'
    elif risk_score >= 40:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'
    
    # Get recent incidents (top 5)
    recent = city_incidents.head(5)[['date', 'category', 'title']].to_dict('records')
    
    return {
        'risk_level': risk_level,
        'score': risk_score,
        'total_incidents': total_incidents,
        'force_incidents': len(force_incidents),
        'force_pct': round(force_pct, 1),
        'citizen_incidents': len(citizen_incidents),
        'citizen_pct': round(citizen_pct, 1),
        'sensitive_location': len(sensitive_location),
        'sensitive_pct': round(sensitive_pct, 1),
        'recent_incidents': recent
    }

if __name__ == "__main__":
    # Test the calculator
    df = load_data()
    
    test_cities = ['Portland', 'Chicago', 'Minneapolis', 'Phoenix']
    
    for city in test_cities:
        print(f"\n{'='*60}")
        print(f"RISK ASSESSMENT: {city}")
        print('='*60)
        
        result = calculate_city_risk(city, df)
        
        print(f"Risk Level: {result['risk_level']}")
        print(f"Risk Score: {result['score']}/100")
        print(f"\nIncident Stats:")
        print(f"  Total incidents: {result['total_incidents']}")
        print(f"  Use of Force: {result.get('force_incidents', 0)} ({result.get('force_pct', 0)}%)")
        print(f"  U.S. Citizens: {result.get('citizen_incidents', 0)} ({result.get('citizen_pct', 0)}%)")
        print(f"  Sensitive Locations: {result.get('sensitive_location', 0)} ({result.get('sensitive_pct', 0)}%)")
        
        if 'recent_incidents' in result:
            print(f"\nRecent Incidents:")
            for inc in result['recent_incidents'][:3]:
                print(f"  - {inc['date']}: {inc['title'][:60]}...")
