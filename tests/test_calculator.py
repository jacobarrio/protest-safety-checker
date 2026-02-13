"""
Comprehensive test suite for calculator.py
Tests all functions with edge cases, unicode, special characters, etc.
"""

import pytest
import pandas as pd
import os
import tempfile
from datetime import datetime
from calculator import (
    normalize_city_input,
    find_matching_cities,
    calculate_risk_score,
    get_last_updated,
    get_all_cities,
    get_timeline_data,
    get_risk_for_city
)


class TestNormalizeCityInput:
    """Tests for normalize_city_input() function"""
    
    def test_basic_normalization(self):
        """Test basic lowercase and strip"""
        assert normalize_city_input("Portland") == "portland"
        assert normalize_city_input("NEW YORK") == "new york"
    
    def test_strip_whitespace(self):
        """Test stripping leading/trailing whitespace"""
        assert normalize_city_input("  Portland  ") == "portland"
        assert normalize_city_input("\tPhoenix\n") == "phoenix"
    
    def test_remove_commas(self):
        """Test comma removal"""
        assert normalize_city_input("Portland, OR") == "portland or"
        assert normalize_city_input("Los Angeles, CA") == "los angeles ca"
    
    def test_multiple_spaces(self):
        """Test collapsing multiple spaces"""
        assert normalize_city_input("Los    Angeles") == "los angeles"
        assert normalize_city_input("New  York  City") == "new york city"
    
    def test_mixed_punctuation(self):
        """Test handling mixed punctuation"""
        assert normalize_city_input("Portland, OR  ") == "portland or"
        assert normalize_city_input("  ,  Portland  ,  ") == "portland"
    
    def test_empty_string(self):
        """Test empty string handling"""
        assert normalize_city_input("") == ""
        assert normalize_city_input("   ") == ""
    
    def test_unicode_characters(self):
        """Test unicode city names"""
        assert normalize_city_input("São Paulo") == "são paulo"
        assert normalize_city_input("Montréal") == "montréal"
        assert normalize_city_input("München") == "münchen"
    
    def test_special_characters(self):
        """Test special characters get normalized"""
        # Commas should be replaced with spaces
        assert normalize_city_input("City,State") == "city state"
        # Multiple commas
        assert normalize_city_input("City,,,,State") == "city state"
    
    def test_single_word(self):
        """Test single word cities"""
        assert normalize_city_input("Chicago") == "chicago"
        assert normalize_city_input("MIAMI") == "miami"


class TestFindMatchingCities:
    """Tests for find_matching_cities() function"""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing"""
        return pd.DataFrame({
            'location': [
                'Portland, OR',
                'Portland, ME',
                'Phoenix, AZ',
                'Los Angeles, CA',
                'New York, NY',
                'San Francisco, CA'
            ],
            'date': ['2026-01-01'] * 6,
            'category': ['Use of Force'] * 6,
            'description': ['Test incident'] * 6
        })
    
    def test_exact_match(self, sample_df):
        """Test exact city match"""
        result = find_matching_cities("Portland, OR", sample_df)
        assert len(result) == 1
        assert 'Portland, OR' in result['location'].values
    
    def test_exact_match_case_insensitive(self, sample_df):
        """Test case insensitive exact match"""
        result = find_matching_cities("PORTLAND, OR", sample_df)
        assert len(result) == 1
        assert 'Portland, OR' in result['location'].values
    
    def test_partial_match(self, sample_df):
        """Test partial matching (e.g., 'portland' matches both Portlands)"""
        result = find_matching_cities("Portland", sample_df)
        assert len(result) == 2
        assert 'Portland, OR' in result['location'].values
        assert 'Portland, ME' in result['location'].values
    
    def test_multi_word_partial_match(self, sample_df):
        """Test multi-word partial matching"""
        result = find_matching_cities("Los Angeles", sample_df)
        assert len(result) == 1
        assert 'Los Angeles, CA' in result['location'].values
    
    def test_prefix_match(self, sample_df):
        """Test prefix matching for typos"""
        result = find_matching_cities("phoeni", sample_df)
        assert len(result) == 1
        assert 'Phoenix, AZ' in result['location'].values
    
    def test_no_match(self, sample_df):
        """Test no matching city"""
        result = find_matching_cities("Boston", sample_df)
        assert result.empty
    
    def test_empty_input(self, sample_df):
        """Test empty string input"""
        result = find_matching_cities("", sample_df)
        assert result.empty
    
    def test_whitespace_only(self, sample_df):
        """Test whitespace-only input"""
        result = find_matching_cities("   ", sample_df)
        assert result.empty
    
    def test_special_characters_in_search(self, sample_df):
        """Test searching with special characters"""
        result = find_matching_cities("Portland, OR", sample_df)
        assert len(result) == 1
    
    def test_unicode_city_names(self):
        """Test unicode city names"""
        df = pd.DataFrame({
            'location': ['São Paulo, Brazil', 'Montréal, Canada'],
            'date': ['2026-01-01'] * 2,
            'category': ['Use of Force'] * 2,
            'description': ['Test'] * 2
        })
        result = find_matching_cities("são paulo", df)
        assert len(result) == 1
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame"""
        df = pd.DataFrame(columns=['location', 'date', 'category', 'description'])
        result = find_matching_cities("Portland", df)
        assert result.empty


