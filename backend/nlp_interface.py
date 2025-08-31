"""Natural Language Processing interface for querying football data and predictions."""

import re
import spacy
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from enum import Enum
import structlog

logger = structlog.get_logger()

class QueryType(Enum):
    PREDICTION = "prediction"
    STATS = "stats"
    COMPARISON = "comparison"
    HISTORICAL = "historical"
    PERFORMANCE = "performance"
    SCHEDULE = "schedule"
    UNKNOWN = "unknown"

class EntityType(Enum):
    TEAM = "team"
    PLAYER = "player"
    DATE = "date"
    METRIC = "metric"
    SEASON = "season"

@dataclass
class Entity:
    """Named entity extracted from query."""
    text: str
    type: EntityType
    confidence: float
    normalized: str

@dataclass
class QueryIntent:
    """Parsed query intent and entities."""
    query_type: QueryType
    entities: List[Entity]
    confidence: float
    parameters: Dict[str, Any]
    sql_query: Optional[str] = None
    response_template: Optional[str] = None

class NLPInterface:
    """Natural language processing interface for football queries."""
    
    def __init__(self):
        # Initialize spaCy model (using small English model)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using basic NLP")
            self.nlp = None
        
        # Premier League teams mapping
        self.team_mappings = {
            # Full names
            "arsenal": "Arsenal",
            "chelsea": "Chelsea", 
            "liverpool": "Liverpool",
            "manchester city": "Manchester City",
            "manchester united": "Manchester United",
            "tottenham": "Tottenham",
            "newcastle": "Newcastle United",
            "brighton": "Brighton",
            "aston villa": "Aston Villa",
            "west ham": "West Ham",
            "crystal palace": "Crystal Palace",
            "fulham": "Fulham",
            "wolves": "Wolves",
            "everton": "Everton",
            "brentford": "Brentford",
            "nottingham forest": "Nottingham Forest",
            "luton town": "Luton Town",
            "burnley": "Burnley",
            "sheffield united": "Sheffield United",
            "bournemouth": "Bournemouth",
            
            # Common abbreviations and nicknames
            "city": "Manchester City",
            "united": "Manchester United",
            "spurs": "Tottenham",
            "gunners": "Arsenal",
            "blues": "Chelsea",
            "reds": "Liverpool",
            "hammers": "West Ham",
            "eagles": "Crystal Palace",
            "cottagers": "Fulham",
            "toffees": "Everton",
            "bees": "Brentford",
            "magpies": "Newcastle United",
            "seagulls": "Brighton",
            "villans": "Aston Villa",
            "cherries": "Bournemouth"
        }
        
        # Query patterns for intent classification
        self.query_patterns = {
            QueryType.PREDICTION: [
                r"predict|prediction|forecast|who will win|outcome|result",
                r"vs|against|play|match|game",
                r"chances|probability|likely|odds"
            ],
            QueryType.STATS: [
                r"stats|statistics|performance|record",
                r"goals|assists|clean sheets|wins|losses",
                r"how many|total|average|best|worst"
            ],
            QueryType.COMPARISON: [
                r"compare|comparison|versus|vs|better|worse",
                r"difference|similar|different",
                r"who is|which team"
            ],
            QueryType.HISTORICAL: [
                r"history|historical|past|previous|last season",
                r"all time|ever|since|before|after",
                r"when did|has.*ever"
            ],
            QueryType.PERFORMANCE: [
                r"form|recent|current|this season",
                r"performing|doing|playing",
                r"streak|run|trend"
            ],
            QueryType.SCHEDULE: [
                r"next|upcoming|fixture|schedule|when",
                r"play next|next game|next match",
                r"calendar|dates"
            ]
        }
        
        # Metric mappings
        self.metric_mappings = {
            "goals": "goals_scored",
            "goals scored": "goals_scored", 
            "goals for": "goals_scored",
            "goals against": "goals_conceded",
            "goals conceded": "goals_conceded",
            "clean sheets": "clean_sheets",
            "wins": "wins",
            "losses": "losses",
            "draws": "draws",
            "points": "points",
            "position": "league_position",
            "rank": "league_position",
            "form": "recent_form",
            "win rate": "win_percentage",
            "possession": "avg_possession",
            "shots": "shots_per_game",
            "accuracy": "pass_accuracy"
        }
    
    def parse_query(self, query: str) -> QueryIntent:
        """Parse natural language query into structured intent."""
        
        query_lower = query.lower().strip()
        
        # Extract entities
        entities = self._extract_entities(query_lower)
        
        # Classify query type
        query_type = self._classify_query_type(query_lower)
        
        # Extract parameters based on query type and entities
        parameters = self._extract_parameters(query_lower, entities, query_type)
        
        # Generate SQL query if applicable
        sql_query = self._generate_sql_query(query_type, parameters, entities)
        
        # Generate response template
        response_template = self._generate_response_template(query_type, parameters)
        
        confidence = self._calculate_confidence(query_type, entities, parameters)
        
        return QueryIntent(
            query_type=query_type,
            entities=entities,
            confidence=confidence,
            parameters=parameters,
            sql_query=sql_query,
            response_template=response_template
        )
    
    def _extract_entities(self, query: str) -> List[Entity]:
        """Extract named entities from query."""
        entities = []
        
        # Extract teams
        for team_key, team_name in self.team_mappings.items():
            if team_key in query:
                entities.append(Entity(
                    text=team_key,
                    type=EntityType.TEAM,
                    confidence=0.9,
                    normalized=team_name
                ))
        
        # Extract metrics
        for metric_key, metric_name in self.metric_mappings.items():
            if metric_key in query:
                entities.append(Entity(
                    text=metric_key,
                    type=EntityType.METRIC,
                    confidence=0.8,
                    normalized=metric_name
                ))
        
        # Extract dates using regex
        date_patterns = [
            r"today|tomorrow|yesterday",
            r"this week|next week|last week",
            r"this month|next month|last month", 
            r"this season|next season|last season",
            r"\d{1,2}/\d{1,2}/\d{4}",
            r"\d{4}-\d{2}-\d{2}"
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, query)
            for match in matches:
                entities.append(Entity(
                    text=match.group(),
                    type=EntityType.DATE,
                    confidence=0.7,
                    normalized=self._normalize_date(match.group())
                ))
        
        # Use spaCy for additional entity extraction if available
        if self.nlp:
            doc = self.nlp(query)
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "DATE", "TIME"]:
                    entity_type = self._map_spacy_label(ent.label_)
                    entities.append(Entity(
                        text=ent.text,
                        type=entity_type,
                        confidence=0.6,
                        normalized=ent.text
                    ))
        
        return entities
    
    def _classify_query_type(self, query: str) -> QueryType:
        """Classify the type of query based on patterns."""
        
        scores = {query_type: 0 for query_type in QueryType}
        
        for query_type, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    scores[query_type] += 1
        
        # Return the query type with highest score
        max_score = max(scores.values())
        if max_score > 0:
            for query_type, score in scores.items():
                if score == max_score:
                    return query_type
        
        return QueryType.UNKNOWN
    
    def _extract_parameters(self, query: str, entities: List[Entity], query_type: QueryType) -> Dict[str, Any]:
        """Extract parameters based on query type and entities."""
        
        parameters = {}
        
        # Extract teams
        teams = [e.normalized for e in entities if e.type == EntityType.TEAM]
        if teams:
            parameters["teams"] = teams
            if len(teams) >= 2:
                parameters["home_team"] = teams[0]
                parameters["away_team"] = teams[1]
            elif len(teams) == 1:
                parameters["team"] = teams[0]
        
        # Extract metrics
        metrics = [e.normalized for e in entities if e.type == EntityType.METRIC]
        if metrics:
            parameters["metrics"] = metrics
        
        # Extract dates
        dates = [e.normalized for e in entities if e.type == EntityType.DATE]
        if dates:
            parameters["dates"] = dates
        
        # Query-specific parameter extraction
        if query_type == QueryType.PREDICTION:
            # Look for prediction-specific keywords
            if "probability" in query or "chances" in query:
                parameters["include_probability"] = True
            if "confidence" in query:
                parameters["include_confidence"] = True
        
        elif query_type == QueryType.COMPARISON:
            # Ensure we have at least 2 teams for comparison
            if len(teams) < 2:
                parameters["comparison_type"] = "league_average"
            else:
                parameters["comparison_type"] = "head_to_head"
        
        elif query_type == QueryType.HISTORICAL:
            # Look for time period indicators
            if "all time" in query:
                parameters["time_period"] = "all_time"
            elif "season" in query:
                parameters["time_period"] = "season"
            else:
                parameters["time_period"] = "recent"
        
        return parameters
    
    def _generate_sql_query(self, query_type: QueryType, parameters: Dict[str, Any], entities: List[Entity]) -> Optional[str]:
        """Generate SQL query based on parsed intent."""
        
        if query_type == QueryType.STATS:
            team = parameters.get("team")
            metrics = parameters.get("metrics", ["goals_scored", "goals_conceded", "wins"])
            
            if team:
                return f"""
                SELECT {', '.join(metrics)}
                FROM team_stats 
                WHERE team_name = '{team}'
                AND season = '2023-24'
                """
        
        elif query_type == QueryType.COMPARISON:
            teams = parameters.get("teams", [])
            if len(teams) >= 2:
                return f"""
                SELECT team_name, goals_scored, goals_conceded, wins, losses, draws
                FROM team_stats
                WHERE team_name IN ({', '.join([f"'{team}'" for team in teams])})
                AND season = '2023-24'
                """
        
        elif query_type == QueryType.HISTORICAL:
            team = parameters.get("team")
            if team:
                return f"""
                SELECT season, wins, losses, draws, points, league_position
                FROM historical_stats
                WHERE team_name = '{team}'
                ORDER BY season DESC
                LIMIT 5
                """
        
        return None
    
    def _generate_response_template(self, query_type: QueryType, parameters: Dict[str, Any]) -> str:
        """Generate response template based on query type."""
        
        if query_type == QueryType.PREDICTION:
            teams = parameters.get("teams", [])
            if len(teams) >= 2:
                return f"Based on current form and statistics, here's the prediction for {teams[0]} vs {teams[1]}:"
            else:
                return "I need two teams to make a prediction. Please specify both teams."
        
        elif query_type == QueryType.STATS:
            team = parameters.get("team")
            if team:
                return f"Here are the current season statistics for {team}:"
            else:
                return "Here are the requested statistics:"
        
        elif query_type == QueryType.COMPARISON:
            teams = parameters.get("teams", [])
            if len(teams) >= 2:
                return f"Comparing {teams[0]} and {teams[1]}:"
            else:
                return "Here's how the team compares to the league average:"
        
        elif query_type == QueryType.HISTORICAL:
            team = parameters.get("team")
            if team:
                return f"Historical performance data for {team}:"
            else:
                return "Here's the historical data you requested:"
        
        elif query_type == QueryType.PERFORMANCE:
            team = parameters.get("team")
            if team:
                return f"Current form and performance analysis for {team}:"
            else:
                return "Here's the performance analysis:"
        
        elif query_type == QueryType.SCHEDULE:
            team = parameters.get("team")
            if team:
                return f"Upcoming fixtures for {team}:"
            else:
                return "Here's the fixture information:"
        
        else:
            return "I'm not sure how to help with that query. Could you please rephrase it?"
    
    def _calculate_confidence(self, query_type: QueryType, entities: List[Entity], parameters: Dict[str, Any]) -> float:
        """Calculate confidence score for the parsed query."""
        
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on query type classification
        if query_type != QueryType.UNKNOWN:
            confidence += 0.2
        
        # Boost confidence based on entity extraction
        team_entities = [e for e in entities if e.type == EntityType.TEAM]
        if team_entities:
            confidence += 0.2 * min(len(team_entities), 2)  # Max boost for 2 teams
        
        # Boost confidence based on parameters
        if parameters:
            confidence += 0.1 * min(len(parameters), 3)  # Max boost for 3 parameters
        
        return min(confidence, 1.0)
    
    def _normalize_date(self, date_text: str) -> str:
        """Normalize date text to standard format."""
        
        date_mappings = {
            "today": datetime.now().strftime("%Y-%m-%d"),
            "tomorrow": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "yesterday": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "this week": datetime.now().strftime("%Y-W%U"),
            "next week": (datetime.now() + timedelta(weeks=1)).strftime("%Y-W%U"),
            "last week": (datetime.now() - timedelta(weeks=1)).strftime("%Y-W%U"),
            "this season": "2023-24",
            "last season": "2022-23",
            "next season": "2024-25"
        }
        
        return date_mappings.get(date_text.lower(), date_text)
    
    def _map_spacy_label(self, spacy_label: str) -> EntityType:
        """Map spaCy entity labels to our entity types."""
        
        mapping = {
            "PERSON": EntityType.PLAYER,
            "ORG": EntityType.TEAM,
            "DATE": EntityType.DATE,
            "TIME": EntityType.DATE
        }
        
        return mapping.get(spacy_label, EntityType.TEAM)
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query and return structured response."""
        
        try:
            # Parse the query
            intent = self.parse_query(query)
            
            # Generate response based on intent
            response = self._generate_response(intent)
            
            return {
                "success": True,
                "query": query,
                "intent": {
                    "type": intent.query_type.value,
                    "confidence": intent.confidence,
                    "entities": [
                        {
                            "text": e.text,
                            "type": e.type.value,
                            "normalized": e.normalized,
                            "confidence": e.confidence
                        } for e in intent.entities
                    ],
                    "parameters": intent.parameters
                },
                "response": response,
                "sql_query": intent.sql_query,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Query processing error", error=str(e), query=query)
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "response": "I'm sorry, I couldn't understand your query. Please try rephrasing it.",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_response(self, intent: QueryIntent) -> Dict[str, Any]:
        """Generate response data based on parsed intent."""
        
        response = {
            "message": intent.response_template or "Here's what I found:",
            "data": {},
            "visualizations": [],
            "suggestions": []
        }
        
        # Generate mock data based on query type
        if intent.query_type == QueryType.PREDICTION:
            teams = intent.parameters.get("teams", [])
            if len(teams) >= 2:
                response["data"] = {
                    "home_team": teams[0],
                    "away_team": teams[1],
                    "win_probability": 0.65,
                    "draw_probability": 0.20,
                    "loss_probability": 0.15,
                    "confidence": 0.82
                }
                response["visualizations"] = ["probability_chart", "confidence_meter"]
        
        elif intent.query_type == QueryType.STATS:
            team = intent.parameters.get("team")
            if team:
                response["data"] = {
                    "team": team,
                    "goals_scored": 45,
                    "goals_conceded": 28,
                    "wins": 18,
                    "draws": 8,
                    "losses": 6,
                    "points": 62,
                    "league_position": 4
                }
                response["visualizations"] = ["stats_table", "performance_radar"]
        
        elif intent.query_type == QueryType.COMPARISON:
            teams = intent.parameters.get("teams", [])
            if len(teams) >= 2:
                response["data"] = {
                    "teams": teams,
                    "comparison": {
                        teams[0]: {"goals": 45, "wins": 18, "points": 62},
                        teams[1]: {"goals": 38, "wins": 15, "points": 54}
                    }
                }
                response["visualizations"] = ["comparison_chart", "head_to_head"]
        
        # Add suggestions for follow-up queries
        response["suggestions"] = self._generate_suggestions(intent)
        
        return response
    
    def _generate_suggestions(self, intent: QueryIntent) -> List[str]:
        """Generate follow-up query suggestions."""
        
        suggestions = []
        
        if intent.query_type == QueryType.PREDICTION:
            teams = intent.parameters.get("teams", [])
            if teams:
                suggestions.extend([
                    f"Show me {teams[0]}'s recent form",
                    f"Compare {teams[0]} and {teams[1]} head-to-head record",
                    "What factors influence this prediction?"
                ])
        
        elif intent.query_type == QueryType.STATS:
            team = intent.parameters.get("team")
            if team:
                suggestions.extend([
                    f"Compare {team} with league average",
                    f"Show {team}'s historical performance",
                    f"What are {team}'s upcoming fixtures?"
                ])
        
        # Add general suggestions
        suggestions.extend([
            "Show me the league table",
            "Which team has the best attack?",
            "Predict the next gameweek results"
        ])
        
        return suggestions[:5]  # Limit to 5 suggestions

# Global NLP interface instance
nlp_interface = NLPInterface()
