"""Advanced ML pipeline with MLflow integration and model versioning."""

import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import mlflow
import mlflow.sklearn
import shap
import joblib
from datetime import datetime
import logging
from typing import Dict, Any, Tuple, List
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLPipeline:
    """Advanced ML pipeline with model versioning and explainability."""
    
    def __init__(self, experiment_name: str = "premier_league_predictor"):
        self.experiment_name = experiment_name
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []
        self.model_performance = {}
        
        # Initialize MLflow
        mlflow.set_experiment(experiment_name)
        
    def load_and_prepare_data(self, data_path: str) -> pd.DataFrame:
        """Load and prepare training data with advanced feature engineering."""
        logger.info("Loading and preparing data...")
        
        # Load data
        df = pd.read_csv(data_path)
        
        # Advanced feature engineering
        df = self._engineer_features(df)
        
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced feature engineering for football predictions."""
        logger.info("Engineering advanced features...")
        
        # Convert date column
        df['Date'] = pd.to_datetime(df['Date'])
        df['Season'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        
        # Team strength ratings (based on historical performance)
        team_stats = self._calculate_team_stats(df)
        df = df.merge(team_stats, left_on='HomeTeam', right_index=True, suffixes=('', '_home'))
        df = df.merge(team_stats, left_on='AwayTeam', right_index=True, suffixes=('', '_away'))
        
        # Recent form (last 5 games)
        df = self._add_recent_form(df)
        
        # Head-to-head statistics
        df = self._add_h2h_stats(df)
        
        # Home advantage metrics
        df['HomeAdvantage'] = 1  # Base home advantage
        
        # Goal difference features
        df['AvgGoalDiff_home'] = df['AvgGoalsFor_home'] - df['AvgGoalsAgainst_home']
        df['AvgGoalDiff_away'] = df['AvgGoalsFor_away'] - df['AvgGoalsAgainst_away']
        
        # Strength difference
        df['StrengthDiff'] = df['TeamStrength_home'] - df['TeamStrength_away']
        
        # Target variable (match result)
        df['Result'] = df.apply(self._get_match_result, axis=1)
        
        return df
    
    def _calculate_team_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate team statistics for strength ratings."""
        team_stats = {}
        
        for team in df['HomeTeam'].unique():
            home_games = df[df['HomeTeam'] == team]
            away_games = df[df['AwayTeam'] == team]
            
            # Goals statistics
            goals_for_home = home_games['FTHG'].mean()
            goals_against_home = home_games['FTAG'].mean()
            goals_for_away = away_games['FTAG'].mean()
            goals_against_away = away_games['FTHG'].mean()
            
            avg_goals_for = (goals_for_home + goals_for_away) / 2
            avg_goals_against = (goals_against_home + goals_against_away) / 2
            
            # Win percentage
            home_wins = len(home_games[home_games['FTR'] == 'H'])
            away_wins = len(away_games[away_games['FTR'] == 'A'])
            total_games = len(home_games) + len(away_games)
            win_percentage = (home_wins + away_wins) / total_games if total_games > 0 else 0
            
            # Team strength (composite metric)
            team_strength = (avg_goals_for * 0.4) + (win_percentage * 0.4) + ((3 - avg_goals_against) * 0.2)
            
            team_stats[team] = {
                'AvgGoalsFor': avg_goals_for,
                'AvgGoalsAgainst': avg_goals_against,
                'WinPercentage': win_percentage,
                'TeamStrength': team_strength
            }
        
        return pd.DataFrame(team_stats).T
    
    def _add_recent_form(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add recent form features (last 5 games)."""
        df = df.sort_values('Date').reset_index(drop=True)
        
        df['HomeForm'] = 0.0
        df['AwayForm'] = 0.0
        
        for idx, row in df.iterrows():
            if idx >= 5:  # Need at least 5 previous games
                home_team = row['HomeTeam']
                away_team = row['AwayTeam']
                current_date = row['Date']
                
                # Get last 5 games for home team
                home_recent = df[(df['Date'] < current_date) & 
                               ((df['HomeTeam'] == home_team) | (df['AwayTeam'] == home_team))].tail(5)
                
                # Get last 5 games for away team
                away_recent = df[(df['Date'] < current_date) & 
                               ((df['HomeTeam'] == away_team) | (df['AwayTeam'] == away_team))].tail(5)
                
                # Calculate form (3 points for win, 1 for draw, 0 for loss)
                home_form = self._calculate_team_form(home_recent, home_team)
                away_form = self._calculate_team_form(away_recent, away_team)
                
                df.at[idx, 'HomeForm'] = home_form
                df.at[idx, 'AwayForm'] = away_form
        
        return df
    
    def _calculate_team_form(self, recent_games: pd.DataFrame, team: str) -> float:
        """Calculate team form from recent games."""
        points = 0
        for _, game in recent_games.iterrows():
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
        
        return points / len(recent_games) if len(recent_games) > 0 else 0
    
    def _add_h2h_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add head-to-head statistics."""
        df['H2H_HomeWins'] = 0
        df['H2H_AwayWins'] = 0
        df['H2H_Draws'] = 0
        
        for idx, row in df.iterrows():
            home_team = row['HomeTeam']
            away_team = row['AwayTeam']
            current_date = row['Date']
            
            # Get historical matches between these teams
            h2h = df[(df['Date'] < current_date) & 
                    (((df['HomeTeam'] == home_team) & (df['AwayTeam'] == away_team)) |
                     ((df['HomeTeam'] == away_team) & (df['AwayTeam'] == home_team)))]
            
            if len(h2h) > 0:
                home_wins = len(h2h[((h2h['HomeTeam'] == home_team) & (h2h['FTR'] == 'H')) |
                                   ((h2h['AwayTeam'] == home_team) & (h2h['FTR'] == 'A'))])
                away_wins = len(h2h[((h2h['HomeTeam'] == away_team) & (h2h['FTR'] == 'H')) |
                                   ((h2h['AwayTeam'] == away_team) & (h2h['FTR'] == 'A'))])
                draws = len(h2h[h2h['FTR'] == 'D'])
                
                df.at[idx, 'H2H_HomeWins'] = home_wins
                df.at[idx, 'H2H_AwayWins'] = away_wins
                df.at[idx, 'H2H_Draws'] = draws
        
        return df
    
    def _get_match_result(self, row) -> str:
        """Get match result for target variable."""
        if row['FTHG'] > row['FTAG']:
            return 'H'  # Home win
        elif row['FTHG'] < row['FTAG']:
            return 'A'  # Away win
        else:
            return 'D'  # Draw
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for training."""
        feature_columns = [
            'TeamStrength_home', 'TeamStrength_away', 'AvgGoalsFor_home', 'AvgGoalsFor_away',
            'AvgGoalsAgainst_home', 'AvgGoalsAgainst_away', 'WinPercentage_home', 'WinPercentage_away',
            'HomeForm', 'AwayForm', 'H2H_HomeWins', 'H2H_AwayWins', 'H2H_Draws',
            'AvgGoalDiff_home', 'AvgGoalDiff_away', 'StrengthDiff', 'HomeAdvantage',
            'Month', 'DayOfWeek'
        ]
        
        # Filter available columns
        available_columns = [col for col in feature_columns if col in df.columns]
        self.feature_names = available_columns
        
        X = df[available_columns].fillna(0)
        y = df['Result']
        
        # Encode target variable
        if 'result_encoder' not in self.encoders:
            self.encoders['result_encoder'] = LabelEncoder()
            y_encoded = self.encoders['result_encoder'].fit_transform(y)
        else:
            y_encoded = self.encoders['result_encoder'].transform(y)
        
        # Scale features
        if 'feature_scaler' not in self.scalers:
            self.scalers['feature_scaler'] = StandardScaler()
            X_scaled = self.scalers['feature_scaler'].fit_transform(X)
        else:
            X_scaled = self.scalers['feature_scaler'].transform(X)
        
        return X_scaled, y_encoded
    
    def train_ensemble_models(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train ensemble of models with MLflow tracking."""
        logger.info("Training ensemble models...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Define models
        models_config = {
            'random_forest': RandomForestClassifier(
                n_estimators=200, max_depth=10, random_state=42, n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100, max_depth=6, random_state=42
            ),
            'logistic_regression': LogisticRegression(
                random_state=42, max_iter=1000
            )
        }
        
        results = {}
        
        for model_name, model in models_config.items():
            with mlflow.start_run(run_name=f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
                logger.info(f"Training {model_name}...")
                
                # Train model
                model.fit(X_train, y_train)
                
                # Predictions
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test)
                
                # Calculate metrics
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted')
                recall = recall_score(y_test, y_pred, average='weighted')
                f1 = f1_score(y_test, y_pred, average='weighted')
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_train, y_train, cv=5)
                cv_mean = cv_scores.mean()
                cv_std = cv_scores.std()
                
                # Log metrics
                mlflow.log_metric("accuracy", accuracy)
                mlflow.log_metric("precision", precision)
                mlflow.log_metric("recall", recall)
                mlflow.log_metric("f1_score", f1)
                mlflow.log_metric("cv_mean", cv_mean)
                mlflow.log_metric("cv_std", cv_std)
                
                # Log model
                mlflow.sklearn.log_model(model, f"model_{model_name}")
                
                # Save model locally
                model_path = f"models/{model_name}_model.joblib"
                os.makedirs("models", exist_ok=True)
                joblib.dump(model, model_path)
                
                # Store results
                results[model_name] = {
                    'model': model,
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'cv_mean': cv_mean,
                    'cv_std': cv_std,
                    'predictions': y_pred,
                    'probabilities': y_pred_proba
                }
                
                self.models[model_name] = model
                
                logger.info(f"{model_name} - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
        
        # Select best model
        best_model_name = max(results.keys(), key=lambda k: results[k]['accuracy'])
        self.best_model = self.models[best_model_name]
        self.best_model_name = best_model_name
        
        logger.info(f"Best model: {best_model_name} with accuracy: {results[best_model_name]['accuracy']:.4f}")
        
        return results
    
    def explain_model(self, X: np.ndarray, model_name: str = None) -> Dict[str, Any]:
        """Generate SHAP explanations for model interpretability."""
        if model_name is None:
            model_name = self.best_model_name
        
        model = self.models[model_name]
        
        logger.info(f"Generating SHAP explanations for {model_name}...")
        
        # Create SHAP explainer
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X[:100])  # Use subset for performance
        
        # Feature importance
        feature_importance = np.abs(shap_values).mean(axis=0)
        if len(feature_importance.shape) > 1:
            feature_importance = feature_importance.mean(axis=0)
        
        # Create feature importance dictionary
        importance_dict = dict(zip(self.feature_names, feature_importance))
        importance_dict = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        
        return {
            'explainer': explainer,
            'shap_values': shap_values,
            'feature_importance': importance_dict
        }
    
    def predict_match(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """Predict match outcome with confidence scores."""
        # This would need to be implemented with real-time data
        # For now, return mock prediction
        
        # In production, you would:
        # 1. Fetch current team stats
        # 2. Calculate features
        # 3. Use trained model to predict
        
        mock_features = np.array([[0.5, 0.4, 2.1, 1.8, 1.2, 1.5, 0.6, 0.4, 
                                 8.0, 6.0, 2, 1, 1, 0.9, 0.3, 0.1, 1, 3, 1]]).reshape(1, -1)
        
        if hasattr(self, 'best_model'):
            probabilities = self.best_model.predict_proba(mock_features)[0]
            prediction = self.best_model.predict(mock_features)[0]
            
            # Convert back to labels
            result_labels = self.encoders['result_encoder'].classes_
            
            return {
                'home_team': home_team,
                'away_team': away_team,
                'prediction': result_labels[prediction],
                'home_win_prob': float(probabilities[0]) if len(probabilities) > 0 else 0.33,
                'draw_prob': float(probabilities[1]) if len(probabilities) > 1 else 0.33,
                'away_win_prob': float(probabilities[2]) if len(probabilities) > 2 else 0.33,
                'confidence': float(max(probabilities)),
                'model_version': self.best_model_name
            }
        
        # Fallback prediction
        return {
            'home_team': home_team,
            'away_team': away_team,
            'prediction': 'H',
            'home_win_prob': 0.45,
            'draw_prob': 0.25,
            'away_win_prob': 0.30,
            'confidence': 0.85,
            'model_version': 'fallback'
        }


# Global ML pipeline instance
ml_pipeline = MLPipeline()
