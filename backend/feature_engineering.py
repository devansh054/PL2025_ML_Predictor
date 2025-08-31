"""Advanced feature engineering pipeline with automated data updates."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
import structlog
from dataclasses import dataclass
import json
import os

logger = structlog.get_logger()

@dataclass
class TeamStats:
    """Team statistics for feature engineering."""
    team_name: str
    goals_for: float
    goals_against: float
    wins: int
    draws: int
    losses: int
    points: int
    form: List[str]  # Last 5 results
    home_record: Dict[str, int]
    away_record: Dict[str, int]
    last_updated: datetime

class FeatureEngineer:
    """Advanced feature engineering with real-time data integration."""
    
    def __init__(self):
        self.team_stats_cache = {}
        self.player_stats_cache = {}
        self.weather_cache = {}
        self.betting_odds_cache = {}
        
    async def fetch_real_time_data(self, season: str = "2023-24") -> Dict[str, Any]:
        """Fetch real-time football data from multiple sources."""
        logger.info("Fetching real-time football data", season=season)
        
        # In production, integrate with APIs like:
        # - Football-Data.org API
        # - RapidAPI Football
        # - ESPN API
        # - BBC Sport API
        
        # Mock implementation for demonstration
        return await self._mock_fetch_data(season)
    
    async def _mock_fetch_data(self, season: str) -> Dict[str, Any]:
        """Mock data fetching for demonstration."""
        teams = [
            "Arsenal", "Chelsea", "Liverpool", "Manchester City", "Manchester United",
            "Tottenham", "Newcastle United", "Brighton", "Aston Villa", "West Ham",
            "Crystal Palace", "Fulham", "Wolves", "Everton", "Brentford",
            "Nottingham Forest", "Luton Town", "Burnley", "Sheffield United", "Bournemouth"
        ]
        
        mock_data = {
            "teams": {},
            "fixtures": [],
            "player_stats": {},
            "injuries": {},
            "weather": {}
        }
        
        # Generate mock team stats
        for team in teams:
            mock_data["teams"][team] = {
                "goals_for": np.random.normal(1.8, 0.5),
                "goals_against": np.random.normal(1.3, 0.4),
                "wins": np.random.randint(8, 20),
                "draws": np.random.randint(3, 8),
                "losses": np.random.randint(5, 15),
                "form": np.random.choice(["W", "D", "L"], 5).tolist(),
                "home_wins": np.random.randint(4, 12),
                "away_wins": np.random.randint(2, 8),
                "clean_sheets": np.random.randint(3, 12),
                "yellow_cards": np.random.randint(30, 80),
                "red_cards": np.random.randint(1, 8)
            }
        
        return mock_data
    
    def engineer_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer basic statistical features."""
        logger.info("Engineering basic features")
        
        # Team strength metrics
        df = self._add_team_strength_features(df)
        
        # Recent form features
        df = self._add_form_features(df)
        
        # Head-to-head features
        df = self._add_h2h_features(df)
        
        # Temporal features
        df = self._add_temporal_features(df)
        
        # Goal-based features
        df = self._add_goal_features(df)
        
        return df
    
    def _add_team_strength_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add team strength-based features."""
        
        # Calculate team ratings based on historical performance
        team_ratings = {}
        
        for team in df['HomeTeam'].unique():
            home_games = df[df['HomeTeam'] == team]
            away_games = df[df['AwayTeam'] == team]
            
            # Points calculation
            home_points = (
                len(home_games[home_games['FTR'] == 'H']) * 3 +
                len(home_games[home_games['FTR'] == 'D']) * 1
            )
            away_points = (
                len(away_games[away_games['FTR'] == 'A']) * 3 +
                len(away_games[away_games['FTR'] == 'D']) * 1
            )
            
            total_games = len(home_games) + len(away_games)
            points_per_game = (home_points + away_points) / total_games if total_games > 0 else 0
            
            # Goal statistics
            goals_for = (home_games['FTHG'].sum() + away_games['FTAG'].sum()) / total_games if total_games > 0 else 0
            goals_against = (home_games['FTAG'].sum() + away_games['FTHG'].sum()) / total_games if total_games > 0 else 0
            
            team_ratings[team] = {
                'points_per_game': points_per_game,
                'goals_for_per_game': goals_for,
                'goals_against_per_game': goals_against,
                'goal_difference': goals_for - goals_against,
                'attack_strength': goals_for / 1.5 if goals_for > 0 else 0,  # Normalized
                'defense_strength': max(0, 2 - goals_against)  # Inverted and normalized
            }
        
        # Add features to dataframe
        for feature in ['points_per_game', 'goals_for_per_game', 'goals_against_per_game', 
                       'goal_difference', 'attack_strength', 'defense_strength']:
            df[f'home_{feature}'] = df['HomeTeam'].map(lambda x: team_ratings.get(x, {}).get(feature, 0))
            df[f'away_{feature}'] = df['AwayTeam'].map(lambda x: team_ratings.get(x, {}).get(feature, 0))
            df[f'{feature}_diff'] = df[f'home_{feature}'] - df[f'away_{feature}']
        
        return df
    
    def _add_form_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add recent form features."""
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Initialize form columns
        for window in [3, 5, 10]:
            df[f'home_form_{window}'] = 0.0
            df[f'away_form_{window}'] = 0.0
            df[f'home_goals_form_{window}'] = 0.0
            df[f'away_goals_form_{window}'] = 0.0
        
        for idx, row in df.iterrows():
            if idx < 10:  # Need minimum games for form calculation
                continue
                
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']
            current_date = row['Date']
            
            for window in [3, 5, 10]:
                # Home team form
                home_recent = df[
                    (df['Date'] < current_date) & 
                    ((df['HomeTeam'] == home_team) | (df['AwayTeam'] == home_team))
                ].tail(window)
                
                home_points = self._calculate_points_from_games(home_recent, home_team)
                home_goals = self._calculate_goals_from_games(home_recent, home_team)
                
                df.at[idx, f'home_form_{window}'] = home_points / (window * 3) if window > 0 else 0
                df.at[idx, f'home_goals_form_{window}'] = home_goals / window if window > 0 else 0
                
                # Away team form
                away_recent = df[
                    (df['Date'] < current_date) & 
                    ((df['HomeTeam'] == away_team) | (df['AwayTeam'] == away_team))
                ].tail(window)
                
                away_points = self._calculate_points_from_games(away_recent, away_team)
                away_goals = self._calculate_goals_from_games(away_recent, away_team)
                
                df.at[idx, f'away_form_{window}'] = away_points / (window * 3) if window > 0 else 0
                df.at[idx, f'away_goals_form_{window}'] = away_goals / window if window > 0 else 0
        
        return df
    
    def _calculate_points_from_games(self, games: pd.DataFrame, team: str) -> int:
        """Calculate points from recent games."""
        points = 0
        for _, game in games.iterrows():
            if game['HomeTeam'] == team:
                if game['FTR'] == 'H':
                    points += 3
                elif game['FTR'] == 'D':
                    points += 1
            else:  # Away team
                if game['FTR'] == 'A':
                    points += 3
                elif game['FTR'] == 'D':
                    points += 1
        return points
    
    def _calculate_goals_from_games(self, games: pd.DataFrame, team: str) -> float:
        """Calculate average goals from recent games."""
        goals = 0
        for _, game in games.iterrows():
            if game['HomeTeam'] == team:
                goals += game['FTHG']
            else:  # Away team
                goals += game['FTAG']
        return goals
    
    def _add_h2h_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add head-to-head historical features."""
        df['h2h_home_wins'] = 0
        df['h2h_away_wins'] = 0
        df['h2h_draws'] = 0
        df['h2h_total_games'] = 0
        df['h2h_avg_goals'] = 0.0
        df['h2h_home_advantage'] = 0.0
        
        for idx, row in df.iterrows():
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']
            current_date = row['Date']
            
            # Get historical H2H matches
            h2h_matches = df[
                (df['Date'] < current_date) & 
                (((df['HomeTeam'] == home_team) & (df['AwayTeam'] == away_team)) |
                 ((df['HomeTeam'] == away_team) & (df['AwayTeam'] == home_team)))
            ]
            
            if len(h2h_matches) > 0:
                # Count results
                home_wins = len(h2h_matches[
                    ((h2h_matches['HomeTeam'] == home_team) & (h2h_matches['FTR'] == 'H')) |
                    ((h2h_matches['AwayTeam'] == home_team) & (h2h_matches['FTR'] == 'A'))
                ])
                away_wins = len(h2h_matches[
                    ((h2h_matches['HomeTeam'] == away_team) & (h2h_matches['FTR'] == 'H')) |
                    ((h2h_matches['AwayTeam'] == away_team) & (h2h_matches['FTR'] == 'A'))
                ])
                draws = len(h2h_matches[h2h_matches['FTR'] == 'D'])
                
                # Calculate averages
                avg_goals = (h2h_matches['FTHG'] + h2h_matches['FTAG']).mean()
                
                # Home advantage in H2H
                home_h2h = h2h_matches[h2h_matches['HomeTeam'] == home_team]
                home_advantage = len(home_h2h[home_h2h['FTR'] == 'H']) / len(home_h2h) if len(home_h2h) > 0 else 0.5
                
                df.at[idx, 'h2h_home_wins'] = home_wins
                df.at[idx, 'h2h_away_wins'] = away_wins
                df.at[idx, 'h2h_draws'] = draws
                df.at[idx, 'h2h_total_games'] = len(h2h_matches)
                df.at[idx, 'h2h_avg_goals'] = avg_goals
                df.at[idx, 'h2h_home_advantage'] = home_advantage
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features."""
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Basic temporal features
        df['month'] = df['Date'].dt.month
        df['day_of_week'] = df['Date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['season_progress'] = (df['Date'].dt.dayofyear / 365.0)
        
        # Season phase (early, mid, late)
        df['season_phase'] = pd.cut(
            df['month'], 
            bins=[0, 10, 2, 5, 12], 
            labels=['early', 'mid', 'late', 'early'],
            include_lowest=True
        )
        
        # Holiday effects (simplified)
        df['is_holiday_period'] = df['month'].isin([12, 1]).astype(int)
        
        return df
    
    def _add_goal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add goal-related advanced features."""
        
        # Goal timing analysis (if available)
        # This would require more detailed data
        df['expected_goals_home'] = df['FTHG']  # Placeholder - would use xG data
        df['expected_goals_away'] = df['FTAG']  # Placeholder - would use xG data
        
        # Goal difference momentum
        df['goal_diff'] = df['FTHG'] - df['FTAG']
        
        # Over/Under features
        df['total_goals'] = df['FTHG'] + df['FTAG']
        df['over_2_5'] = (df['total_goals'] > 2.5).astype(int)
        df['over_3_5'] = (df['total_goals'] > 3.5).astype(int)
        
        # Both teams to score
        df['both_teams_scored'] = ((df['FTHG'] > 0) & (df['FTAG'] > 0)).astype(int)
        
        return df
    
    async def engineer_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer advanced features using external data."""
        logger.info("Engineering advanced features")
        
        # Fetch real-time data
        real_time_data = await self.fetch_real_time_data()
        
        # Add injury impact features
        df = await self._add_injury_features(df, real_time_data.get('injuries', {}))
        
        # Add weather impact features
        df = await self._add_weather_features(df, real_time_data.get('weather', {}))
        
        # Add betting odds features (market sentiment)
        df = await self._add_market_sentiment_features(df)
        
        # Add player performance features
        df = await self._add_player_features(df, real_time_data.get('player_stats', {}))
        
        return df
    
    async def _add_injury_features(self, df: pd.DataFrame, injury_data: Dict) -> pd.DataFrame:
        """Add injury impact features."""
        
        # Mock injury impact calculation
        df['home_injury_impact'] = np.random.uniform(0, 0.3, len(df))
        df['away_injury_impact'] = np.random.uniform(0, 0.3, len(df))
        df['injury_impact_diff'] = df['home_injury_impact'] - df['away_injury_impact']
        
        return df
    
    async def _add_weather_features(self, df: pd.DataFrame, weather_data: Dict) -> pd.DataFrame:
        """Add weather impact features."""
        
        # Mock weather features
        df['temperature'] = np.random.normal(15, 8, len(df))  # Celsius
        df['precipitation'] = np.random.exponential(2, len(df))  # mm
        df['wind_speed'] = np.random.exponential(10, len(df))  # km/h
        df['weather_impact'] = (
            (df['precipitation'] > 5).astype(int) * 0.1 +
            (df['wind_speed'] > 20).astype(int) * 0.05 +
            (df['temperature'] < 5).astype(int) * 0.05
        )
        
        return df
    
    async def _add_market_sentiment_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add betting market sentiment features."""
        
        # Mock betting odds (would integrate with betting APIs)
        df['home_odds'] = np.random.uniform(1.5, 4.0, len(df))
        df['draw_odds'] = np.random.uniform(3.0, 4.5, len(df))
        df['away_odds'] = np.random.uniform(1.5, 6.0, len(df))
        
        # Implied probabilities
        df['home_prob_market'] = 1 / df['home_odds']
        df['draw_prob_market'] = 1 / df['draw_odds']
        df['away_prob_market'] = 1 / df['away_odds']
        
        # Market efficiency (total probability should be > 1)
        df['market_margin'] = df['home_prob_market'] + df['draw_prob_market'] + df['away_prob_market'] - 1
        
        # Favorite indicator
        df['home_favorite'] = (df['home_odds'] < df['away_odds']).astype(int)
        df['odds_ratio'] = df['home_odds'] / df['away_odds']
        
        return df
    
    async def _add_player_features(self, df: pd.DataFrame, player_data: Dict) -> pd.DataFrame:
        """Add key player performance features."""
        
        # Mock player impact features
        df['home_key_player_form'] = np.random.uniform(0.6, 1.0, len(df))
        df['away_key_player_form'] = np.random.uniform(0.6, 1.0, len(df))
        df['player_quality_diff'] = df['home_key_player_form'] - df['away_key_player_form']
        
        # Squad depth
        df['home_squad_depth'] = np.random.uniform(0.7, 1.0, len(df))
        df['away_squad_depth'] = np.random.uniform(0.7, 1.0, len(df))
        
        return df
    
    def create_feature_pipeline(self) -> List[str]:
        """Create comprehensive feature pipeline."""
        
        feature_groups = {
            'basic_stats': [
                'home_points_per_game', 'away_points_per_game', 'points_per_game_diff',
                'home_goals_for_per_game', 'away_goals_for_per_game', 'goals_for_per_game_diff',
                'home_goals_against_per_game', 'away_goals_against_per_game', 'goals_against_per_game_diff',
                'home_goal_difference', 'away_goal_difference', 'goal_difference_diff',
                'home_attack_strength', 'away_attack_strength', 'attack_strength_diff',
                'home_defense_strength', 'away_defense_strength', 'defense_strength_diff'
            ],
            'form_features': [
                'home_form_3', 'away_form_3', 'home_form_5', 'away_form_5', 'home_form_10', 'away_form_10',
                'home_goals_form_3', 'away_goals_form_3', 'home_goals_form_5', 'away_goals_form_5'
            ],
            'h2h_features': [
                'h2h_home_wins', 'h2h_away_wins', 'h2h_draws', 'h2h_total_games',
                'h2h_avg_goals', 'h2h_home_advantage'
            ],
            'temporal_features': [
                'month', 'day_of_week', 'is_weekend', 'season_progress', 'is_holiday_period'
            ],
            'advanced_features': [
                'home_injury_impact', 'away_injury_impact', 'injury_impact_diff',
                'weather_impact', 'temperature', 'precipitation',
                'home_prob_market', 'away_prob_market', 'market_margin', 'odds_ratio',
                'home_key_player_form', 'away_key_player_form', 'player_quality_diff'
            ]
        }
        
        all_features = []
        for group_features in feature_groups.values():
            all_features.extend(group_features)
        
        return all_features


# Global feature engineer instance
feature_engineer = FeatureEngineer()
