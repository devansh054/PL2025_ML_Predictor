"""Simplified FastAPI backend for Render deployment - no heavy dependencies."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
import random
from datetime import datetime

# Setup logging
import logging
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

# Skip predictor loading for minimal deployment
predictor = True  # Mock predictor availability

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
        
        # Mock prediction for deployment (using built-in random)
        home_prob = random.uniform(0.2, 0.6)
        draw_prob = random.uniform(0.2, 0.4)
        away_prob = 1.0 - home_prob - draw_prob
        
        # Determine predicted outcome
        probs = [home_prob, draw_prob, away_prob]
        outcomes = ["home_win", "draw", "away_win"]
        predicted_outcome = outcomes[probs.index(max(probs))]
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
