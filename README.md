# Protest Safety Checker

ICE incident tracker and risk assessment tool using verified data from the House Oversight Democrats Immigration Enforcement Dashboard.

## What It Does

- **Scrapes 462+ verified ICE incidents** from Congressional oversight data (Nov 2025 - Jan 2026)
- **Calculates city-specific risk scores** based on:
  - Use of force incidents
  - U.S. citizen targeting
  - Sensitive location operations (schools, hospitals, etc.)
- **CLI tool** for quick risk assessment

## Quick Start
```bash
# Check risk for your city
python3 protest_checker.py Portland
python3 protest_checker.py "Los Angeles"
python3 protest_checker.py Minneapolis
```

## Example Output
```
🔴 RISK LEVEL: High
   Risk Score: 90/100

📊 INCIDENT STATISTICS:
   Total incidents: 21
   Use of Force: 12 (57.1%)
   U.S. Citizens targeted: 8 (38.1%)
   Sensitive Locations: 4 (19.0%)

📰 RECENT INCIDENTS:
   1. [01/23/2026] Asylum seeker detained by ICE...
   2. [01/22/2026] Masked agents detain civil engineer...
```

## Installation
```bash
# Clone repo
git clone https://github.com/jacobarrio/protest-safety-checker.git
cd protest-safety-checker

# Install dependencies
pip install selenium pandas beautifulsoup4 --break-system-packages

# Install Chrome/Chromium
sudo apt install chromium-browser chromium-chromedriver
```

## Data Source

**House Oversight Democrats Immigration Enforcement Dashboard**
- Official Congressional oversight data
- 462+ verified incidents from reputable news sources
- Covers Nov 2025 - Jan 2026
- Categories: Use of Force, Arrest/Detention, U.S. Citizen, Sensitive Locations, Deportation

## Files

- `scrape_oversight_selenium.py` - Scraper (gets latest data)
- `calculator.py` - Risk scoring algorithm
- `protest_checker.py` - CLI interface
- `protest_data_oversight.csv` - Current dataset

## Update Data
```bash
python3 scrape_oversight_selenium.py
```

Scrapes latest incidents from dashboard (~1-2 minutes).

## Testing

Comprehensive test suite included to ensure reliability.

### Run Tests
```bash
# Install testing dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=calculator --cov=app --cov-report=html

# Run specific test file
pytest tests/test_calculator.py

# Run specific test class
pytest tests/test_calculator.py::TestNormalizeCityInput

# Run with verbose output
pytest tests/ -v
```

### Test Coverage
The test suite includes:
- **Unit tests** for all calculator functions (normalize, find, score, etc.)
- **Edge cases**: empty strings, unicode, special characters, None values
- **Integration tests** for Flask routes and API endpoints
- **Mock data tests** to avoid dependency on real CSV files

### Continuous Integration
Tests run automatically on GitHub Actions for all pull requests.

## Built By

Jacob - Self-taught ML/RL engineer building resistance tech tools.

## License

Public domain. Use this to protect people.
