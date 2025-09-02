"""Simplified FastAPI backend for Render deployment - no heavy dependencies."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Using built-in typing instead of pydantic to avoid compilation
from typing import List, Dict, Any
import numpy as np
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Premier League Predictor API",
    version="1.0.0",
    description="Lightweight Premier League match prediction API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple data structures (no pydantic to avoid compilation)
class PredictionRequest:
    def __init__(self, home_team: str, away_team: str):
        self.home_team = home_team
        self.away_team = away_team

class PredictionResponse:
    def __init__(self, home_team: str, away_team: str, home_win_prob: float, 
                 draw_prob: float, away_win_prob: float, predicted_outcome: str, confidence: float):
        self.home_team = home_team
        self.away_team = away_team
        self.home_win_prob = home_win_prob
        self.draw_prob = draw_prob
        self.away_win_prob = away_win_prob
        self.predicted_outcome = predicted_outcome
        self.confidence = confidence

# Load simple predictor
try:
    import sys
    sys.path.append('..')
    from pl_predictor import EnhancedPLPredictor
    predictor = EnhancedPLPredictor()
    logger.info("Predictor loaded successfully")
except Exception as e:
    logger.error(f"Failed to load predictor: {e}")
    predictor = None

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Premier League Predictor API",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "predictor_loaded": predictor is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/teams")
async def get_teams():
    """Get list of Premier League teams."""
    teams = [
        "Arsenal", "Aston Villa", "Brighton", "Burnley", "Chelsea",
        "Crystal Palace", "Everton", "Fulham", "Liverpool", "Luton Town",
        "Manchester City", "Manchester United", "Newcastle United", "Nottingham Forest",
        "Sheffield United", "Tottenham", "West Ham", "Wolves", "Bournemouth", "Brentford"
    ]
    return {"teams": teams}

@app.post("/predict")
async def predict_match(request: Dict[str, str]):
    """Predict Premier League match outcome."""
    try:
        if not predictor:
            raise HTTPException(status_code=503, detail="Predictor not available")
        
        # Simple prediction logic
        home_team = request.get("home_team")
        away_team = request.get("away_team")
        
        if not home_team or not away_team:
            raise HTTPException(status_code=400, detail="Missing home_team or away_team")
        
        # Mock prediction for deployment (replace with actual logic)
        home_prob = np.random.uniform(0.2, 0.6)
        draw_prob = np.random.uniform(0.2, 0.4)
        away_prob = 1.0 - home_prob - draw_prob
        
        # Determine predicted outcome
        probs = [home_prob, draw_prob, away_prob]
        outcomes = ["home_win", "draw", "away_win"]
        predicted_outcome = outcomes[np.argmax(probs)]
        confidence = max(probs)
        
        logger.info(f"Prediction: {home_team} vs {away_team} -> {predicted_outcome}")
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": round(home_prob, 3),
            "draw_prob": round(draw_prob, 3),
            "away_win_prob": round(away_prob, 3),
            "predicted_outcome": predicted_outcome,
            "confidence": round(confidence, 3)
        }
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