class TestCalculateRiskScore:
    """Tests for calculate_risk_score() function"""
    
    def test_basic_risk_calculation(self):
        """Test basic risk score calculation"""
        df = pd.DataFrame({
            'location': ['Portland, OR'] * 10,
            'category': ['Use of Force'] * 5 + ['Arrest/Detention'] * 5,
            'date': ['2026-01-01'] * 10,
            'description': ['Incident'] * 10
        })
        result = calculate_risk_score(df)
        
        assert result is not None
        assert 'risk_score' in result
        assert 'risk_level' in result
        assert 'total_incidents' in result
        assert result['total_incidents'] == 10
        assert result['use_of_force'] == 5
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame"""
        df = pd.DataFrame(columns=['location', 'category', 'date', 'description'])
        result = calculate_risk_score(df)
        assert result is None
    
    def test_high_risk_score(self):
        """Test high risk classification"""
        df = pd.DataFrame({
            'location': ['City'] * 50,
            'category': ['Use of Force'] * 30 + ['U.S. Citizen'] * 20,
            'date': ['2026-01-01'] * 50,
            'description': ['Incident'] * 50
        })
        result = calculate_risk_score(df)
        assert result['risk_level'] == 'High'
        assert result['risk_score'] >= 70
    
    def test_medium_risk_score(self):
        """Test medium risk classification"""
        df = pd.DataFrame({
            'location': ['City'] * 15,
            'category': ['Use of Force'] * 5 + ['Arrest/Detention'] * 10,
            'date': ['2026-01-01'] * 15,
            'description': ['Incident'] * 15
        })
        result = calculate_risk_score(df)
        assert result['risk_level'] == 'Medium'
        assert 40 <= result['risk_score'] < 70
    
    def test_low_risk_score(self):
        """Test low risk classification"""
        df = pd.DataFrame({
            'location': ['City'] * 5,
            'category': ['Arrest/Detention'] * 5,
            'date': ['2026-01-01'] * 5,
            'description': ['Incident'] * 5
        })
        result = calculate_risk_score(df)
        assert result['risk_level'] == 'Low'
        assert result['risk_score'] < 40
    
    def test_risk_score_capped_at_100(self):
        """Test risk score is capped at 100"""
        # Create dataset that would score > 100
        df = pd.DataFrame({
            'location': ['City'] * 100,
            'category': ['Use of Force'] * 50 + ['Sensitive Location'] * 50,
            'date': ['2026-01-01'] * 100,
            'description': ['Incident'] * 100
        })
        result = calculate_risk_score(df)
        assert result['risk_score'] <= 100
    
    def test_percentages_calculated(self):
        """Test percentage calculations"""
        df = pd.DataFrame({
            'location': ['City'] * 10,
            'category': ['Use of Force'] * 3 + ['U.S. Citizen'] * 2 + ['Arrest/Detention'] * 5,
            'date': ['2026-01-01'] * 10,
            'description': ['Incident'] * 10
        })
        result = calculate_risk_score(df)
        
        assert result['use_of_force_pct'] == 30.0
        assert result['us_citizens_pct'] == 20.0
    
    def test_recent_incidents_limited_to_5(self):
        """Test recent incidents are limited to 5"""
        df = pd.DataFrame({
            'location': ['City'] * 10,
            'category': ['Use of Force'] * 10,
            'date': ['2026-01-01'] * 10,
            'description': [f'Incident {i}' for i in range(10)]
        })
        result = calculate_risk_score(df)
        
        assert len(result['recent_incidents']) == 5
    
    def test_nan_values_handled(self):
        """Test NaN values are handled properly"""
        df = pd.DataFrame({
            'location': ['City'] * 5,
            'category': ['Use of Force', None, 'U.S. Citizen', None, 'Arrest/Detention'],
            'date': ['2026-01-01'] * 5,
            'description': ['Incident', None, 'Test', None, 'Another']
        })
        result = calculate_risk_score(df)
        
        assert result is not None
        # Check that None values don't break JSON serialization
        assert all(
            value is None or isinstance(value, (str, int, float, bool))
            for incident in result['recent_incidents']
            for value in incident.values()
        )
    
    def test_zero_incidents_percentages(self):
        """Test percentages when there are no matching categories"""
        df = pd.DataFrame({
            'location': ['City'] * 5,
            'category': ['Other'] * 5,  # No recognized categories
            'date': ['2026-01-01'] * 5,
            'description': ['Incident'] * 5
        })
        result = calculate_risk_score(df)
        
        assert result['use_of_force_pct'] == 0
        assert result['us_citizens_pct'] == 0
        assert result['sensitive_locations_pct'] == 0
    
    def test_sensitive_location_category(self):
        """Test sensitive location category detection"""
        df = pd.DataFrame({
            'location': ['City'] * 5,
            'category': ['Sensitive Location'] * 5,
            'date': ['2026-01-01'] * 5,
            'description': ['School arrest'] * 5
        })
        result = calculate_risk_score(df)
        
        assert result['sensitive_locations'] == 5
        assert result['sensitive_locations_pct'] == 100.0


class TestGetLastUpdated:
    """Tests for get_last_updated() function"""
    
    def test_with_existing_file(self):
        """Test with existing CSV file"""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("test,data\n")
            temp_path = f.name
        
        try:
            result = get_last_updated(temp_path)
            
            assert 'hours_ago' in result
            assert 'time_str' in result
            assert 'timestamp' in result
            assert isinstance(result['hours_ago'], int)
            assert result['hours_ago'] == 0  # Just created
            assert result['time_str'] == "less than an hour ago"
        finally:
            os.unlink(temp_path)
    
    def test_with_nonexistent_file(self):
        """Test with nonexistent file"""
        result = get_last_updated('/nonexistent/file.csv')
        
        assert result['hours_ago'] is None
        assert result['time_str'] is None
        assert result['timestamp'] is None
    
    def test_time_string_formatting(self):
        """Test time string formatting logic"""
        # This is more of an integration test - we can't easily mock file timestamps
        # but we can verify the structure
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("test\n")
            temp_path = f.name
        
        try:
            result = get_last_updated(temp_path)
            assert result['time_str'] in ["less than an hour ago", "1 hour ago"] or "hours ago" in result['time_str']
        finally:
            os.unlink(temp_path)


class TestGetAllCities:
    """Tests for get_all_cities() function"""
    
    def test_with_valid_csv(self):
        """Test getting cities from valid CSV"""
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category\n")
            f.write("Portland, OR,2026-01-01,Use of Force\n")
            f.write("Phoenix, AZ,2026-01-02,Arrest/Detention\n")
            f.write("Portland, OR,2026-01-03,U.S. Citizen\n")  # Duplicate
            temp_path = f.name
        
        try:
            cities = get_all_cities(temp_path)
            
            assert len(cities) == 2  # Unique cities only
            assert 'Phoenix, AZ' in cities
            assert 'Portland, OR' in cities
            # Should be sorted
            assert cities == sorted(cities)
        finally:
            os.unlink(temp_path)
    
    def test_with_nonexistent_file(self):
        """Test with nonexistent CSV file"""
        cities = get_all_cities('/nonexistent/file.csv')
        assert cities == []
    
    def test_cities_sorted(self):
        """Test that cities are sorted alphabetically"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category\n")
            f.write("Zebra City,2026-01-01,Use of Force\n")
            f.write("Apple City,2026-01-02,Arrest/Detention\n")
            f.write("Middle City,2026-01-03,U.S. Citizen\n")
            temp_path = f.name
        
        try:
            cities = get_all_cities(temp_path)
            assert cities[0] == 'Apple City'
            assert cities[-1] == 'Zebra City'
        finally:
            os.unlink(temp_path)


