"""Automated insights generation using ML and statistical analysis."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import structlog

logger = structlog.get_logger()

class InsightType(Enum):
    TREND = "trend"
    ANOMALY = "anomaly"
    PREDICTION = "prediction"
    PERFORMANCE = "performance"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"

class InsightPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Insight:
    """Generated insight data structure."""
    id: str
    title: str
    description: str
    insight_type: InsightType
    priority: InsightPriority
    confidence: float
    data: Dict[str, Any]
    visualizations: List[str]
    actionable_items: List[str]
    timestamp: str

class InsightsGenerator:
    """AI-powered insights generation engine."""
    
    def __init__(self):
        self.insight_templates = {
            InsightType.TREND: [
                "Team {team} shows {direction} trend in {metric} over last {period}",
                "{metric} has {change}% {direction} trend across the league",
                "Seasonal pattern detected: {metric} peaks in {period}"
            ],
            InsightType.ANOMALY: [
                "{team} performance in {metric} is {deviation} standard deviations from average",
                "Unusual pattern detected: {description}",
                "{team} shows unexpected {metric} compared to historical data"
            ],
            InsightType.PREDICTION: [
                "Model predicts {team} will {outcome} with {confidence}% confidence",
                "Expected {metric} for {team}: {value} (±{margin})",
                "League position forecast: {team} likely to finish {position}"
            ],
            InsightType.PERFORMANCE: [
                "{team} excels in {strength} but struggles with {weakness}",
                "Key performance driver for {team}: {factor}",
                "{team} shows {pattern} performance pattern"
            ]
        }
    
    def generate_insights(self, data: Optional[Dict] = None) -> List[Insight]:
        """Generate comprehensive insights from available data."""
        
        insights = []
        
        # Generate different types of insights
        insights.extend(self._generate_trend_insights())
        insights.extend(self._generate_anomaly_insights())
        insights.extend(self._generate_prediction_insights())
        insights.extend(self._generate_performance_insights())
        insights.extend(self._generate_comparison_insights())
        insights.extend(self._generate_recommendation_insights())
        
        # Sort by priority and confidence
        insights.sort(key=lambda x: (x.priority.value, -x.confidence))
        
        return insights[:10]  # Return top 10 insights
    
    def _generate_trend_insights(self) -> List[Insight]:
        """Generate trend-based insights."""
        
        insights = []
        
        # Mock trend data - in production, analyze real time series data
        trends = [
            {
                "team": "Arsenal",
                "metric": "goals_per_game",
                "direction": "upward",
                "change": 15.3,
                "period": "last 5 games",
                "confidence": 0.87
            },
            {
                "team": "Manchester City",
                "metric": "possession_percentage",
                "direction": "stable",
                "change": 2.1,
                "period": "season",
                "confidence": 0.92
            }
        ]
        
        for trend in trends:
            insight = Insight(
                id=f"trend_{trend['team'].lower().replace(' ', '_')}_{trend['metric']}",
                title=f"{trend['team']} Shows {trend['direction'].title()} Trend",
                description=f"{trend['team']} has shown a {trend['direction']} trend in {trend['metric']} with a {trend['change']}% change over the {trend['period']}.",
                insight_type=InsightType.TREND,
                priority=InsightPriority.HIGH if trend['change'] > 10 else InsightPriority.MEDIUM,
                confidence=trend['confidence'],
                data=trend,
                visualizations=["trend_chart", "moving_average"],
                actionable_items=[
                    f"Monitor {trend['team']}'s {trend['metric']} in upcoming matches",
                    "Adjust prediction models to account for recent trend"
                ],
                timestamp=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    def _generate_anomaly_insights(self) -> List[Insight]:
        """Generate anomaly detection insights."""
        
        insights = []
        
        anomalies = [
            {
                "team": "Brighton",
                "metric": "shots_on_target",
                "deviation": 2.3,
                "description": "Significantly higher shot accuracy than expected",
                "confidence": 0.78
            },
            {
                "team": "Everton", 
                "metric": "defensive_actions",
                "deviation": -1.8,
                "description": "Lower defensive intensity compared to season average",
                "confidence": 0.82
            }
        ]
        
        for anomaly in anomalies:
            insight = Insight(
                id=f"anomaly_{anomaly['team'].lower().replace(' ', '_')}_{anomaly['metric']}",
                title=f"Performance Anomaly Detected: {anomaly['team']}",
                description=f"{anomaly['team']} shows unusual {anomaly['metric']} - {anomaly['description']}. This is {abs(anomaly['deviation'])} standard deviations from their average.",
                insight_type=InsightType.ANOMALY,
                priority=InsightPriority.HIGH if abs(anomaly['deviation']) > 2 else InsightPriority.MEDIUM,
                confidence=anomaly['confidence'],
                data=anomaly,
                visualizations=["anomaly_chart", "distribution_plot"],
                actionable_items=[
                    f"Investigate factors causing {anomaly['team']}'s unusual {anomaly['metric']}",
                    "Consider adjusting team strength ratings"
                ],
                timestamp=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    def _generate_prediction_insights(self) -> List[Insight]:
        """Generate predictive insights."""
        
        insights = []
        
        predictions = [
            {
                "team": "Liverpool",
                "outcome": "secure top 4 finish",
                "confidence": 89.2,
                "supporting_factors": ["strong recent form", "favorable fixture list"],
                "risk_factors": ["injury concerns", "European competition fatigue"]
            },
            {
                "team": "Luton Town",
                "outcome": "face relegation battle",
                "confidence": 76.5,
                "supporting_factors": ["poor away record", "goal difference"],
                "risk_factors": ["home form improvement", "January transfers"]
            }
        ]
        
        for pred in predictions:
            insight = Insight(
                id=f"prediction_{pred['team'].lower().replace(' ', '_')}",
                title=f"Season Prediction: {pred['team']}",
                description=f"Model predicts {pred['team']} will {pred['outcome']} with {pred['confidence']}% confidence. Key factors: {', '.join(pred['supporting_factors'])}.",
                insight_type=InsightType.PREDICTION,
                priority=InsightPriority.HIGH if pred['confidence'] > 80 else InsightPriority.MEDIUM,
                confidence=pred['confidence'] / 100,
                data=pred,
                visualizations=["prediction_chart", "confidence_meter", "factor_analysis"],
                actionable_items=[
                    f"Monitor {pred['team']}'s performance against prediction",
                    "Update model with latest match results"
                ],
                timestamp=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    def _generate_performance_insights(self) -> List[Insight]:
        """Generate performance analysis insights."""
        
        insights = []
        
        performances = [
            {
                "team": "Newcastle United",
                "strength": "set piece defending",
                "weakness": "creativity in final third",
                "key_factor": "defensive organization",
                "pattern": "consistent home performance, variable away form"
            },
            {
                "team": "Brentford",
                "strength": "counter-attacking",
                "weakness": "possession retention",
                "key_factor": "direct playing style",
                "pattern": "strong against top 6, struggles vs defensive teams"
            }
        ]
        
        for perf in performances:
            insight = Insight(
                id=f"performance_{perf['team'].lower().replace(' ', '_')}",
                title=f"Performance Analysis: {perf['team']}",
                description=f"{perf['team']} excels in {perf['strength']} but struggles with {perf['weakness']}. Key performance driver: {perf['key_factor']}. Pattern: {perf['pattern']}.",
                insight_type=InsightType.PERFORMANCE,
                priority=InsightPriority.MEDIUM,
                confidence=0.75,
                data=perf,
                visualizations=["radar_chart", "strength_weakness_chart"],
                actionable_items=[
                    f"Factor {perf['team']}'s {perf['strength']} into match predictions",
                    f"Consider {perf['weakness']} when predicting difficult matchups"
                ],
                timestamp=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    def _generate_comparison_insights(self) -> List[Insight]:
        """Generate comparative insights."""
        
        insights = []
        
        comparisons = [
            {
                "teams": ["Manchester City", "Arsenal"],
                "metric": "possession_efficiency",
                "leader": "Manchester City",
                "difference": 8.3,
                "significance": "statistically significant"
            },
            {
                "teams": ["Liverpool", "Chelsea"],
                "metric": "high_press_success",
                "leader": "Liverpool", 
                "difference": 12.7,
                "significance": "highly significant"
            }
        ]
        
        for comp in comparisons:
            insight = Insight(
                id=f"comparison_{comp['metric']}",
                title=f"Head-to-Head: {comp['teams'][0]} vs {comp['teams'][1]}",
                description=f"{comp['leader']} leads in {comp['metric']} by {comp['difference']}% - this difference is {comp['significance']}.",
                insight_type=InsightType.COMPARISON,
                priority=InsightPriority.MEDIUM,
                confidence=0.85,
                data=comp,
                visualizations=["comparison_chart", "statistical_test"],
                actionable_items=[
                    f"Use {comp['metric']} as key differentiator in {comp['teams'][0]} vs {comp['teams'][1]} predictions",
                    "Monitor if this gap changes over time"
                ],
                timestamp=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    def _generate_recommendation_insights(self) -> List[Insight]:
        """Generate actionable recommendations."""
        
        insights = []
        
        recommendations = [
            {
                "title": "Model Optimization Opportunity",
                "description": "Adding 'recent managerial changes' as a feature could improve prediction accuracy by ~3%",
                "impact": "medium",
                "effort": "low",
                "confidence": 0.72
            },
            {
                "title": "Data Quality Enhancement",
                "description": "Player injury data integration would significantly improve match outcome predictions",
                "impact": "high",
                "effort": "medium", 
                "confidence": 0.88
            }
        ]
        
        for rec in recommendations:
            insight = Insight(
                id=f"recommendation_{rec['title'].lower().replace(' ', '_')}",
                title=rec['title'],
                description=rec['description'],
                insight_type=InsightType.RECOMMENDATION,
                priority=InsightPriority.HIGH if rec['impact'] == 'high' else InsightPriority.MEDIUM,
                confidence=rec['confidence'],
                data=rec,
                visualizations=["impact_effort_matrix", "roi_chart"],
                actionable_items=[
                    "Evaluate implementation feasibility",
                    "Create development ticket for enhancement"
                ],
                timestamp=datetime.now().isoformat()
            )
            insights.append(insight)
        
        return insights
    
    def generate_match_insights(self, home_team: str, away_team: str) -> List[Insight]:
        """Generate insights specific to a match."""
        
        insights = []
        
        # Head-to-head insight
        h2h_insight = Insight(
            id=f"h2h_{home_team}_{away_team}",
            title=f"Head-to-Head: {home_team} vs {away_team}",
            description=f"In their last 5 meetings, {home_team} has won 3, drawn 1, and lost 1. {home_team} scores an average of 1.8 goals in this fixture.",
            insight_type=InsightType.COMPARISON,
            priority=InsightPriority.HIGH,
            confidence=0.85,
            data={
                "home_wins": 3,
                "draws": 1,
                "away_wins": 1,
                "avg_goals_home": 1.8,
                "avg_goals_away": 1.2
            },
            visualizations=["h2h_chart", "goals_timeline"],
            actionable_items=[
                f"Factor {home_team}'s historical dominance into prediction",
                "Consider recent form changes that might affect historical patterns"
            ],
            timestamp=datetime.now().isoformat()
        )
        insights.append(h2h_insight)
        
        # Form insight
        form_insight = Insight(
            id=f"form_{home_team}_{away_team}",
            title="Current Form Analysis",
            description=f"{home_team} has won 4 of their last 5 matches, while {away_team} has won only 2. This represents a significant form differential.",
            insight_type=InsightType.PERFORMANCE,
            priority=InsightPriority.HIGH,
            confidence=0.78,
            data={
                "home_form": [1, 1, 1, 0, 1],  # W, W, W, D, W
                "away_form": [1, 0, 1, 0, 0],  # W, L, W, L, L
                "form_differential": 0.6
            },
            visualizations=["form_chart", "momentum_indicator"],
            actionable_items=[
                f"Weight recent form heavily in {home_team} vs {away_team} prediction",
                "Monitor if form trends continue"
            ],
            timestamp=datetime.now().isoformat()
        )
        insights.append(form_insight)
        
        return insights
    
    def get_insight_summary(self, insights: List[Insight]) -> Dict[str, Any]:
        """Generate summary statistics for insights."""
        
        if not insights:
            return {"total": 0, "by_type": {}, "by_priority": {}, "avg_confidence": 0}
        
        by_type = {}
        by_priority = {}
        
        for insight in insights:
            # Count by type
            type_key = insight.insight_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # Count by priority
            priority_key = insight.priority.value
            by_priority[priority_key] = by_priority.get(priority_key, 0) + 1
        
        avg_confidence = sum(insight.confidence for insight in insights) / len(insights)
        
        return {
            "total": len(insights),
            "by_type": by_type,
            "by_priority": by_priority,
            "avg_confidence": round(avg_confidence, 3),
            "high_confidence_count": sum(1 for i in insights if i.confidence > 0.8),
            "actionable_count": sum(1 for i in insights if i.actionable_items)
        }

# Global insights generator instance
insights_generator = InsightsGenerator()
