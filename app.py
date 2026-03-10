import os
import re
import json
from urllib.request import urlopen
from urllib.error import URLError
from flask import Flask, Response, render_template, request, jsonify, redirect
from calculator import (
    get_risk_for_city,
    get_all_cities,
    get_last_updated,
    get_timeline_data,
    search_cities,
    get_detention_facility_data,
    get_data_summary,
    get_black_site_signals,
    get_spending_analytics,
    get_live_feed,
    get_us_state_incident_counts,
    get_detention_death_tracker,
    get_contractor_tracker_data,
)
import pandas as pd

app = Flask(__name__)


def resolve_location_input(raw_input: str) -> str:
    """Accept city text or US ZIP code and normalize to city/state when possible."""
    value = (raw_input or '').strip()
    if not re.fullmatch(r'\d{5}', value):
        return value

    try:
        with urlopen(f'https://api.zippopotam.us/us/{value}', timeout=2.5) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
        places = payload.get('places') or []
        if not places:
            return value
        place = places[0]
        city = (place.get('place name') or '').strip()
        state = (place.get('state abbreviation') or '').strip()
        if city and state:
            return f"{city}, {state}"
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
        pass

    return value

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ice-risk-tracker')
@app.route('/risk-tracker')
@app.route('/tracker')
def legacy_tracker_redirects():
    return redirect('/')

@app.route('/favicon.ico')
def favicon():
    return Response(status=204)

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    return Response(status=204)

@app.route('/robots.txt')
def robots_txt():
    return Response("User-agent: *\nAllow: /\n", mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
        "<url><loc>https://protest-safety-checker-production.up.railway.app/</loc></url>"
        "<url><loc>https://protest-safety-checker-production.up.railway.app/detention-facilities</loc></url>"
        "<url><loc>https://protest-safety-checker-production.up.railway.app/intel</loc></url>"
        "<url><loc>https://protest-safety-checker-production.up.railway.app/health</loc></url>"
        "</urlset>"
    )
    return Response(xml, mimetype='application/xml')

@app.route('/for-organizers')
def for_organizers():
    return render_template('for_organizers.html')

@app.route('/for-researchers')
def for_researchers():
    return render_template('for_researchers.html')

@app.route('/methodology')
def methodology():
    return render_template('methodology.html')

@app.route('/safety-privacy')
def safety_privacy():
    return render_template('safety_privacy.html')

@app.route('/check', methods=['POST'])
def check_risk():
    city_input = request.form.get('city', '').strip()

    if not city_input:
        return render_template('index.html',
            error='Please enter a city name')

    risk_data = get_risk_for_city(city_input)

    if 'error' in risk_data:
        return render_template('index.html',
            error=risk_data['error'],
            suggestions=risk_data.get('suggestions', []))

    return render_template('results.html', data=risk_data)

@app.route('/api/check', methods=['POST'])
def api_check_post():
    """API endpoint for programmatic access (POST with JSON)"""
    data = request.get_json()
    city = data.get('city', '').strip()

    if not city:
        return jsonify({'error': 'City or ZIP required'}), 400

    resolved_city = resolve_location_input(city)
    risk_data = get_risk_for_city(resolved_city)
    if isinstance(risk_data, dict):
        risk_data['query_input'] = city
        risk_data['resolved_location'] = resolved_city
    return jsonify(risk_data)

@app.route('/api/check/<city>')
def api_check_get(city):
    """API endpoint for programmatic access (GET with URL param)"""
    resolved_city = resolve_location_input(city)
    risk_data = get_risk_for_city(resolved_city)
    if isinstance(risk_data, dict):
        risk_data['query_input'] = city
        risk_data['resolved_location'] = resolved_city
    return jsonify(risk_data)

@app.route('/cities')
def list_cities():
    """List all available cities"""
    try:
        df = pd.read_csv('protest_data_oversight.csv')
        cities = sorted(df['location'].str.strip().unique())
        return render_template('cities.html', cities=cities)
    except:
        return "Error loading cities", 500

@app.route('/api/cities')
def api_cities():
    """Autocomplete endpoint - supports optional query filtering"""
    query = request.args.get('q', '').strip()
    if query:
        cities = search_cities(query, limit=10)
    else:
        cities = get_all_cities()
    return jsonify(cities)

@app.route('/api/last_updated')
def api_last_updated():
    """Get last data update time"""
    return jsonify(get_last_updated())

@app.route('/api/data_summary')
def api_data_summary():
    """Get high-level dataset transparency stats"""
    return jsonify(get_data_summary())

@app.route('/detention-facilities')
def detention_facilities():
    """Detention/facility related incidents transparency page"""
    data = get_detention_facility_data()
    summary = get_data_summary()
    last_updated = get_last_updated()
    return render_template('detention_facilities.html', data=data, summary=summary, last_updated=last_updated)

@app.route('/intel')
def intelligence_dashboard():
    """Detention + spending + signal intelligence dashboard"""
    detention = get_detention_facility_data()
    black_sites = get_black_site_signals()
    spending = get_spending_analytics()
    summary = get_data_summary()
    return render_template(
        'intelligence.html',
        detention=detention,
        black_sites=black_sites,
        spending=spending,
        summary=summary,
        last_updated=get_last_updated(),
    )

@app.route('/api/live-feed')
def api_live_feed():
    limit = int(request.args.get('limit', 30))
    return jsonify(get_live_feed(limit=limit))

@app.route('/api/spending-analytics')
def api_spending_analytics():
    return jsonify(get_spending_analytics())

@app.route('/api/timeline')
def api_timeline():
    """Get timeline data (all incidents or filtered by city)"""
    city = request.args.get('city', None)
    timeline = get_timeline_data(city)
    return jsonify(timeline)

@app.route('/api/us-map')
def api_us_map():
    """US state-level incident footprint for homepage map."""
    return jsonify(get_us_state_incident_counts())

@app.route('/api/death-tracker')
def api_death_tracker():
    return jsonify(get_detention_death_tracker())

@app.route('/api/contractor-tracker')
def api_contractor_tracker():
    return jsonify(get_contractor_tracker_data())

@app.route('/health', methods=['GET'])
def health():
    return {'ok': True}, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
