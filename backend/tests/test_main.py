"""Unit tests for main API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestTeamsEndpoint:
    """Test teams endpoint."""
    
    @patch('main.get_teams')
    def test_get_teams_success(self, mock_get_teams):
        """Test successful teams retrieval."""
        mock_teams = ["Arsenal", "Chelsea", "Liverpool"]
        mock_get_teams.return_value = mock_teams
        
        response = client.get("/teams")
        assert response.status_code == 200
        assert response.json() == mock_teams
    
    @patch('main.get_teams')
    def test_get_teams_error(self, mock_get_teams):
        """Test teams endpoint error handling."""
        mock_get_teams.side_effect = Exception("Database error")
        
        response = client.get("/teams")
        assert response.status_code == 500


class TestPredictionEndpoint:
    """Test prediction endpoint."""
    
    @patch('main.make_prediction')
    def test_predict_success(self, mock_make_prediction):
        """Test successful prediction."""
        mock_prediction = {
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "home_win_prob": 0.45,
            "draw_prob": 0.25,
            "away_win_prob": 0.30,
            "confidence": 0.85
        }
        mock_make_prediction.return_value = mock_prediction
        
        response = client.post("/predict", json={
            "home_team": "Arsenal",
            "away_team": "Chelsea"
        })
        
        assert response.status_code == 200
        assert response.json() == mock_prediction
    
    def test_predict_missing_data(self):
        """Test prediction with missing data."""
        response = client.post("/predict", json={
            "home_team": "Arsenal"
            # Missing away_team
        })
        
        assert response.status_code == 422  # Validation error
    
    @patch('main.make_prediction')
    def test_predict_error(self, mock_make_prediction):
        """Test prediction endpoint error handling."""
        mock_make_prediction.side_effect = Exception("Model error")
        
        response = client.post("/predict", json={
            "home_team": "Arsenal",
            "away_team": "Chelsea"
        })
        
        assert response.status_code == 500


class TestMetricsEndpoint:
    """Test metrics endpoint."""
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint returns prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


@pytest.fixture
def mock_database():
    """Mock database session."""
    with patch('main.get_db') as mock_db:
        yield mock_db


@pytest.fixture
def mock_cache():
    """Mock cache manager."""
    with patch('main.cache_manager') as mock_cache:
        yield mock_cache
