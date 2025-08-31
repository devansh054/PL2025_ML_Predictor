"""A/B testing framework for model comparison and experimentation."""

import os
import json
import random
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

@dataclass
class Experiment:
    """A/B test experiment configuration."""
    id: str
    name: str
    description: str
    model_a: str
    model_b: str
    traffic_split: float  # Percentage for model A (0.0 to 1.0)
    start_date: datetime
    end_date: datetime
    is_active: bool
    success_metric: str
    minimum_sample_size: int
    created_at: datetime

@dataclass
class ExperimentResult:
    """Result of an A/B test experiment."""
    experiment_id: str
    model_name: str
    total_predictions: int
    correct_predictions: int
    accuracy: float
    avg_confidence: float
    conversion_rate: float
    statistical_significance: float

class ABTestingFramework:
    """A/B testing framework for ML model comparison."""
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.results_cache = {}
        
    async def create_experiment(
        self,
        name: str,
        description: str,
        model_a: str,
        model_b: str,
        traffic_split: float = 0.5,
        duration_days: int = 30,
        success_metric: str = "accuracy",
        minimum_sample_size: int = 1000
    ) -> str:
        """Create a new A/B test experiment."""
        
        experiment_id = self._generate_experiment_id(name)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        experiment = Experiment(
            id=experiment_id,
            name=name,
            description=description,
            model_a=model_a,
            model_b=model_b,
            traffic_split=traffic_split,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            success_metric=success_metric,
            minimum_sample_size=minimum_sample_size,
            created_at=datetime.now()
        )
        
        self.experiments[experiment_id] = experiment
        
        logger.info(
            "A/B test experiment created",
            experiment_id=experiment_id,
            name=name,
            model_a=model_a,
            model_b=model_b,
            traffic_split=traffic_split
        )
        
        return experiment_id
    
    def _generate_experiment_id(self, name: str) -> str:
        """Generate unique experiment ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"exp_{timestamp}_{name_hash}"
    
    async def assign_model(self, user_id: str, experiment_id: str) -> str:
        """Assign user to model variant based on experiment configuration."""
        
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        if not experiment.is_active:
            return experiment.model_a  # Default to model A if experiment is inactive
        
        if datetime.now() > experiment.end_date:
            await self._deactivate_experiment(experiment_id)
            return experiment.model_a
        
        # Consistent assignment based on user ID hash
        user_hash = hashlib.md5(f"{user_id}_{experiment_id}".encode()).hexdigest()
        hash_value = int(user_hash[:8], 16) / (16**8)
        
        if hash_value < experiment.traffic_split:
            assigned_model = experiment.model_a
        else:
            assigned_model = experiment.model_b
        
        logger.debug(
            "Model assigned for A/B test",
            user_id=user_id,
            experiment_id=experiment_id,
            assigned_model=assigned_model,
            hash_value=hash_value
        )
        
        return assigned_model
    
    async def record_prediction(
        self,
        experiment_id: str,
        user_id: str,
        model_name: str,
        prediction: Dict[str, Any],
        actual_result: Optional[str] = None
    ):
        """Record prediction result for A/B test analysis."""
        
        if experiment_id not in self.experiments:
            return
        
        prediction_data = {
            'experiment_id': experiment_id,
            'user_id': user_id,
            'model_name': model_name,
            'prediction': prediction,
            'actual_result': actual_result,
            'timestamp': datetime.now().isoformat(),
            'confidence': prediction.get('confidence', 0.0)
        }
        
        # In production, store in database
        # For now, store in memory cache
        if experiment_id not in self.results_cache:
            self.results_cache[experiment_id] = []
        
        self.results_cache[experiment_id].append(prediction_data)
        
        logger.debug(
            "Prediction recorded for A/B test",
            experiment_id=experiment_id,
            model_name=model_name,
            confidence=prediction.get('confidence', 0.0)
        )
    
    async def get_experiment_results(self, experiment_id: str) -> Dict[str, ExperimentResult]:
        """Get current results for an A/B test experiment."""
        
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        predictions = self.results_cache.get(experiment_id, [])
        
        # Group predictions by model
        model_a_predictions = [p for p in predictions if p['model_name'] == experiment.model_a]
        model_b_predictions = [p for p in predictions if p['model_name'] == experiment.model_b]
        
        # Calculate results for each model
        results = {}
        
        for model_name, model_predictions in [
            (experiment.model_a, model_a_predictions),
            (experiment.model_b, model_b_predictions)
        ]:
            if not model_predictions:
                results[model_name] = ExperimentResult(
                    experiment_id=experiment_id,
                    model_name=model_name,
                    total_predictions=0,
                    correct_predictions=0,
                    accuracy=0.0,
                    avg_confidence=0.0,
                    conversion_rate=0.0,
                    statistical_significance=0.0
                )
                continue
            
            total_predictions = len(model_predictions)
            correct_predictions = sum(
                1 for p in model_predictions 
                if p['actual_result'] and p['prediction'].get('prediction') == p['actual_result']
            )
            
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
            avg_confidence = sum(p['confidence'] for p in model_predictions) / total_predictions
            
            # Conversion rate (high confidence predictions)
            high_confidence_predictions = sum(1 for p in model_predictions if p['confidence'] > 0.8)
            conversion_rate = high_confidence_predictions / total_predictions if total_predictions > 0 else 0.0
            
            results[model_name] = ExperimentResult(
                experiment_id=experiment_id,
                model_name=model_name,
                total_predictions=total_predictions,
                correct_predictions=correct_predictions,
                accuracy=accuracy,
                avg_confidence=avg_confidence,
                conversion_rate=conversion_rate,
                statistical_significance=0.0  # Would calculate with proper statistical test
            )
        
        return results
    
    async def calculate_statistical_significance(
        self, 
        experiment_id: str
    ) -> Dict[str, float]:
        """Calculate statistical significance of A/B test results."""
        
        results = await self.get_experiment_results(experiment_id)
        experiment = self.experiments[experiment_id]
        
        model_a_result = results.get(experiment.model_a)
        model_b_result = results.get(experiment.model_b)
        
        if not model_a_result or not model_b_result:
            return {'p_value': 1.0, 'significance': 0.0}
        
        # Simple z-test for proportions (in production, use proper statistical libraries)
        n1, n2 = model_a_result.total_predictions, model_b_result.total_predictions
        p1, p2 = model_a_result.accuracy, model_b_result.accuracy
        
        if n1 < 30 or n2 < 30:
            return {'p_value': 1.0, 'significance': 0.0}
        
        # Pooled proportion
        p_pool = (model_a_result.correct_predictions + model_b_result.correct_predictions) / (n1 + n2)
        
        # Standard error
        se = (p_pool * (1 - p_pool) * (1/n1 + 1/n2)) ** 0.5
        
        if se == 0:
            return {'p_value': 1.0, 'significance': 0.0}
        
        # Z-score
        z_score = abs(p1 - p2) / se
        
        # Approximate p-value (simplified)
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))
        
        significance = 1 - p_value
        
        return {
            'p_value': p_value,
            'significance': significance,
            'z_score': z_score,
            'effect_size': abs(p1 - p2)
        }
    
    def _normal_cdf(self, x: float) -> float:
        """Approximate normal CDF (simplified implementation)."""
        return 0.5 * (1 + self._erf(x / (2**0.5)))
    
    def _erf(self, x: float) -> float:
        """Approximate error function."""
        # Simplified approximation
        a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
        p = 0.3275911
        
        sign = 1 if x >= 0 else -1
        x = abs(x)
        
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * (2.718281828 ** (-x * x))
        
        return sign * y
    
    async def get_active_experiments(self) -> List[Experiment]:
        """Get all active experiments."""
        current_time = datetime.now()
        active_experiments = []
        
        for experiment in self.experiments.values():
            if experiment.is_active and current_time <= experiment.end_date:
                active_experiments.append(experiment)
            elif experiment.is_active and current_time > experiment.end_date:
                await self._deactivate_experiment(experiment.id)
        
        return active_experiments
    
    async def _deactivate_experiment(self, experiment_id: str):
        """Deactivate an experiment."""
        if experiment_id in self.experiments:
            self.experiments[experiment_id].is_active = False
            logger.info("Experiment deactivated", experiment_id=experiment_id)
    
    async def get_experiment_summary(self, experiment_id: str) -> Dict[str, Any]:
        """Get comprehensive experiment summary."""
        
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        results = await self.get_experiment_results(experiment_id)
        significance = await self.calculate_statistical_significance(experiment_id)
        
        # Determine winner
        model_a_result = results.get(experiment.model_a)
        model_b_result = results.get(experiment.model_b)
        
        winner = None
        if model_a_result and model_b_result:
            if model_a_result.accuracy > model_b_result.accuracy:
                winner = experiment.model_a
            elif model_b_result.accuracy > model_a_result.accuracy:
                winner = experiment.model_b
            else:
                winner = "tie"
        
        return {
            'experiment': asdict(experiment),
            'results': {k: asdict(v) for k, v in results.items()},
            'statistical_significance': significance,
            'winner': winner,
            'is_conclusive': significance['significance'] > 0.95,
            'sample_size_met': all(
                r.total_predictions >= experiment.minimum_sample_size 
                for r in results.values()
            )
        }


# Global A/B testing framework instance
ab_testing = ABTestingFramework()
