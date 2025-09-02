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
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data


class TestTeamsEndpoint:
    """Test teams endpoint."""
    
    @patch('main.predictor')
    def test_get_teams_success(self, mock_predictor):
        """Test successful teams retrieval."""
        mock_df = Mock()
        mock_df.unique.return_value.tolist.return_value = ["Arsenal", "Chelsea", "Liverpool"]
        mock_predictor.matches = {"team": mock_df}
        
        response = client.get("/teams")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_teams_no_model(self):
        """Test teams endpoint when model not loaded."""
        with patch('main.predictor', None):
            response = client.get("/teams")
            assert response.status_code == 503


class TestPredictionEndpoint:
    """Test prediction endpoint."""
    
    @patch('main.predictor')
    def test_predict_success(self, mock_predictor):
        """Test successful prediction."""
        # Mock the predictor's matches DataFrame
        mock_df = Mock()
        mock_df.empty = False
        mock_df.tail.return_value = mock_df
        mock_df.__len__ = Mock(return_value=5)
        mock_df.__getitem__ = Mock(return_value=mock_df)
        mock_predictor.matches = mock_df
        
        response = client.post("/predict", json={
            "home_team": "Arsenal",
            "away_team": "Chelsea"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "home_team" in data
        assert "away_team" in data
        assert "win_probability" in data
    
    def test_predict_missing_data(self):
        """Test prediction with missing data."""
        response = client.post("/predict", json={
            "home_team": "Arsenal"
            # Missing away_team
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_predict_no_model(self):
        """Test prediction endpoint when model not loaded."""
        with patch('main.predictor', None):
            response = client.post("/predict", json={
                "home_team": "Arsenal",
                "away_team": "Chelsea"
            })
            assert response.status_code == 503


class TestMetricsEndpoint:
    """Test metrics endpoint."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns basic info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


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
