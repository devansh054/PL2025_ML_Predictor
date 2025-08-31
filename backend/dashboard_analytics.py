"""Interactive dashboard analytics with advanced visualizations and insights."""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import base64
from io import BytesIO
import structlog

logger = structlog.get_logger()

@dataclass
class DashboardMetric:
    """Dashboard metric data structure."""
    name: str
    value: float
    change: float  # Percentage change
    trend: str  # "up", "down", "stable"
    format_type: str  # "percentage", "number", "currency", "time"
    description: str

@dataclass
class ChartData:
    """Chart data structure."""
    chart_id: str
    title: str
    chart_type: str  # "line", "bar", "pie", "scatter", "heatmap", "3d"
    data: Dict[str, Any]
    config: Dict[str, Any]
    insights: List[str]

class DashboardAnalytics:
    """Advanced analytics engine for interactive dashboards."""
    
    def __init__(self):
        self.color_palette = {
            "primary": "#1f77b4",
            "success": "#2ca02c", 
            "warning": "#ff7f0e",
            "danger": "#d62728",
            "info": "#17a2b8",
            "premier_league": "#37003c"
        }
        
    def generate_kpi_metrics(self, data: Dict[str, Any]) -> List[DashboardMetric]:
        """Generate key performance indicator metrics."""
        
        # Mock data for demonstration - in production, calculate from real data
        metrics = [
            DashboardMetric(
                name="Model Accuracy",
                value=81.4,
                change=2.3,
                trend="up",
                format_type="percentage",
                description="Overall prediction accuracy across all models"
            ),
            DashboardMetric(
                name="Predictions Today",
                value=1247,
                change=15.8,
                trend="up", 
                format_type="number",
                description="Total predictions made in the last 24 hours"
            ),
            DashboardMetric(
                name="Active Users",
                value=89,
                change=-5.2,
                trend="down",
                format_type="number",
                description="Currently active users on the platform"
            ),
            DashboardMetric(
                name="Avg Response Time",
                value=0.234,
                change=-12.1,
                trend="up",  # Lower is better for response time
                format_type="time",
                description="Average API response time in seconds"
            ),
            DashboardMetric(
                name="Cache Hit Rate",
                value=94.7,
                change=3.1,
                trend="up",
                format_type="percentage", 
                description="Percentage of requests served from cache"
            ),
            DashboardMetric(
                name="System Uptime",
                value=99.97,
                change=0.02,
                trend="stable",
                format_type="percentage",
                description="System availability over the last 30 days"
            )
        ]
        
        return metrics
    
    def create_prediction_accuracy_chart(self, data: Optional[Dict] = None) -> ChartData:
        """Create prediction accuracy trend chart."""
        
        # Generate sample data
        dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
        models = ['Random Forest', 'Gradient Boosting', 'Logistic Regression', 'Ensemble']
        
        fig = go.Figure()
        
        for model in models:
            # Generate realistic accuracy trends
            base_accuracy = np.random.uniform(0.75, 0.85)
            noise = np.random.normal(0, 0.02, len(dates))
            trend = np.linspace(0, 0.05, len(dates))  # Slight improvement over time
            accuracy = base_accuracy + trend + noise
            accuracy = np.clip(accuracy, 0.7, 0.9)  # Keep realistic bounds
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=accuracy,
                mode='lines+markers',
                name=model,
                line=dict(width=3),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title="Model Accuracy Trends Over Time",
            xaxis_title="Date",
            yaxis_title="Accuracy",
            yaxis=dict(range=[0.7, 0.9], tickformat='.1%'),
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        return ChartData(
            chart_id="accuracy_trends",
            title="Model Accuracy Trends",
            chart_type="line",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=[
                "Ensemble model shows most consistent performance",
                "All models show gradual improvement over time",
                "Random Forest has highest peak accuracy at 87.3%"
            ]
        )
    
    def create_team_performance_heatmap(self, data: Optional[Dict] = None) -> ChartData:
        """Create team performance heatmap."""
        
        teams = [
            "Arsenal", "Chelsea", "Liverpool", "Manchester City", "Manchester United",
            "Tottenham", "Newcastle United", "Brighton", "Aston Villa", "West Ham"
        ]
        
        metrics = ["Goals For", "Goals Against", "Possession %", "Pass Accuracy", "Shots on Target"]
        
        # Generate sample performance data
        performance_data = np.random.rand(len(teams), len(metrics))
        performance_data = (performance_data * 40 + 60)  # Scale to 60-100 range
        
        fig = go.Figure(data=go.Heatmap(
            z=performance_data,
            x=metrics,
            y=teams,
            colorscale='RdYlGn',
            colorbar=dict(title="Performance Score"),
            hoverongaps=False,
            text=np.round(performance_data, 1),
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="Team Performance Heatmap",
            xaxis_title="Performance Metrics",
            yaxis_title="Teams",
            height=500,
            template='plotly_white'
        )
        
        return ChartData(
            chart_id="team_heatmap",
            title="Team Performance Analysis",
            chart_type="heatmap",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=[
                "Manchester City leads in possession and pass accuracy",
                "Liverpool shows strongest attacking metrics",
                "Arsenal demonstrates most balanced performance across all metrics"
            ]
        )
    
    def create_prediction_distribution_chart(self, data: Optional[Dict] = None) -> ChartData:
        """Create prediction confidence distribution chart."""
        
        # Generate sample prediction confidence data
        np.random.seed(42)
        confidence_scores = np.random.beta(2, 1.5, 1000) * 100  # Beta distribution for realistic confidence
        
        fig = go.Figure()
        
        # Histogram
        fig.add_trace(go.Histogram(
            x=confidence_scores,
            nbinsx=30,
            name="Confidence Distribution",
            marker_color=self.color_palette["primary"],
            opacity=0.7
        ))
        
        # Add mean line
        mean_confidence = np.mean(confidence_scores)
        fig.add_vline(
            x=mean_confidence,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean: {mean_confidence:.1f}%"
        )
        
        fig.update_layout(
            title="Prediction Confidence Distribution",
            xaxis_title="Confidence Score (%)",
            yaxis_title="Number of Predictions",
            template='plotly_white',
            height=400
        )
        
        return ChartData(
            chart_id="confidence_distribution",
            title="Prediction Confidence Analysis",
            chart_type="histogram",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=[
                f"Average prediction confidence: {mean_confidence:.1f}%",
                "Most predictions fall in the 60-80% confidence range",
                "High confidence predictions (>90%) represent top-tier match certainty"
            ]
        )
    
    def create_real_time_metrics_chart(self, data: Optional[Dict] = None) -> ChartData:
        """Create real-time system metrics chart."""
        
        # Generate sample real-time data
        timestamps = pd.date_range(start=datetime.now() - timedelta(hours=1), 
                                 end=datetime.now(), freq='1min')
        
        cpu_usage = 50 + 20 * np.sin(np.linspace(0, 4*np.pi, len(timestamps))) + np.random.normal(0, 5, len(timestamps))
        memory_usage = 60 + 15 * np.cos(np.linspace(0, 3*np.pi, len(timestamps))) + np.random.normal(0, 3, len(timestamps))
        requests_per_min = 100 + 30 * np.sin(np.linspace(0, 6*np.pi, len(timestamps))) + np.random.normal(0, 10, len(timestamps))
        
        # Ensure realistic bounds
        cpu_usage = np.clip(cpu_usage, 0, 100)
        memory_usage = np.clip(memory_usage, 0, 100)
        requests_per_min = np.clip(requests_per_min, 0, 200)
        
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('CPU Usage (%)', 'Memory Usage (%)', 'Requests per Minute'),
            vertical_spacing=0.1
        )
        
        fig.add_trace(
            go.Scatter(x=timestamps, y=cpu_usage, name="CPU", line=dict(color=self.color_palette["danger"])),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=timestamps, y=memory_usage, name="Memory", line=dict(color=self.color_palette["warning"])),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=timestamps, y=requests_per_min, name="Requests", line=dict(color=self.color_palette["success"])),
            row=3, col=1
        )
        
        fig.update_layout(
            title="Real-Time System Metrics",
            height=600,
            template='plotly_white',
            showlegend=False
        )
        
        return ChartData(
            chart_id="realtime_metrics",
            title="System Performance Monitoring",
            chart_type="multiline",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=[
                f"Current CPU usage: {cpu_usage[-1]:.1f}%",
                f"Current memory usage: {memory_usage[-1]:.1f}%",
                f"Request rate: {requests_per_min[-1]:.0f}/min"
            ]
        )
    
    def create_match_outcome_pie_chart(self, data: Optional[Dict] = None) -> ChartData:
        """Create match outcome distribution pie chart."""
        
        # Sample match outcome data
        outcomes = {
            'Home Win': 342,
            'Draw': 156, 
            'Away Win': 289
        }
        
        colors = [self.color_palette["success"], self.color_palette["warning"], self.color_palette["danger"]]
        
        fig = go.Figure(data=[go.Pie(
            labels=list(outcomes.keys()),
            values=list(outcomes.values()),
            hole=0.4,
            marker_colors=colors,
            textinfo='label+percent+value',
            textfont_size=12
        )])
        
        fig.update_layout(
            title="Match Outcome Distribution (Season 2023-24)",
            template='plotly_white',
            height=400,
            annotations=[dict(text='Total<br>787', x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        
        return ChartData(
            chart_id="outcome_pie",
            title="Match Outcomes Analysis",
            chart_type="pie",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=[
                "Home advantage evident with 43.4% home wins",
                "Away wins account for 36.7% of matches",
                "Draws represent 19.8% of all matches"
            ]
        )
    
    def create_feature_importance_chart(self, data: Optional[Dict] = None) -> ChartData:
        """Create feature importance visualization."""
        
        features = [
            "Team Strength Diff", "Recent Form", "Head-to-Head Record", 
            "Home Advantage", "Player Quality", "Injury Impact",
            "Weather Conditions", "Market Sentiment", "Historical Performance",
            "Goal Difference", "Possession Style", "Defensive Record"
        ]
        
        importance_scores = np.random.exponential(0.3, len(features))
        importance_scores = importance_scores / np.sum(importance_scores) * 100  # Normalize to 100%
        importance_scores = np.sort(importance_scores)[::-1]  # Sort descending
        
        fig = go.Figure(data=[
            go.Bar(
                x=importance_scores,
                y=features,
                orientation='h',
                marker_color=px.colors.sequential.Viridis[::2][:len(features)]
            )
        ])
        
        fig.update_layout(
            title="ML Model Feature Importance",
            xaxis_title="Importance Score (%)",
            yaxis_title="Features",
            template='plotly_white',
            height=500
        )
        
        return ChartData(
            chart_id="feature_importance",
            title="Model Feature Analysis",
            chart_type="horizontal_bar",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=[
                f"Top feature: {features[0]} ({importance_scores[0]:.1f}%)",
                "Team strength differential is the strongest predictor",
                "Recent form and historical data provide significant value"
            ]
        )
    
    def create_3d_performance_scatter(self, data: Optional[Dict] = None) -> ChartData:
        """Create 3D scatter plot of team performance."""
        
        teams = [
            "Arsenal", "Chelsea", "Liverpool", "Manchester City", "Manchester United",
            "Tottenham", "Newcastle United", "Brighton", "Aston Villa", "West Ham",
            "Crystal Palace", "Fulham", "Wolves", "Everton", "Brentford"
        ]
        
        # Generate 3D performance data
        goals_for = np.random.normal(1.8, 0.4, len(teams))
        goals_against = np.random.normal(1.3, 0.3, len(teams))
        possession = np.random.normal(55, 8, len(teams))
        
        # Ensure realistic bounds
        goals_for = np.clip(goals_for, 0.8, 3.0)
        goals_against = np.clip(goals_against, 0.5, 2.5)
        possession = np.clip(possession, 35, 75)
        
        fig = go.Figure(data=[go.Scatter3d(
            x=goals_for,
            y=goals_against,
            z=possession,
            mode='markers+text',
            text=teams,
            textposition="top center",
            marker=dict(
                size=8,
                color=goals_for,  # Color by goals scored
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Goals For")
            )
        )])
        
        fig.update_layout(
            title="3D Team Performance Analysis",
            scene=dict(
                xaxis_title='Goals For (per game)',
                yaxis_title='Goals Against (per game)',
                zaxis_title='Possession (%)',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            height=600,
            template='plotly_white'
        )
        
        return ChartData(
            chart_id="3d_performance",
            title="Multi-dimensional Performance View",
            chart_type="3d_scatter",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=[
                "Top-right quadrant shows high-scoring, defensively solid teams",
                "Possession percentage varies significantly across performance levels",
                "Elite teams cluster in low goals-against, high goals-for region"
            ]
        )
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate complete dashboard data."""
        
        return {
            "kpi_metrics": [asdict(metric) for metric in self.generate_kpi_metrics({})],
            "charts": [
                asdict(self.create_prediction_accuracy_chart()),
                asdict(self.create_team_performance_heatmap()),
                asdict(self.create_prediction_distribution_chart()),
                asdict(self.create_real_time_metrics_chart()),
                asdict(self.create_match_outcome_pie_chart()),
                asdict(self.create_feature_importance_chart()),
                asdict(self.create_3d_performance_scatter())
            ],
            "last_updated": datetime.now().isoformat(),
            "refresh_interval": 30,  # seconds
            "theme": "light"
        }
    
    def generate_custom_chart(self, chart_config: Dict[str, Any]) -> ChartData:
        """Generate custom chart based on configuration."""
        
        chart_type = chart_config.get("type", "line")
        title = chart_config.get("title", "Custom Chart")
        
        if chart_type == "line":
            return self._create_custom_line_chart(chart_config)
        elif chart_type == "bar":
            return self._create_custom_bar_chart(chart_config)
        elif chart_type == "pie":
            return self._create_custom_pie_chart(chart_config)
        else:
            # Default to line chart
            return self._create_custom_line_chart(chart_config)
    
    def _create_custom_line_chart(self, config: Dict[str, Any]) -> ChartData:
        """Create custom line chart."""
        
        # Generate sample data based on config
        x_data = config.get("x_data", list(range(10)))
        y_data = config.get("y_data", np.random.randn(10).cumsum())
        
        fig = go.Figure(data=go.Scatter(x=x_data, y=y_data, mode='lines+markers'))
        fig.update_layout(
            title=config.get("title", "Custom Line Chart"),
            xaxis_title=config.get("x_title", "X Axis"),
            yaxis_title=config.get("y_title", "Y Axis"),
            template='plotly_white'
        )
        
        return ChartData(
            chart_id=f"custom_{config.get('id', 'chart')}",
            title=config.get("title", "Custom Chart"),
            chart_type="line",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=config.get("insights", ["Custom chart generated successfully"])
        )
    
    def _create_custom_bar_chart(self, config: Dict[str, Any]) -> ChartData:
        """Create custom bar chart."""
        
        x_data = config.get("x_data", ["A", "B", "C", "D"])
        y_data = config.get("y_data", [1, 3, 2, 4])
        
        fig = go.Figure(data=go.Bar(x=x_data, y=y_data))
        fig.update_layout(
            title=config.get("title", "Custom Bar Chart"),
            xaxis_title=config.get("x_title", "Categories"),
            yaxis_title=config.get("y_title", "Values"),
            template='plotly_white'
        )
        
        return ChartData(
            chart_id=f"custom_{config.get('id', 'chart')}",
            title=config.get("title", "Custom Chart"),
            chart_type="bar",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=config.get("insights", ["Custom chart generated successfully"])
        )
    
    def _create_custom_pie_chart(self, config: Dict[str, Any]) -> ChartData:
        """Create custom pie chart."""
        
        labels = config.get("labels", ["A", "B", "C"])
        values = config.get("values", [30, 40, 30])
        
        fig = go.Figure(data=go.Pie(labels=labels, values=values))
        fig.update_layout(
            title=config.get("title", "Custom Pie Chart"),
            template='plotly_white'
        )
        
        return ChartData(
            chart_id=f"custom_{config.get('id', 'chart')}",
            title=config.get("title", "Custom Chart"),
            chart_type="pie",
            data=fig.to_dict(),
            config={"displayModeBar": True, "responsive": True},
            insights=config.get("insights", ["Custom chart generated successfully"])
        )

# Global dashboard analytics instance
dashboard_analytics = DashboardAnalytics()
