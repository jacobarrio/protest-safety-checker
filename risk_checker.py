# risk_checker.py - V0.1 protest safety checker
import pandas as pd
from datetime import datetime, timedelta

def calculate_risk(city):
    """Calculate risk score for a city based on recent incidents"""
    
    # Load data
    try:
        df = pd.read_csv('protest_data.csv')
    except FileNotFoundError:
        print("❌ No data found. Run seed_data.py first.")
        return
    
    # Filter by city (case-insensitive)
    city_data = df[df['city'].str.lower() == city.lower()].copy()
    
    if len(city_data) == 0:
        print(f"⚠️  No incidents found for {city}")
        print(f"\n🚨 RISK LEVEL: UNKNOWN (no data)")
        return
    
    # Convert dates
    city_data['date'] = pd.to_datetime(city_data['date'])
    
    # Recent incidents (last 30 days)
    cutoff_30 = datetime.now() - timedelta(days=30)
    recent = city_data[city_data['date'] >= cutoff_30]
    
    # Risk scoring
    recent_count = len(recent)
    total_count = len(city_data)
    avg_severity = city_data['severity'].mean()
    
    # Weighted score
    score = (recent_count * 3) + (total_count * 1) + (avg_severity * 2)
    
    # Risk levels
    if score >= 30:
        risk = "🔴 HIGH"
    elif score >= 15:
        risk = "🟡 MEDIUM"
    else:
        risk = "🟢 LOW"
    
    # Output
    print(f"\n{'='*50}")
    print(f"PROTEST SAFETY ASSESSMENT: {city.upper()}")
    print(f"{'='*50}")
    print(f"\n🚨 RISK LEVEL: {risk}")
    print(f"📊 Risk Score: {score:.1f}")
    print(f"\n📈 Statistics:")
    print(f"  • Last 30 days: {recent_count} incidents")
    print(f"  • Last 6 months: {total_count} incidents")
    print(f"  • Avg severity: {avg_severity:.1f}/10")
    
    print(f"\n📋 Recent Incidents:")
    recent_sorted = city_data.sort_values('date', ascending=False).head(5)
    for _, row in recent_sorted.iterrows():
        print(f"  • {row['date'].strftime('%Y-%m-%d')} | {row['type']}")
        print(f"    {row['description'][:80]}")
    
    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    city = input("Enter city name: ")
    calculate_risk(city)
