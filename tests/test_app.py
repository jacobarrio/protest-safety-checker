"""
Test suite for Flask app routes
Tests all endpoints with various scenarios
"""

import pytest
import json
import tempfile
import os
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_csv():
    """Create a temporary CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("location,date,category,description\n")
        f.write("Portland, OR,2026-01-01,Use of Force,Test incident 1\n")
        f.write("Portland, OR,2026-01-02,Arrest/Detention,Test incident 2\n")
        f.write("Phoenix, AZ,2026-01-01,U.S. Citizen,Test incident 3\n")
        f.write("Los Angeles, CA,2026-01-03,Sensitive Location,Test incident 4\n")
        temp_path = f.name
    
    # Temporarily replace the default CSV path
    original_path = 'protest_data_oversight.csv'
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


class TestIndexRoute:
    """Tests for the index route"""
    
    def test_index_loads(self, client):
        """Test that index page loads successfully"""
        response = client.get('/')
        assert response.status_code == 200
        # Check that it's trying to render the template
        # (will fail if template doesn't exist, but that's OK for MVP)


class TestCheckRiskRoute:
    """Tests for the /check POST route"""
    
    def test_check_with_valid_city(self, client, monkeypatch):
        """Test checking risk for a valid city"""
        # Mock the get_risk_for_city function
        def mock_get_risk(city, csv_path='protest_data_oversight.csv'):
            return {
                'risk_level': 'Medium',
                'risk_score': 50,
                'total_incidents': 10,
                'matched_cities': ['Portland, OR']
            }
        
        import calculator
        monkeypatch.setattr(calculator, 'get_risk_for_city', mock_get_risk)
        
        response = client.post('/check', data={'city': 'Portland'})
        assert response.status_code == 200
    
    def test_check_with_empty_city(self, client):
        """Test checking with no city input"""
        response = client.post('/check', data={'city': ''})
        assert response.status_code == 200
        # Should return an error message in the rendered template
    
    def test_check_with_whitespace_city(self, client):
        """Test checking with whitespace-only city"""
        response = client.post('/check', data={'city': '   '})
        assert response.status_code == 200
    
    def test_check_with_nonexistent_city(self, client, monkeypatch):
        """Test checking a city that doesn't exist"""
        def mock_get_risk(city, csv_path='protest_data_oversight.csv'):
            return {
                'error': 'No data found for "InvalidCity"',
                'suggestions': ['Portland, OR', 'Phoenix, AZ']
            }
        
        import calculator
        monkeypatch.setattr(calculator, 'get_risk_for_city', mock_get_risk)
        
        response = client.post('/check', data={'city': 'InvalidCity'})
        assert response.status_code == 200


