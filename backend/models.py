"""Database models for Premier League Predictor."""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .database import Base


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    logo_url = Column(String(500))
    primary_color = Column(String(7))
    secondary_color = Column(String(7))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    home_predictions = relationship("Prediction", foreign_keys="Prediction.home_team_id", back_populates="home_team")
    away_predictions = relationship("Prediction", foreign_keys="Prediction.away_team_id", back_populates="away_team")


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    home_score = Column(Integer)
    away_score = Column(Integer)
    match_date = Column(Date, nullable=False)
    season = Column(String(10), nullable=False)
    gameweek = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    predicted_home_score = Column(Float)
    predicted_away_score = Column(Float)
    confidence_score = Column(Float)
    model_version = Column(String(50))
    prediction_date = Column(DateTime(timezone=True), server_default=func.now())
    actual_home_score = Column(Integer)
    actual_away_score = Column(Integer)
    is_correct = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_predictions")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_predictions")


class ModelPerformance(Base):
    __tablename__ = "model_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    accuracy = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    f1_score = Column(Float)
    training_date = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FeatureImportance(Base):
    __tablename__ = "feature_importance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version = Column(String(50), nullable=False)
    feature_name = Column(String(100), nullable=False)
    importance_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    prediction_requests = relationship("PredictionRequest", back_populates="session")


class PredictionRequest(Base):
    __tablename__ = "prediction_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), ForeignKey("user_sessions.session_id"))
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"))
    response_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("UserSession", back_populates="prediction_requests")
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
