import pandas as pd
import re
from datetime import datetime
import os
from difflib import SequenceMatcher, get_close_matches

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

def _read_incident_csv(csv_path):
    """Read CSV and repair common malformed location rows (e.g. unquoted 'City, ST')."""
    df = pd.read_csv(csv_path)

    # If location looks like just state abbreviations and index contains city names,
    # reconstruct location from index + location.
    if 'location' in df.columns and not isinstance(df.index, pd.RangeIndex):
        location_vals = df['location'].astype(str).str.strip()
        likely_state = location_vals.str.fullmatch(r'[A-Z]{2}').fillna(False)
        if likely_state.mean() > 0.5:
            city_part = pd.Index(df.index.astype(str)).str.strip()
            df = df.reset_index(drop=True)
            df['location'] = [f"{city}, {state}" for city, state in zip(city_part, location_vals)]

    return df


def _normalize_location_series(df):
    """Return a copy of df with normalized location column for matching."""
    df_copy = df.copy()
    df_copy['location_normalized'] = df_copy['location'].str.strip().str.lower().apply(
        lambda x: re.sub(r'[,\s]+', ' ', x).strip()
    )
    return df_copy


def search_cities(query, csv_path='protest_data_oversight.csv', limit=10):
    """Return ranked city suggestions for autocomplete and typo tolerance."""
    cities = get_all_cities(csv_path)
    if not cities:
        return []

    normalized_query = normalize_city_input(query)
    if not normalized_query:
        return cities[:limit]

    scored = []
    for city in cities:
        normalized_city = normalize_city_input(city)
        score = 0.0

        if normalized_city == normalized_query:
            score = 1.0
        elif normalized_city.startswith(normalized_query):
            score = 0.95
        elif normalized_query in normalized_city:
            score = 0.85
        else:
            score = SequenceMatcher(None, normalized_query, normalized_city).ratio()

        if score >= 0.45:
            scored.append((city, score))

    if not scored:
        normalized_map = {normalize_city_input(city): city for city in cities}
        fuzzy_norm = get_close_matches(normalized_query, list(normalized_map.keys()), n=limit, cutoff=0.55)
        return [normalized_map[norm] for norm in fuzzy_norm]

    scored.sort(key=lambda item: (-item[1], item[0]))
    return [city for city, _ in scored[:limit]]


def find_matching_cities(user_input, df):
    """
    Find all cities that match user input (handles variations)
    Returns DataFrame of matching incidents
    """
    normalized_input = normalize_city_input(user_input)
    if not normalized_input or df.empty:
        return pd.DataFrame()

    df_norm = _normalize_location_series(df)

    # Try exact match first
    exact_match = df_norm[df_norm['location_normalized'] == normalized_input]
    if not exact_match.empty:
        return exact_match
    
    # Try partial match (handles "portland" matching "portland or")
    # Split input into parts to match flexibly
    input_parts = normalized_input.split()
    
    def matches_input(city_name):
        # Check if all input parts exist in city name
        return all(part in city_name for part in input_parts)
    
    partial_matches = df_norm[df_norm['location_normalized'].apply(matches_input)]

    if not partial_matches.empty:
        return partial_matches

    # Fallback: starts with (handles typos like "phoeni" -> "phoenix")
    if input_parts:
        first_word = input_parts[0]
        startswith_matches = df_norm[df_norm['location_normalized'].str.startswith(first_word)]
        if not startswith_matches.empty:
            return startswith_matches

    # Fuzzy fallback: pick closest normalized location labels
    unique_norm_locations = df_norm['location_normalized'].dropna().unique().tolist()
    fuzzy_matches = get_close_matches(normalized_input, unique_norm_locations, n=3, cutoff=0.65)
    if fuzzy_matches:
        return df_norm[df_norm['location_normalized'].isin(fuzzy_matches)]

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

    score_breakdown = {
        'formula': 'min((incidents*2, cap 40) + (use_of_force*1.5) + (us_citizens*1.2) + (sensitive_locations*2), 100)',
        'components': [
            {
                'name': 'Incident volume',
                'count': total_incidents,
                'weight': 2.0,
                'raw_score': total_incidents * 2,
                'capped_score': round(base_score, 2),
                'cap': 40
            },
            {
                'name': 'Use of Force incidents',
                'count': use_of_force,
                'weight': 1.5,
                'raw_score': round(force_score, 2)
            },
            {
                'name': 'U.S. Citizen incidents',
                'count': us_citizens,
                'weight': 1.2,
                'raw_score': round(citizen_score, 2)
            },
            {
                'name': 'Sensitive Location incidents',
                'count': sensitive_locations,
                'weight': 2.0,
                'raw_score': round(sensitive_score, 2)
            }
        ],
        'pre_cap_total': round(total_score, 2),
        'final_score': risk_score
    }
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = "High"
    elif risk_score >= 30:
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
        'recent_incidents': incidents_list,
        'score_breakdown': score_breakdown
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
        df = _read_incident_csv(csv_path)
        cities = sorted(df['location'].astype(str).str.strip().unique())
        return cities
    except:
        return []

def get_timeline_data(city_input=None, csv_path='protest_data_oversight.csv'):
    """Get incident counts by date for timeline chart"""
    try:
        df = _read_incident_csv(csv_path)
        
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
        df = _read_incident_csv(csv_path)
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