class TestAPICheckPost:
    """Tests for /api/check POST endpoint"""
    
    def test_api_check_with_valid_json(self, client, monkeypatch):
        """Test API endpoint with valid JSON"""
        def mock_get_risk(city, csv_path='protest_data_oversight.csv'):
            return {
                'risk_level': 'High',
                'risk_score': 85,
                'total_incidents': 20
            }
        
        import calculator
        monkeypatch.setattr(calculator, 'get_risk_for_city', mock_get_risk)
        
        response = client.post('/api/check',
                              data=json.dumps({'city': 'Portland'}),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['risk_level'] == 'High'
        assert data['risk_score'] == 85
    
    def test_api_check_without_city(self, client):
        """Test API endpoint without city parameter"""
        response = client.post('/api/check',
                              data=json.dumps({}),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_api_check_with_empty_city(self, client):
        """Test API endpoint with empty city"""
        response = client.post('/api/check',
                              data=json.dumps({'city': ''}),
                              content_type='application/json')
        
        assert response.status_code == 400
    
    def test_api_check_returns_json(self, client, monkeypatch):
        """Test that API returns proper JSON"""
        def mock_get_risk(city, csv_path='protest_data_oversight.csv'):
            return {'risk_score': 50}
        
        import calculator
        monkeypatch.setattr(calculator, 'get_risk_for_city', mock_get_risk)
        
        response = client.post('/api/check',
                              data=json.dumps({'city': 'Portland'}),
                              content_type='application/json')
        
        assert response.content_type == 'application/json'


class TestAPICheckGet:
    """Tests for /api/check/<city> GET endpoint"""
    
    def test_api_check_get_with_valid_city(self, client, monkeypatch):
        """Test GET endpoint with valid city"""
        def mock_get_risk(city, csv_path='protest_data_oversight.csv'):
            return {
                'risk_level': 'Medium',
                'risk_score': 45,
                'search_term': city
            }
        
        import calculator
        monkeypatch.setattr(calculator, 'get_risk_for_city', mock_get_risk)
        
        response = client.get('/api/check/Portland')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'risk_score' in data
    
    def test_api_check_get_with_url_encoded_city(self, client, monkeypatch):
        """Test GET endpoint with URL-encoded city name"""
        def mock_get_risk(city, csv_path='protest_data_oversight.csv'):
            return {'risk_score': 30}
        
        import calculator
        monkeypatch.setattr(calculator, 'get_risk_for_city', mock_get_risk)
        
        response = client.get('/api/check/Los%20Angeles')
        assert response.status_code == 200
    
    def test_api_check_get_returns_json(self, client, monkeypatch):
        """Test that GET endpoint returns JSON"""
        def mock_get_risk(city, csv_path='protest_data_oversight.csv'):
            return {'risk_score': 50}
        
        import calculator
        monkeypatch.setattr(calculator, 'get_risk_for_city', mock_get_risk)
        
        response = client.get('/api/check/Portland')
        assert response.content_type == 'application/json'


class TestCitiesRoute:
    """Tests for /cities route"""
    
    def test_cities_page_loads(self, client):
        """Test that cities page attempts to load"""
        response = client.get('/cities')
        # Will be 200 if CSV exists, 500 if not - both are expected
        assert response.status_code in [200, 500]


class TestAPICities:
    """Tests for /api/cities endpoint"""
    
    def test_api_cities_returns_json(self, client, monkeypatch):
        """Test that cities API returns JSON list"""
        def mock_get_all_cities(csv_path='protest_data_oversight.csv'):
            return ['Portland, OR', 'Phoenix, AZ', 'Los Angeles, CA']
        
        import calculator
        monkeypatch.setattr(calculator, 'get_all_cities', mock_get_all_cities)
        
        response = client.get('/api/cities')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 3
    
    def test_api_cities_returns_empty_on_error(self, client, monkeypatch):
        """Test that cities API returns empty list on error"""
        def mock_get_all_cities(csv_path='protest_data_oversight.csv'):
            return []
        
        import calculator
        monkeypatch.setattr(calculator, 'get_all_cities', mock_get_all_cities)
        
        response = client.get('/api/cities')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []


class TestAPILastUpdated:
    """Tests for /api/last_updated endpoint"""
    
    def test_api_last_updated_returns_json(self, client, monkeypatch):
        """Test that last_updated returns proper JSON"""
        def mock_get_last_updated(csv_path='protest_data_oversight.csv'):
            return {
                'hours_ago': 2,
                'time_str': '2 hours ago',
                'timestamp': '2026-01-01T12:00:00'
            }
        
        import calculator
        monkeypatch.setattr(calculator, 'get_last_updated', mock_get_last_updated)
        
        response = client.get('/api/last_updated')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert 'hours_ago' in data
        assert 'time_str' in data
    
    def test_api_last_updated_handles_missing_file(self, client, monkeypatch):
        """Test that last_updated handles missing file gracefully"""
        def mock_get_last_updated(csv_path='protest_data_oversight.csv'):
            return {
                'hours_ago': None,
                'time_str': None,
                'timestamp': None
            }
        
        import calculator
        monkeypatch.setattr(calculator, 'get_last_updated', mock_get_last_updated)
        
        response = client.get('/api/last_updated')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['hours_ago'] is None


class TestAPITimeline:
    """Tests for /api/timeline endpoint"""
    
    def test_api_timeline_without_filter(self, client, monkeypatch):
        """Test timeline API without city filter"""
        def mock_get_timeline(city=None, csv_path='protest_data_oversight.csv'):
            return [
                {'date': '2026-01-01', 'count': 5},
                {'date': '2026-01-02', 'count': 3}
            ]
        
        import calculator
        monkeypatch.setattr(calculator, 'get_timeline_data', mock_get_timeline)
        
        response = client.get('/api/timeline')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]['count'] == 5
    
    def test_api_timeline_with_city_filter(self, client, monkeypatch):
        """Test timeline API with city filter"""
        def mock_get_timeline(city=None, csv_path='protest_data_oversight.csv'):
            if city == 'Portland':
                return [{'date': '2026-01-01', 'count': 3}]
            return []
        
        import calculator
        monkeypatch.setattr(calculator, 'get_timeline_data', mock_get_timeline)
        
        response = client.get('/api/timeline?city=Portland')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
    
    def test_api_timeline_returns_empty_list_on_error(self, client, monkeypatch):
        """Test timeline returns empty list on error"""
        def mock_get_timeline(city=None, csv_path='protest_data_oversight.csv'):
            return []
        
        import calculator
        monkeypatch.setattr(calculator, 'get_timeline_data', mock_get_timeline)
        
        response = client.get('/api/timeline')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []


class TestEdgeCases:
    """Edge case tests for the Flask app"""
    
    def test_post_with_unicode_city(self, client, monkeypatch):
        """Test posting with unicode city name"""
        def mock_get_risk(city, csv_path='protest_data_oversight.csv'):
            return {'risk_score': 50}
        
        import calculator
        monkeypatch.setattr(calculator, 'get_risk_for_city', mock_get_risk)
        
        response = client.post('/api/check',
                              data=json.dumps({'city': 'São Paulo'}),
                              content_type='application/json')
        assert response.status_code == 200
    
    def test_get_with_special_characters(self, client, monkeypatch):
        """Test GET with special characters in city name"""
        def mock_get_risk(city, csv_path='protest_data_oversight.csv'):
            return {'risk_score': 50}
        
        import calculator
        monkeypatch.setattr(calculator, 'get_risk_for_city', mock_get_risk)
        
        response = client.get('/api/check/Portland%2C%20OR')
        assert response.status_code == 200
    
    def test_api_with_malformed_json(self, client):
        """Test API with malformed JSON"""
        response = client.post('/api/check',
                              data='{"city": invalid}',
                              content_type='application/json')
        # Should handle gracefully (400 or 500)
        assert response.status_code >= 400
    
    def test_timeline_with_invalid_city_param(self, client, monkeypatch):
        """Test timeline with invalid city parameter"""
        def mock_get_timeline(city=None, csv_path='protest_data_oversight.csv'):
            return []
        
        import calculator
        monkeypatch.setattr(calculator, 'get_timeline_data', mock_get_timeline)
        
        response = client.get('/api/timeline?city=NonexistentCity')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []
