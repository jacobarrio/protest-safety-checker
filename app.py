from flask import Flask, render_template, request, jsonify
from calculator import get_risk_for_city, get_all_cities, get_last_updated, get_timeline_data
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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
        return jsonify({'error': 'City name required'}), 400
    
    risk_data = get_risk_for_city(city)
    return jsonify(risk_data)

@app.route('/api/check/<city>')
def api_check_get(city):
    """API endpoint for programmatic access (GET with URL param)"""
    risk_data = get_risk_for_city(city)
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
    """Autocomplete endpoint - returns all cities as JSON"""
    cities = get_all_cities()
    return jsonify(cities)

@app.route('/api/last_updated')
def api_last_updated():
    """Get last data update time"""
    return jsonify(get_last_updated())

@app.route('/api/timeline')
def api_timeline():
    """Get timeline data (all incidents or filtered by city)"""
    city = request.args.get('city', None)
    timeline = get_timeline_data(city)
    return jsonify(timeline)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
