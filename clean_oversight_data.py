#!/usr/bin/env python3
"""
Clean protest_data_oversight.csv - fix misaligned rows
"""
import pandas as pd
import re
from datetime import datetime

def parse_date(date_str):
    """Convert MM/DD/YYYY to YYYY-MM-DD, handle 'Unknown'"""
    if date_str == 'Unknown' or pd.isna(date_str):
        return 'Unknown'
    
    try:
        # Try MM/DD/YYYY format
        date_obj = datetime.strptime(str(date_str).strip(), "%m/%d/%Y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        return 'Unknown'

def parse_location(loc_str):
    """Extract city and state from location string"""
    if pd.isna(loc_str) or loc_str == 'Unknown':
        return 'Unknown', 'XX'
    
    # Handle "City, ST" format
    parts = str(loc_str).split(',')
    if len(parts) >= 2:
        city = parts[0].strip()
        state = parts[1].strip()[:2]
        return city, state
    else:
        return loc_str.strip(), 'XX'

def map_category_to_type(category):
    """Map oversight category to incident type"""
    cat_lower = str(category).lower()
    
    if 'use of force' in cat_lower:
        return 'POLICE_VIOLENCE'
    elif 'citizen' in cat_lower:
        return 'CONSTITUTIONAL_VIOLATION'
    elif 'arrest' in cat_lower or 'detention' in cat_lower or 'deportation' in cat_lower:
        return 'ICE_OPERATION'
    elif 'sensitive location' in cat_lower:
        return 'ICE_OPERATION'
    else:
        return 'ICE_OPERATION'

def calculate_severity(category, title):
    """Calculate severity 1-10 based on incident details"""
    severity = 5
    
    text = f"{category} {title}".lower()
    
    # Violence indicators
    violence_words = ['force', 'shot', 'killed', 'assault', 'injured', 'tear gas', 'pepper spray']
    for word in violence_words:
        if word in text:
            severity += 2
            break
    
    # Vulnerable populations
    if any(word in text for word in ['child', 'minor', 'family', 'cancer', 'dying', 'hospital']):
        severity += 1
    
    # Constitutional violations
    if 'citizen' in text or 'unlawful' in text or 'illegal' in text:
        severity += 1
    
    return min(severity, 10)

def clean_data():
    print("🧹 Cleaning protest_data_oversight.csv...")
    
    # Read raw CSV
    df = pd.read_csv('protest_data_oversight.csv')
    print(f"  Loaded {len(df)} rows")
    
    cleaned_incidents = []
    misaligned_count = 0
    
    for idx, row in df.iterrows():
        # Detect misaligned rows: date column contains category text
        date_val = str(row['date']).strip()
        
        if 'Concerning' in date_val or 'Enforcement Action' in date_val or 'U.S. Citizen' in date_val:
            # Misaligned row: category, Unknown, location, title, url
            misaligned_count += 1
            
            category = date_val  # Actually category
            date = 'Unknown'
            location = row['category']  # Actually location
            title = row['title']
            source_url = row['source_url'] if 'source_url' in row else ''
            
        else:
            # Normal row
            date = date_val
            location = row['location']
            category = row['category']
            title = row['title']
            source_url = row['source_url'] if 'source_url' in row else ''
        
        # Parse and normalize
        date_clean = parse_date(date)
        city, state = parse_location(location)
        incident_type = map_category_to_type(category)
        severity = calculate_severity(category, title)
        
        # Truncate long descriptions
        description = title[:150] if len(title) > 150 else title
        
        cleaned_incidents.append({
            'city': city,
            'state': state,
            'date': date_clean,
            'type': incident_type,
            'description': description,
            'source': source_url,
            'severity': severity
        })
    
    print(f"  Fixed {misaligned_count} misaligned rows")
    
    # Create clean DataFrame
    df_clean = pd.DataFrame(cleaned_incidents)
    
    # Remove duplicates
    before = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['city', 'date', 'description'])
    after = len(df_clean)
    print(f"  Removed {before - after} duplicates")
    
    # Sort by date (most recent first)
    df_clean = df_clean.sort_values('date', ascending=False)
    
    # Save cleaned data
    df_clean.to_csv('protest_data_clean.csv', index=False)
    print(f"✅ Saved {len(df_clean)} clean incidents to protest_data_clean.csv")
    
    # Stats
    print(f"\n📊 Stats:")
    print(f"  Cities: {df_clean['city'].nunique()}")
    print(f"  States: {df_clean['state'].nunique()}")
    print(f"  Date range: {df_clean['date'].min()} to {df_clean['date'].max()}")
    print(f"  Avg severity: {df_clean['severity'].mean():.1f}/10")
    print(f"\n  Top cities:")
    print(df_clean['city'].value_counts().head(10))
    
    return df_clean

if __name__ == "__main__":
    clean_data()
