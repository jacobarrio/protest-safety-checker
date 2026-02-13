"""
Pytest configuration and shared fixtures
"""

import pytest
import pandas as pd
import tempfile
import os


@pytest.fixture
def sample_protest_data():
    """Create sample protest data for testing"""
    return pd.DataFrame({
        'location': [
            'Portland, OR',
            'Portland, OR',
            'Phoenix, AZ',
            'Los Angeles, CA'
        ],
        'date': [
            '2026-01-01',
            '2026-01-02',
            '2026-01-01',
            '2026-01-03'
        ],
        'category': [
            'Use of Force',
            'Arrest/Detention',
            'U.S. Citizen',
            'Sensitive Location'
        ],
        'description': [
            'Test incident 1',
            'Test incident 2',
            'Test incident 3',
            'Test incident 4'
        ]
    })


@pytest.fixture
def temp_csv_file(sample_protest_data):
    """Create a temporary CSV file with sample data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_protest_data.to_csv(f, index=False)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def empty_csv_file():
    """Create an empty CSV file with headers"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("location,date,category,description\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)
