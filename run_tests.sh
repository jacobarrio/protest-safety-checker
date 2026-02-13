#!/bin/bash
# Test runner script for Protest Safety Checker

echo "🧪 Protest Safety Checker - Test Suite Runner"
echo "=============================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing dependencies..."
    pip install -r requirements-dev.txt --break-system-packages
fi

# Parse command line arguments
case "$1" in
    "quick")
        echo "🏃 Running quick test (no coverage)..."
        pytest tests/ -v
        ;;
    "coverage")
        echo "📊 Running tests with coverage report..."
        pytest tests/ --cov=calculator --cov=app --cov-report=term-missing --cov-report=html
        echo ""
        echo "✅ Coverage report generated: htmlcov/index.html"
        ;;
    "unit")
        echo "🔬 Running unit tests only (calculator.py)..."
        pytest tests/test_calculator.py -v
        ;;
    "integration")
        echo "🔗 Running integration tests only (app.py)..."
        pytest tests/test_app.py -v
        ;;
    "failed")
        echo "🔍 Re-running previously failed tests..."
        pytest tests/ --lf -v
        ;;
    "verbose")
        echo "📝 Running tests with maximum verbosity..."
        pytest tests/ -vv -s
        ;;
    "clean")
        echo "🧹 Running tests without real data..."
        if [ -f protest_data_oversight.csv ]; then
            mv protest_data_oversight.csv protest_data_oversight.csv.temp
            pytest tests/ -v
            mv protest_data_oversight.csv.temp protest_data_oversight.csv
        else
            pytest tests/ -v
        fi
        ;;
    *)
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  quick       - Run all tests without coverage"
        echo "  coverage    - Run tests with coverage report (HTML + terminal)"
        echo "  unit        - Run only unit tests (calculator.py)"
        echo "  integration - Run only integration tests (app.py)"
        echo "  failed      - Re-run only previously failed tests"
        echo "  verbose     - Run tests with maximum verbosity"
        echo "  clean       - Run tests without real data file"
        echo ""
        echo "Default (no option): Run all tests with standard output"
        pytest tests/ -v
        ;;
esac

echo ""
echo "✨ Done!"
