import pandas as pd
import re
from datetime import datetime
import os

def normalize_city_input(city_input):
    """
    Normalize user input: strip, lowercase, remove extra spaces/punctuation
    'Portland, OR' -> 'portland or'
    'Phoenix  ' -> 'phoenix'
    """
    city_input = city_input.strip().lower()
    # Remove commas, extra spaces
    city_input = re.sub(r'[,\s]+', ' ', city_input).strip()
    return city_input

def find_matching_cities(user_input, df):
    """
    Find all cities that match user input (handles variations)
    Returns DataFrame of matching incidents
    """
    normalized_input = normalize_city_input(user_input)
    
    # Normalize CSV city names for comparison (column is 'location' not 'City')
    df['location_normalized'] = df['location'].str.strip().str.lower().apply(
        lambda x: re.sub(r'[,\s]+', ' ', x).strip()
    )
    
    # Try exact match first
    exact_match = df[df['location_normalized'] == normalized_input]
    if not exact_match.empty:
        return exact_match
    
    # Try partial match (handles "portland" matching "portland or")
    # Split input into parts to match flexibly
    input_parts = normalized_input.split()
    
    def matches_input(city_name):
        # Check if all input parts exist in city name
        return all(part in city_name for part in input_parts)
    
    partial_matches = df[df['location_normalized'].apply(matches_input)]
    
    if not partial_matches.empty:
        return partial_matches
    
    # Fallback: starts with (handles typos like "phoeni" -> "phoenix")
    if input_parts:
        first_word = input_parts[0]
        startswith_matches = df[df['location_normalized'].str.startswith(first_word)]
        return startswith_matches
    
    return pd.DataFrame()  # Empty DataFrame

def calculate_risk_score(city_data):
    """
    Calculate risk score from incident data
    """
    if city_data.empty:
        return None
    
    total_incidents = len(city_data)
    
    # Count specific risk factors (column is 'category' not 'Tags')
    use_of_force = len(city_data[city_data['category'].str.contains('Use of Force', na=False)])
    us_citizens = len(city_data[city_data['category'].str.contains('U.S. Citizen', na=False)])
    sensitive_locations = len(city_data[city_data['category'].str.contains('Sensitive Location', na=False)])
    
    # Scoring weights
    base_score = min(total_incidents * 2, 40)  # Cap at 40 for volume
    force_score = use_of_force * 1.5
    citizen_score = us_citizens * 1.2
    sensitive_score = sensitive_locations * 2
    
    total_score = base_score + force_score + citizen_score + sensitive_score
    risk_score = min(int(total_score), 100)  # Cap at 100
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = "High"
    elif risk_score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    # Convert to dict and clean NaN values for JSON serialization
    incidents_list = city_data.head(5).to_dict('records')
    for incident in incidents_list:
        # Replace NaN/None with empty strings for clean JSON
        for key, value in incident.items():
            if pd.isna(value):
                incident[key] = None
    
    return {
        'risk_level': risk_level,
        'risk_score': risk_score,
        'total_incidents': total_incidents,
        'use_of_force': use_of_force,
        'use_of_force_pct': round((use_of_force / total_incidents * 100) if total_incidents else 0, 1),
        'us_citizens': us_citizens,
        'us_citizens_pct': round((us_citizens / total_incidents * 100) if total_incidents else 0, 1),
        'sensitive_locations': sensitive_locations,
        'sensitive_locations_pct': round((sensitive_locations / total_incidents * 100) if total_incidents else 0, 1),
        'recent_incidents': incidents_list
    }

def get_last_updated(csv_path='protest_data_oversight.csv'):
    """Get last modified time of CSV file"""
    try:
        mtime = os.path.getmtime(csv_path)
        dt = datetime.fromtimestamp(mtime)
        hours_ago = int((datetime.now() - dt).total_seconds() / 3600)
        
        # Format time string with proper grammar
        if hours_ago == 0:
            time_str = "less than an hour ago"
        elif hours_ago == 1:
            time_str = "1 hour ago"
        else:
            time_str = f"{hours_ago} hours ago"
        
        return {'hours_ago': hours_ago, 'time_str': time_str, 'timestamp': dt.isoformat()}
    except:
        return {'hours_ago': None, 'time_str': None, 'timestamp': None}

def get_all_cities(csv_path='protest_data_oversight.csv'):
    """Get sorted list of all cities for autocomplete"""
    try:
        df = pd.read_csv(csv_path)
        cities = sorted(df['location'].str.strip().unique())
        return cities
    except:
        return []

def get_timeline_data(city_input=None, csv_path='protest_data_oversight.csv'):
    """Get incident counts by date for timeline chart"""
    try:
        df = pd.read_csv(csv_path)
        
        # Filter by city if provided
        if city_input:
            city_data = find_matching_cities(city_input, df)
            if city_data.empty:
                return []
            df = city_data
        
        # Parse dates and group by date
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        
        # Group by date and count incidents
        timeline = df.groupby(df['date'].dt.date).size().reset_index(name='count')
        timeline['date'] = timeline['date'].astype(str)
        
        return timeline.to_dict('records')
    except:
        return []

def get_risk_for_city(city_input, csv_path='protest_data_oversight.csv'):
    """
    Main function: load data, find city, calculate risk
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        return {'error': 'Data file not found. Please run scraper first.'}
    
    city_data = find_matching_cities(city_input, df)
    
    if city_data.empty:
        # Get list of available cities for suggestions (column is 'location')
        unique_cities = df['location'].str.strip().unique()[:20]
        return {
            'error': f'No data found for "{city_input}"',
            'suggestions': sorted(unique_cities)
        }
    
    # Show which cities were matched (for transparency)
    matched_cities = city_data['location'].str.strip().unique()
    
    risk_data = calculate_risk_score(city_data)
    risk_data['matched_cities'] = list(matched_cities)
    risk_data['search_term'] = city_input
    risk_data['timeline'] = get_timeline_data(city_input, csv_path)
    risk_data['last_updated'] = get_last_updated(csv_path)
    
    return risk_data
