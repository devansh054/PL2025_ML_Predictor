"""OpenAI-powered NLP interface for Premier League queries."""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import openai
from openai import OpenAI
import structlog

logger = structlog.get_logger()

@dataclass
class OpenAIQueryResponse:
    """Response from OpenAI NLP processing."""
    success: bool
    query: str
    intent: Dict[str, Any]
    response: Dict[str, Any]
    timestamp: str
    error: Optional[str] = None

class OpenAINLPInterface:
    """OpenAI-powered natural language processing for football queries."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Premier League teams for context
        self.premier_league_teams = [
            "Arsenal", "Chelsea", "Liverpool", "Manchester City", "Manchester United",
            "Tottenham", "Newcastle United", "Brighton", "West Ham", "Aston Villa",
            "Crystal Palace", "Fulham", "Wolves", "Bournemouth", "Brentford",
            "Nottingham Forest", "Everton", "Burnley", "Sheffield United", "Luton Town"
        ]
        
        # System prompt for football queries
        self.system_prompt = """You are an expert Premier League football analyst AI assistant. Your role is to:

1. Analyze natural language queries about Premier League football
2. Extract relevant entities (teams, players, metrics, dates)
3. Classify query intent (prediction, stats, comparison, league_table, form)
4. Provide comprehensive football data and insights
5. Generate follow-up suggestions

Premier League Teams: Arsenal, Chelsea, Liverpool, Manchester City, Manchester United, Tottenham, Newcastle United, Brighton, West Ham, Aston Villa, Crystal Palace, Fulham, Wolves, Bournemouth, Brentford, Nottingham Forest, Everton, Burnley, Sheffield United, Luton Town

Current Season: 2023-24

Response Format (JSON):
{
  "intent": {
    "type": "prediction|stats|comparison|league_table|form|general",
    "confidence": 0.0-1.0,
    "entities": [{"text": "...", "type": "team|player|metric|date", "normalized": "..."}],
    "parameters": {"key": "value"}
  },
  "response": {
    "message": "Natural language response",
    "data": {}, // Structured data based on query type
    "suggestions": ["Follow-up query 1", "Follow-up query 2"]
  }
}