class TestGetTimelineData:
    """Tests for get_timeline_data() function"""
    
    def test_timeline_all_incidents(self):
        """Test getting timeline for all incidents"""
        # Create temporary CSV with date data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category,description\n")
            f.write("Portland, OR,2026-01-01,Use of Force,Test1\n")
            f.write("Portland, OR,2026-01-01,Arrest/Detention,Test2\n")
            f.write("Phoenix, AZ,2026-01-02,Use of Force,Test3\n")
            temp_path = f.name
        
        try:
            timeline = get_timeline_data(csv_path=temp_path)
            
            assert len(timeline) == 2  # Two unique dates
            # Check structure
            assert all('date' in item and 'count' in item for item in timeline)
            # Check counts
            date_counts = {item['date']: item['count'] for item in timeline}
            assert date_counts['2026-01-01'] == 2
            assert date_counts['2026-01-02'] == 1
        finally:
            os.unlink(temp_path)
    
    def test_timeline_filtered_by_city(self):
        """Test getting timeline filtered by city"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category,description\n")
            f.write("Portland, OR,2026-01-01,Use of Force,Test1\n")
            f.write("Portland, OR,2026-01-02,Arrest/Detention,Test2\n")
            f.write("Phoenix, AZ,2026-01-01,Use of Force,Test3\n")
            temp_path = f.name
        
        try:
            timeline = get_timeline_data(city_input="Portland", csv_path=temp_path)
            
            assert len(timeline) == 2  # Portland has incidents on 2 dates
            # Should only include Portland incidents
            total_count = sum(item['count'] for item in timeline)
            assert total_count == 2
        finally:
            os.unlink(temp_path)
    
    def test_timeline_with_invalid_dates(self):
        """Test timeline handles invalid dates"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category,description\n")
            f.write("Portland, OR,invalid-date,Use of Force,Test1\n")
            f.write("Portland, OR,2026-01-01,Arrest/Detention,Test2\n")
            temp_path = f.name
        
        try:
            timeline = get_timeline_data(csv_path=temp_path)
            # Should only return valid dates
            assert len(timeline) == 1
            assert timeline[0]['date'] == '2026-01-01'
        finally:
            os.unlink(temp_path)
    
    def test_timeline_with_nonexistent_file(self):
        """Test timeline with nonexistent file"""
        timeline = get_timeline_data(csv_path='/nonexistent/file.csv')
        assert timeline == []
    
    def test_timeline_empty_for_nonexistent_city(self):
        """Test timeline returns empty for nonexistent city"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category,description\n")
            f.write("Portland, OR,2026-01-01,Use of Force,Test\n")
            temp_path = f.name
        
        try:
            timeline = get_timeline_data(city_input="Boston", csv_path=temp_path)
            assert timeline == []
        finally:
            os.unlink(temp_path)


class TestGetRiskForCity:
    """Tests for get_risk_for_city() - the main integration function"""
    
    def test_successful_risk_calculation(self):
        """Test successful risk calculation for a city"""
        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category,description\n")
            f.write("Portland, OR,2026-01-01,Use of Force,Test1\n")
            f.write("Portland, OR,2026-01-02,Arrest/Detention,Test2\n")
            f.write("Portland, OR,2026-01-03,U.S. Citizen,Test3\n")
            temp_path = f.name
        
        try:
            result = get_risk_for_city("Portland", csv_path=temp_path)
            
            assert 'error' not in result
            assert result['risk_score'] is not None
            assert result['total_incidents'] == 3
            assert 'matched_cities' in result
            assert 'Portland, OR' in result['matched_cities']
            assert 'search_term' in result
            assert result['search_term'] == "Portland"
            assert 'timeline' in result
            assert 'last_updated' in result
        finally:
            os.unlink(temp_path)
    
    def test_city_not_found(self):
        """Test handling of city not found"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category,description\n")
            f.write("Portland, OR,2026-01-01,Use of Force,Test\n")
            temp_path = f.name
        
        try:
            result = get_risk_for_city("Boston", csv_path=temp_path)
            
            assert 'error' in result
            assert 'Boston' in result['error']
            assert 'suggestions' in result
        finally:
            os.unlink(temp_path)
    
    def test_file_not_found(self):
        """Test handling of missing data file"""
        result = get_risk_for_city("Portland", csv_path='/nonexistent/file.csv')
        
        assert 'error' in result
        assert 'not found' in result['error'].lower()
    
    def test_empty_city_input(self):
        """Test handling of empty city input"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category,description\n")
            f.write("Portland, OR,2026-01-01,Use of Force,Test\n")
            temp_path = f.name
        
        try:
            result = get_risk_for_city("", csv_path=temp_path)
            # Empty input should not find any matches
            assert 'error' in result
        finally:
            os.unlink(temp_path)
    
    def test_suggestions_returned_on_error(self):
        """Test that suggestions are returned when city not found"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category,description\n")
            f.write("Portland, OR,2026-01-01,Use of Force,Test\n")
            f.write("Phoenix, AZ,2026-01-02,Arrest/Detention,Test\n")
            temp_path = f.name
        
        try:
            result = get_risk_for_city("InvalidCity", csv_path=temp_path)
            
            assert 'suggestions' in result
            assert len(result['suggestions']) > 0
            assert len(result['suggestions']) <= 20  # Limited to 20
        finally:
            os.unlink(temp_path)
    
    def test_multiple_cities_matched(self):
        """Test when multiple cities match the search"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("location,date,category,description\n")
            f.write("Portland, OR,2026-01-01,Use of Force,Test1\n")
            f.write("Portland, ME,2026-01-02,Arrest/Detention,Test2\n")
            temp_path = f.name
        
        try:
            result = get_risk_for_city("Portland", csv_path=temp_path)
            
            assert 'matched_cities' in result
            assert len(result['matched_cities']) == 2
            assert 'Portland, OR' in result['matched_cities']
            assert 'Portland, ME' in result['matched_cities']
        finally:
            os.unlink(temp_path)
