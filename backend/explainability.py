"""Model explainability dashboard using SHAP and advanced interpretability techniques."""

import shap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
import json
import base64
from io import BytesIO
import structlog
from dataclasses import dataclass, asdict
from datetime import datetime
import joblib
from sklearn.base import BaseEstimator

logger = structlog.get_logger()

@dataclass
class ExplanationResult:
    """Container for model explanation results."""
    prediction: str
    confidence: float
    shap_values: Dict[str, float]
    feature_importance: Dict[str, float]
    local_explanation: Dict[str, Any]
    global_explanation: Dict[str, Any]
    counterfactual: Optional[Dict[str, Any]]
    timestamp: datetime

class ModelExplainer:
    """Advanced model explainability with SHAP and interpretability techniques."""
    
    def __init__(self):
        self.explainers = {}
        self.feature_names = []
        self.models = {}
        self.explanation_cache = {}
        
    def initialize_explainer(self, model: BaseEstimator, X_train: pd.DataFrame, model_name: str = "default"):
        """Initialize SHAP explainer for a given model."""
        logger.info("Initializing SHAP explainer", model_name=model_name)
        
        self.models[model_name] = model
        self.feature_names = list(X_train.columns)
        
        # Choose appropriate explainer based on model type
        model_type = type(model).__name__.lower()
        
        try:
            if 'tree' in model_type or 'forest' in model_type or 'gradient' in model_type:
                # Tree-based models
                self.explainers[model_name] = shap.TreeExplainer(model)
                logger.info("Using TreeExplainer", model_name=model_name)
                
            elif 'linear' in model_type or 'logistic' in model_type:
                # Linear models
                self.explainers[model_name] = shap.LinearExplainer(model, X_train)
                logger.info("Using LinearExplainer", model_name=model_name)
                
            else:
                # General model explainer (slower but works for any model)
                self.explainers[model_name] = shap.Explainer(model, X_train)
                logger.info("Using general Explainer", model_name=model_name)
                
        except Exception as e:
            logger.error("Failed to initialize SHAP explainer", error=str(e), model_name=model_name)
            # Fallback to permutation explainer
            self.explainers[model_name] = shap.Explainer(model.predict, X_train)
    
    def explain_prediction(
        self, 
        X: pd.DataFrame, 
        model_name: str = "default",
        include_counterfactual: bool = True
    ) -> ExplanationResult:
        """Generate comprehensive explanation for a single prediction."""
        
        if model_name not in self.explainers:
            raise ValueError(f"No explainer found for model: {model_name}")
        
        model = self.models[model_name]
        explainer = self.explainers[model_name]
        
        # Make prediction
        if hasattr(model, 'predict_proba'):
            prediction_proba = model.predict_proba(X)[0]
            prediction = model.classes_[np.argmax(prediction_proba)]
            confidence = np.max(prediction_proba)
        else:
            prediction = model.predict(X)[0]
            confidence = 0.8  # Default confidence for non-probabilistic models
        
        # Calculate SHAP values
        try:
            shap_values = explainer.shap_values(X)
            
            # Handle different SHAP value formats
            if isinstance(shap_values, list):
                # Multi-class case - use values for predicted class
                if hasattr(model, 'classes_'):
                    class_idx = np.where(model.classes_ == prediction)[0][0]
                    shap_vals = shap_values[class_idx][0]
                else:
                    shap_vals = shap_values[0][0]
            else:
                # Binary or regression case
                if len(shap_values.shape) > 1:
                    shap_vals = shap_values[0]
                else:
                    shap_vals = shap_values
            
        except Exception as e:
            logger.error("Failed to calculate SHAP values", error=str(e))
            shap_vals = np.zeros(len(self.feature_names))
        
        # Create feature importance dictionary
        shap_dict = dict(zip(self.feature_names, shap_vals))
        
        # Calculate global feature importance
        feature_importance = self._calculate_feature_importance(model, X)
        
        # Generate local explanation
        local_explanation = self._generate_local_explanation(X, shap_dict, prediction)
        
        # Generate global explanation
        global_explanation = self._generate_global_explanation(model_name)
        
        # Generate counterfactual explanation
        counterfactual = None
        if include_counterfactual:
            counterfactual = self._generate_counterfactual(X, model, prediction)
        
        return ExplanationResult(
            prediction=str(prediction),
            confidence=float(confidence),
            shap_values=shap_dict,
            feature_importance=feature_importance,
            local_explanation=local_explanation,
            global_explanation=global_explanation,
            counterfactual=counterfactual,
            timestamp=datetime.now()
        )
    
    def _calculate_feature_importance(self, model: BaseEstimator, X: pd.DataFrame) -> Dict[str, float]:
        """Calculate feature importance using various methods."""
        
        importance_dict = {}
        
        # Try to get built-in feature importance
        if hasattr(model, 'feature_importances_'):
            importance_dict = dict(zip(self.feature_names, model.feature_importances_))
        elif hasattr(model, 'coef_'):
            # For linear models, use absolute coefficients
            coef = model.coef_
            if len(coef.shape) > 1:
                coef = coef[0]  # Take first class for multi-class
            importance_dict = dict(zip(self.feature_names, np.abs(coef)))
        else:
            # Use permutation importance as fallback
            try:
                from sklearn.inspection import permutation_importance
                perm_importance = permutation_importance(model, X, model.predict(X), n_repeats=5)
                importance_dict = dict(zip(self.feature_names, perm_importance.importances_mean))
            except:
                # Default to equal importance
                importance_dict = {name: 1.0/len(self.feature_names) for name in self.feature_names}
        
        # Normalize to sum to 1
        total_importance = sum(importance_dict.values())
        if total_importance > 0:
            importance_dict = {k: v/total_importance for k, v in importance_dict.items()}
        
        return importance_dict
    
    def _generate_local_explanation(
        self, 
        X: pd.DataFrame, 
        shap_values: Dict[str, float], 
        prediction: str
    ) -> Dict[str, Any]:
        """Generate human-readable local explanation."""
        
        # Sort features by absolute SHAP value
        sorted_features = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Get top positive and negative contributors
        positive_contributors = [(k, v) for k, v in sorted_features if v > 0][:5]
        negative_contributors = [(k, v) for k, v in sorted_features if v < 0][:5]
        
        # Generate explanation text
        explanation_text = f"The model predicts: {prediction}\\n\\n"
        
        if positive_contributors:
            explanation_text += "Top factors supporting this prediction:\\n"
            for feature, value in positive_contributors:
                feature_value = X[feature].iloc[0] if feature in X.columns else "N/A"
                explanation_text += f"• {self._format_feature_name(feature)}: {feature_value} (impact: +{value:.3f})\\n"
        
        if negative_contributors:
            explanation_text += "\\nTop factors opposing this prediction:\\n"
            for feature, value in negative_contributors:
                feature_value = X[feature].iloc[0] if feature in X.columns else "N/A"
                explanation_text += f"• {self._format_feature_name(feature)}: {feature_value} (impact: {value:.3f})\\n"
        
        return {
            'explanation_text': explanation_text,
            'top_positive': positive_contributors,
            'top_negative': negative_contributors,
            'feature_values': X.iloc[0].to_dict() if len(X) > 0 else {}
        }
    
    def _generate_global_explanation(self, model_name: str) -> Dict[str, Any]:
        """Generate global model explanation."""
        
        if model_name not in self.models:
            return {}
        
        model = self.models[model_name]
        
        # Model metadata
        model_info = {
            'model_type': type(model).__name__,
            'model_name': model_name,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names
        }
        
        # Add model-specific information
        if hasattr(model, 'n_estimators'):
            model_info['n_estimators'] = model.n_estimators
        if hasattr(model, 'max_depth'):
            model_info['max_depth'] = model.max_depth
        if hasattr(model, 'learning_rate'):
            model_info['learning_rate'] = model.learning_rate
        
        return {
            'model_info': model_info,
            'interpretation_notes': self._get_model_interpretation_notes(model)
        }
    
    def _get_model_interpretation_notes(self, model: BaseEstimator) -> List[str]:
        """Get model-specific interpretation notes."""
        
        model_type = type(model).__name__.lower()
        notes = []
        
        if 'randomforest' in model_type:
            notes.extend([
                "Random Forest combines multiple decision trees for robust predictions",
                "Feature importance shows average contribution across all trees",
                "Higher feature importance indicates stronger predictive power"
            ])
        elif 'gradientboosting' in model_type:
            notes.extend([
                "Gradient Boosting builds trees sequentially to correct previous errors",
                "Feature importance reflects cumulative contribution across iterations",
                "Model focuses on difficult-to-predict cases"
            ])
        elif 'logistic' in model_type:
            notes.extend([
                "Logistic Regression uses linear combinations of features",
                "Positive coefficients increase probability of positive class",
                "Feature importance based on absolute coefficient values"
            ])
        else:
            notes.append("Model predictions based on learned patterns in training data")
        
        return notes
    
    def _generate_counterfactual(
        self, 
        X: pd.DataFrame, 
        model: BaseEstimator, 
        current_prediction: str
    ) -> Optional[Dict[str, Any]]:
        """Generate counterfactual explanation (what would change the prediction)."""
        
        try:
            # Simple counterfactual generation
            # In production, use libraries like DiCE or Alibi
            
            original_features = X.iloc[0].copy()
            counterfactuals = []
            
            # Try modifying top features
            if hasattr(model, 'feature_importances_'):
                important_features = np.argsort(model.feature_importances_)[-5:]
            else:
                important_features = range(min(5, len(X.columns)))
            
            for feature_idx in important_features:
                feature_name = X.columns[feature_idx]
                original_value = original_features[feature_name]
                
                # Try different modifications
                modifications = []
                if isinstance(original_value, (int, float)):
                    modifications = [
                        original_value * 1.2,
                        original_value * 0.8,
                        original_value + 1,
                        original_value - 1
                    ]
                
                for mod_value in modifications:
                    modified_features = original_features.copy()
                    modified_features[feature_name] = mod_value
                    
                    # Make prediction with modified features
                    modified_X = pd.DataFrame([modified_features])
                    new_prediction = model.predict(modified_X)[0]
                    
                    if str(new_prediction) != current_prediction:
                        counterfactuals.append({
                            'feature': feature_name,
                            'original_value': original_value,
                            'modified_value': mod_value,
                            'new_prediction': str(new_prediction),
                            'change_description': f"If {self._format_feature_name(feature_name)} was {mod_value:.2f} instead of {original_value:.2f}"
                        })
                        break  # Found one counterfactual for this feature
            
            return {
                'counterfactuals': counterfactuals[:3],  # Return top 3
                'explanation': "These changes would lead to different predictions"
            }
            
        except Exception as e:
            logger.error("Failed to generate counterfactual", error=str(e))
            return None
    
    def _format_feature_name(self, feature_name: str) -> str:
        """Format feature name for human readability."""
        
        # Replace underscores with spaces and capitalize
        formatted = feature_name.replace('_', ' ').title()
        
        # Handle common abbreviations
        replacements = {
            'H2h': 'Head-to-Head',
            'Avg': 'Average',
            'Diff': 'Difference',
            'Ppg': 'Points Per Game',
            'Gpg': 'Goals Per Game'
        }
        
        for old, new in replacements.items():
            formatted = formatted.replace(old, new)
        
        return formatted


# Global explainer instance
model_explainer = ModelExplainer()
