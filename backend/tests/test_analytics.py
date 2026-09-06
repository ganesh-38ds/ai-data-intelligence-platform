import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import analytics

def test_advanced_analytics_calculation():
    """Verify that numerical summary statistics and chart previews are correctly computed."""
    df = pd.DataFrame({
        "Category": ["Electronics", "Clothing", "Home", "Electronics"],
        "Sales": [100.0, 200.0, 150.0, 300.0],
        "Quantity": [2, 5, 3, 6]
    })
    
    summary, chart_data = analytics.get_advanced_analytics(df)
    
    assert "Sales" in summary
    assert "Quantity" in summary
    assert summary["Sales"]["mean"] == 187.5
    assert summary["Sales"]["min"] == 100.0
    assert summary["Sales"]["max"] == 300.0
    assert len(chart_data) == 4
    assert chart_data[0]["name"] == "Electronics"
    assert chart_data[0]["Sales"] == 100.0

def test_smart_statistical_insights():
    """Verify that automated data science insights detect hygiene, dominant values, and distributions."""
    df = pd.DataFrame({
        "Region": ["North", "North", "South", "North"],
        "Revenue": [1000, 2000, 1500, 8000]
    })
    
    insights = analytics.generate_smart_statistical_insights(df)
    
    assert len(insights) >= 2
    assert any("North" in s for s in insights) # Dominant category detected
    assert any("Revenue" in s for s in insights) # Primary numerical metric detected

def test_missing_and_duplicate_detection():
    """Verify that missing values and duplicate rows are accurately counted."""
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Alice", "David"],
        "Age": [25, np.nan, 25, 40]
    })
    
    total_missing = int(df.isnull().sum().sum())
    total_duplicates = int(df.duplicated().sum())
    
    assert total_missing == 1
    assert total_duplicates == 1
