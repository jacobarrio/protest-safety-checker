# seed_data.py - Manual incidents you know about
import pandas as pd
from datetime import datetime

incidents = [
    # PORTLAND
    {
        'city': 'Portland',
        'state': 'OR',
        'date': '2026-01-15',
        'type': 'POLICE_VIOLENCE',
        'description': 'Border Patrol shot two protesters at demonstration',
        'source': 'https://example.com',
        'severity': 10
    },
    
    # MINNEAPOLIS - Violence
    {
        'city': 'Minneapolis',
        'state': 'MN', 
        'date': '2026-01-23',
        'type': 'POLICE_VIOLENCE',
        'description': 'General strike - tear gas, pepper spray, flashbangs on protesters',
        'source': 'https://example.com',
        'severity': 9
    },
    
    # MINNEAPOLIS - ICE Operations
    {
        'city': 'Minneapolis',
        'state': 'MN',
        'date': '2026-01-23',
        'type': 'ICE_OPERATION',
        'description': '6-year-old left wandering streets after father detained at laundromat',
        'source': 'https://example.com',
        'severity': 8
    },
    {
        'city': 'Minneapolis',
        'state': 'MN',
        'date': '2026-01-20',
        'type': 'ICE_OPERATION',
        'description': 'Father detained while son dying from Pompe disease, child died Jan 23',
        'source': 'https://example.com',
        'severity': 10
    },
    
    # MINNEAPOLIS - Constitutional Violations
    {
        'city': 'Minneapolis',
        'state': 'MN',
        'date': '2026-01-01',
        'type': 'CONSTITUTIONAL_VIOLATION',
        'description': '96+ court order violations by ICE since Jan 1',
        'source': 'https://example.com',
        'severity': 10
    },
    {
        'city': 'Minneapolis',
        'state': 'MN',
        'date': '2026-01-15',
        'type': 'CONSTITUTIONAL_VIOLATION',
        'description': 'US citizens and legal residents repeatedly detained (4th Amendment)',
        'source': 'https://example.com',
        'severity': 9
    },
    {
        'city': 'Minneapolis',
        'state': 'MN',
        'date': '2026-01-10',
        'type': 'CONSTITUTIONAL_VIOLATION',
        'description': 'Asylum seekers detained in violation of due process (5th Amendment)',
        'source': 'https://example.com',
        'severity': 8
    },
    
    # JOURNALIST ARRESTS
    {
        'city': 'New York',
        'state': 'NY',
        'date': '2026-01-22',
        'type': 'PRESS_FREEDOM',
        'description': 'Don Lemon arrested while covering protests (1st Amendment)',
        'source': 'https://example.com',
        'severity': 9
    },
    {
        'city': 'Atlanta',
        'state': 'GA',
        'date': '2026-01-20',
        'type': 'PRESS_FREEDOM',
        'description': 'Georgia Fort (independent journalist) arrested at protest',
        'source': 'https://example.com',
        'severity': 8
    },
    
    # MASS DETENTION SURGE
    {
        'city': 'National',
        'state': 'USA',
        'date': '2026-01-15',
        'type': 'ICE_OPERATION',
        'description': '2,450% surge in arrests of people with NO criminal record',
        'source': 'https://example.com',
        'severity': 10
    },
    {
        'city': 'National',
        'state': 'USA',
        'date': '2026-01-10',
        'type': 'ICE_OPERATION',
        'description': 'Detention up 75%: 40k → 66k (highest ever)',
        'source': 'https://example.com',
        'severity': 9
    },
    
    # Add more cities as you remember incidents
]

df = pd.DataFrame(incidents)
df.to_csv('protest_data.csv', index=False)
print(f"✅ Created seed data with {len(df)} incidents")
print("\n📊 Breakdown by type:")
print(df['type'].value_counts())
print("\n📍 Cities covered:")
print(df['city'].value_counts())