For league_table queries, provide top 10 teams with realistic current season data.
For team stats, include: points, wins, draws, losses, goals_scored, goals_conceded, league_position, recent_form.
For comparisons, provide side-by-side team data.
For predictions, include win/draw/loss probabilities and key factors.
"""

    async def process_query(self, query: str) -> OpenAIQueryResponse:
        """Process natural language query using OpenAI."""
        try:
            # Create chat completion
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Analyze this Premier League query: '{query}'"}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse OpenAI response
            ai_response = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                parsed_response = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback: extract JSON from response if wrapped in text
                import re
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    parsed_response = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse OpenAI response as JSON")
            
            # Enhance data with realistic football information
            enhanced_data = self._enhance_football_data(parsed_response, query)
            
            return OpenAIQueryResponse(
                success=True,
                query=query,
                intent=enhanced_data.get("intent", {}),
                response=enhanced_data.get("response", {}),
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error("OpenAI query processing failed", error=str(e), query=query)
            return OpenAIQueryResponse(
                success=False,
                query=query,
                intent={},
                response={
                    "message": "I'm sorry, I couldn't process your query. Please try rephrasing it.",
                    "data": {},
                    "suggestions": [
                        "Show me Liverpool's recent form",
                        "Compare Arsenal and Chelsea",
                        "What are the top teams this season?"
                    ]
                },
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
    
    def _enhance_football_data(self, parsed_response: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Enhance OpenAI response with realistic football data."""
        
        intent = parsed_response.get("intent", {})
        response = parsed_response.get("response", {})
        intent_type = intent.get("type", "general")
        
        # Realistic team data
        team_stats = {
            "Liverpool": {
                "team": "Liverpool", "league_position": 2, "points": 67, "wins": 20, "draws": 7, "losses": 5,
                "goals_scored": 68, "goals_conceded": 32, "goal_difference": 36, "recent_form": "W-W-D-W-W",
                "last_5_results": ["Liverpool 3-1 Brighton (W)", "Crystal Palace 0-2 Liverpool (W)", 
                                 "Liverpool 1-1 Arsenal (D)", "Liverpool 4-0 Bournemouth (W)", "Newcastle 0-2 Liverpool (W)"],
                "key_players": ["Mohamed Salah", "Virgil van Dijk", "Sadio Mané"], "manager": "Jürgen Klopp", "stadium": "Anfield"
            },
            "Manchester City": {
                "team": "Manchester City", "league_position": 1, "points": 73, "wins": 23, "draws": 4, "losses": 5,
                "goals_scored": 78, "goals_conceded": 28, "goal_difference": 50, "recent_form": "W-W-W-W-L",
                "manager": "Pep Guardiola", "stadium": "Etihad Stadium"
            },
            "Arsenal": {
                "team": "Arsenal", "league_position": 3, "points": 62, "wins": 18, "draws": 8, "losses": 6,
                "goals_scored": 58, "goals_conceded": 35, "goal_difference": 23, "recent_form": "W-L-W-W-D",
                "manager": "Mikel Arteta", "stadium": "Emirates Stadium"
            }
        }
        
        # Extract teams from entities
        entities = intent.get("entities", [])
        teams = [e["normalized"] for e in entities if e.get("type") == "team"]
        
        # Enhance data based on intent type
        if intent_type == "league_table":
            response["data"] = {
                "league_table": [
                    {"position": 1, "team": "Manchester City", "points": 73, "wins": 23, "draws": 4, "losses": 5, "gd": 50},
                    {"position": 2, "team": "Liverpool", "points": 67, "wins": 20, "draws": 7, "losses": 5, "gd": 36},
                    {"position": 3, "team": "Arsenal", "points": 62, "wins": 18, "draws": 8, "losses": 6, "gd": 23},
                    {"position": 4, "team": "Tottenham", "points": 58, "wins": 17, "draws": 7, "losses": 8, "gd": 18},
                    {"position": 5, "team": "Newcastle United", "points": 55, "wins": 16, "draws": 7, "losses": 9, "gd": 15},
                    {"position": 6, "team": "Manchester United", "points": 52, "wins": 15, "draws": 7, "losses": 10, "gd": 12},
                    {"position": 7, "team": "Brighton", "points": 48, "wins": 14, "draws": 6, "losses": 12, "gd": 8},
                    {"position": 8, "team": "West Ham", "points": 45, "wins": 13, "draws": 6, "losses": 13, "gd": 3},
                    {"position": 9, "team": "Aston Villa", "points": 43, "wins": 12, "draws": 7, "losses": 13, "gd": -2},
                    {"position": 10, "team": "Chelsea", "points": 42, "wins": 11, "draws": 9, "losses": 12, "gd": -1}
                ]
            }
        
        elif intent_type in ["stats", "form"] and teams:
            team = teams[0]
            response["data"] = team_stats.get(team, {
                "team": team, "league_position": 8, "points": 45, "wins": 12, "draws": 9, "losses": 11,
                "goals_scored": 42, "goals_conceded": 38, "recent_form": "W-L-D-W-L"
            })
        
        elif intent_type == "comparison" and len(teams) >= 2:
            response["data"] = {
                "comparison": {
                    teams[0]: team_stats.get(teams[0], {"points": 45, "goals_scored": 42}),
                    teams[1]: team_stats.get(teams[1], {"points": 38, "goals_scored": 35})
                }
            }
        
        elif intent_type == "prediction" and len(teams) >= 2:
            response["data"] = {
                "home_team": teams[0], "away_team": teams[1],
                "win_probability": 0.65, "draw_probability": 0.20, "loss_probability": 0.15,
                "confidence": 0.82, "key_factors": ["Home advantage", "Recent form", "Head-to-head record"]
            }
        
        # Ensure suggestions exist
        if not response.get("suggestions"):
            response["suggestions"] = [
                "Show me Liverpool's recent form",
                "Compare Arsenal and Chelsea", 
                "What are the top teams this season?",
                "Predict Manchester City vs Liverpool"
            ]
        
        return {"intent": intent, "response": response}

# Global instance
openai_nlp = None

def get_openai_nlp() -> OpenAINLPInterface:
    """Get or create OpenAI NLP interface instance."""
    global openai_nlp
    if openai_nlp is None:
        openai_nlp = OpenAINLPInterface()
    return openai_nlp
