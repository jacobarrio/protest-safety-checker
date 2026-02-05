#!/usr/bin/env python3
import sys
from calculator import load_data, calculate_city_risk

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 protest_checker.py <city_name>")
        print("\nExample: python3 protest_checker.py Portland")
        sys.exit(1)
    
    city = ' '.join(sys.argv[1:])
    
    print(f"\n{'='*70}")
    print(f"PROTEST SAFETY CHECKER - ICE Activity Risk Assessment")
    print(f"Data: House Oversight Democrats Immigration Dashboard (Nov 2025-Jan 2026)")
    print('='*70)
    
    df = load_data()
    result = calculate_city_risk(city, df)
    
    if result['total_incidents'] == 0:
        print(f"\n❌ {result['message']}")
        print(f"\nTry: Chicago, Minneapolis, Portland, Los Angeles, Washington DC")
        sys.exit(0)
    
    # Risk level with emoji
    emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢', 'Unknown': '⚪'}
    
    print(f"\n{emoji[result['risk_level']]} RISK LEVEL: {result['risk_level']}")
    print(f"   Risk Score: {result['score']}/100")
    
    print(f"\n📊 INCIDENT STATISTICS:")
    print(f"   Total incidents: {result['total_incidents']}")
    print(f"   Use of Force: {result['force_incidents']} ({result['force_pct']}%)")
    print(f"   U.S. Citizens targeted: {result['citizen_incidents']} ({result['citizen_pct']}%)")
    print(f"   Sensitive Locations: {result['sensitive_location']} ({result['sensitive_pct']}%)")
    
    print(f"\n📰 RECENT INCIDENTS:")
    for i, inc in enumerate(result['recent_incidents'][:5], 1):
        print(f"   {i}. [{inc['date']}] {inc['title'][:65]}...")
    
    print(f"\n💡 SAFETY RECOMMENDATIONS:")
    if result['risk_level'] == 'High':
        print("   ⚠️  High risk of ICE encounters")
        print("   • Know your rights - you can remain silent")
        print("   • Don't open doors without warrant")
        print("   • Document any encounters (video/photos)")
        print("   • Have emergency contacts ready")
    elif result['risk_level'] == 'Medium':
        print("   ⚠️  Moderate risk - stay alert")
        print("   • Be aware of your surroundings")
        print("   • Know your rights")
        print("   • Have emergency plan in place")
    else:
        print("   ✓ Lower risk, but stay informed")
        print("   • Keep monitoring local reports")
        print("   • Know your rights just in case")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
