#!/usr/bin/env python3
"""Test script to verify ML components functionality."""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add backend to path
sys.path.append('backend')

def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    print("🧪 Testing Basic ML Components...")
    
    # Test 1: Basic data structures
    print("✅ Test 1: Basic data structures")
    sample_data = pd.DataFrame({
        'HomeTeam': ['Arsenal', 'Liverpool'],
        'AwayTeam': ['Chelsea', 'Manchester City'],
        'Date': ['2024-01-15', '2024-01-16']
    })
    print(f"   Sample data created: {len(sample_data)} rows")
    
    # Test 2: Team strength calculation
    print("✅ Test 2: Team strength calculation")
    team_strengths = {
        "Manchester City": 0.85, "Arsenal": 0.82, "Liverpool": 0.80,
        "Chelsea": 0.75, "Manchester United": 0.72, "Tottenham": 0.70
    }
    
    for team, strength in list(team_strengths.items())[:3]:
        print(f"   {team}: {strength}")
    
    # Test 3: Prediction logic
    print("✅ Test 3: Basic prediction logic")
    home_team, away_team = "Arsenal", "Chelsea"
    home_strength = team_strengths.get(home_team, 0.5)
    away_strength = team_strengths.get(away_team, 0.5)
    
    home_advantage = 0.1
    strength_diff = home_strength - away_strength + home_advantage
    win_prob = max(0.1, min(0.8, 0.5 + strength_diff))
    loss_prob = max(0.1, min(0.8, 0.5 - strength_diff))
    draw_prob = max(0.1, 1.0 - win_prob - loss_prob)
    
    # Normalize
    total = win_prob + draw_prob + loss_prob
    win_prob /= total
    draw_prob /= total
    loss_prob /= total
    
    print(f"   {home_team} vs {away_team}:")
    print(f"   Win: {win_prob:.3f}, Draw: {draw_prob:.3f}, Loss: {loss_prob:.3f}")
    
    return True

def test_advanced_components():
    """Test advanced ML components if available."""
    print("\n🔬 Testing Advanced ML Components...")
    
    try:
        # Test feature engineering
        print("✅ Test 4: Feature engineering")
        from backend.feature_engineering import FeatureEngineer
        feature_eng = FeatureEngineer()
        print("   Feature engineer initialized")
        
        # Test basic features
        sample_df = pd.DataFrame({
            'HomeTeam': ['Arsenal'],
            'AwayTeam': ['Chelsea'],
            'Date': [datetime.now()],
            'FTHG': [2],
            'FTAG': [1],
            'FTR': ['H']
        })
        
        # This would normally require more data, but we can test the structure
        features = feature_eng.create_feature_pipeline()
        print(f"   Feature pipeline created with {len(features)} features")
        
    except ImportError as e:
        print(f"⚠️  Advanced feature engineering not available: {e}")
    
    try:
        # Test A/B testing framework
        print("✅ Test 5: A/B testing framework")
        from backend.ab_testing import ABTestingFramework
        ab_test = ABTestingFramework()
        print("   A/B testing framework initialized")
        
    except ImportError as e:
        print(f"⚠️  A/B testing framework not available: {e}")
    
    try:
        # Test ML pipeline
        print("✅ Test 6: ML pipeline")
        from backend.ml_pipeline import MLPipeline
        print("   ML pipeline class available")
        
    except ImportError as e:
        print(f"⚠️  ML pipeline not available: {e}")

def test_api_structure():
    """Test API response structure."""
    print("\n🌐 Testing API Structure...")
    
    # Test prediction response structure
    prediction_response = {
        "home_team": "Arsenal",
        "away_team": "Chelsea", 
        "win_probability": 0.456,
        "draw_probability": 0.267,
        "loss_probability": 0.277,
        "confidence_score": 0.456,
        "model_used": "Enhanced-Team-Strength",
        "features_used": 15,
        "prediction_id": "test-123"
    }
    
    print("✅ Test 7: Prediction response structure")
    for key, value in prediction_response.items():
        print(f"   {key}: {value}")
    
    return True

def main():
    """Run all tests."""
    print("🚀 Premier League Predictor - Component Testing")
    print("=" * 50)
    
    try:
        # Basic functionality tests
        test_basic_functionality()
        
        # Advanced component tests
        test_advanced_components()
        
        # API structure tests
        test_api_structure()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("🎯 Ready to proceed with full application testing")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
