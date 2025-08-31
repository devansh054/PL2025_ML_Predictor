"""WebSocket manager for real-time updates and live match data."""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import structlog
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, asdict
import redis.asyncio as redis

logger = structlog.get_logger()

@dataclass
class LiveMatchUpdate:
    """Live match update data structure."""
    match_id: str
    home_team: str
    away_team: str
    minute: int
    home_score: int
    away_score: int
    status: str  # "live", "half-time", "full-time", "pre-match"
    events: List[Dict[str, Any]]
    updated_at: datetime

@dataclass
class PredictionUpdate:
    """Real-time prediction update."""
    match_id: str
    home_team: str
    away_team: str
    win_probability: float
    draw_probability: float
    loss_probability: float
    confidence: float
    model_used: str
    updated_at: datetime

class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}  # user_id -> set of topics
        self.topic_subscribers: Dict[str, Set[str]] = {}   # topic -> set of user_ids
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, topics: List[str] = None) -> str:
        """Accept WebSocket connection and register user."""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        # Initialize user subscriptions
        if topics is None:
            topics = ["general", "predictions", "live_matches"]
        
        self.user_subscriptions[connection_id] = set(topics)
        
        # Add to topic subscribers
        for topic in topics:
            if topic not in self.topic_subscribers:
                self.topic_subscribers[topic] = set()
            self.topic_subscribers[topic].add(connection_id)
        
        # Store connection metadata
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "topics": topics,
            "last_activity": datetime.now()
        }
        
        logger.info(
            "WebSocket connection established",
            connection_id=connection_id,
            user_id=user_id,
            topics=topics
        )
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "connection_id": connection_id,
            "subscribed_topics": topics,
            "timestamp": datetime.now().isoformat()
        }, connection_id)
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Remove WebSocket connection and clean up subscriptions."""
        if connection_id in self.active_connections:
            # Remove from topic subscribers
            if connection_id in self.user_subscriptions:
                for topic in self.user_subscriptions[connection_id]:
                    if topic in self.topic_subscribers:
                        self.topic_subscribers[topic].discard(connection_id)
                        if not self.topic_subscribers[topic]:
                            del self.topic_subscribers[topic]
                
                del self.user_subscriptions[connection_id]
            
            # Clean up connection data
            del self.active_connections[connection_id]
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            logger.info("WebSocket connection closed", connection_id=connection_id)
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message, default=str))
                
                # Update last activity
                if connection_id in self.connection_metadata:
                    self.connection_metadata[connection_id]["last_activity"] = datetime.now()
                    
            except Exception as e:
                logger.error(
                    "Failed to send personal message",
                    connection_id=connection_id,
                    error=str(e)
                )
                await self.disconnect(connection_id)
    
    async def broadcast_to_topic(self, message: Dict[str, Any], topic: str):
        """Broadcast message to all subscribers of a topic."""
        if topic not in self.topic_subscribers:
            return
        
        message["topic"] = topic
        message["timestamp"] = datetime.now().isoformat()
        
        disconnected_connections = []
        
        for connection_id in self.topic_subscribers[topic].copy():
            try:
                await self.send_personal_message(message, connection_id)
            except Exception as e:
                logger.error(
                    "Failed to broadcast to connection",
                    connection_id=connection_id,
                    topic=topic,
                    error=str(e)
                )
                disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            await self.disconnect(connection_id)
        
        logger.debug(
            "Message broadcasted to topic",
            topic=topic,
            subscribers=len(self.topic_subscribers.get(topic, [])),
            message_type=message.get("type", "unknown")
        )
    
    async def subscribe_to_topic(self, connection_id: str, topic: str):
        """Subscribe connection to a topic."""
        if connection_id not in self.active_connections:
            return False
        
        # Add to user subscriptions
        if connection_id not in self.user_subscriptions:
            self.user_subscriptions[connection_id] = set()
        self.user_subscriptions[connection_id].add(topic)
        
        # Add to topic subscribers
        if topic not in self.topic_subscribers:
            self.topic_subscribers[topic] = set()
        self.topic_subscribers[topic].add(connection_id)
        
        # Update metadata
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["topics"].append(topic)
        
        await self.send_personal_message({
            "type": "subscribed",
            "topic": topic,
            "message": f"Successfully subscribed to {topic}"
        }, connection_id)
        
        logger.info(
            "User subscribed to topic",
            connection_id=connection_id,
            topic=topic
        )
        
        return True
    
    async def unsubscribe_from_topic(self, connection_id: str, topic: str):
        """Unsubscribe connection from a topic."""
        if connection_id not in self.active_connections:
            return False
        
        # Remove from user subscriptions
        if connection_id in self.user_subscriptions:
            self.user_subscriptions[connection_id].discard(topic)
        
        # Remove from topic subscribers
        if topic in self.topic_subscribers:
            self.topic_subscribers[topic].discard(connection_id)
            if not self.topic_subscribers[topic]:
                del self.topic_subscribers[topic]
        
        await self.send_personal_message({
            "type": "unsubscribed",
            "topic": topic,
            "message": f"Successfully unsubscribed from {topic}"
        }, connection_id)
        
        logger.info(
            "User unsubscribed from topic",
            connection_id=connection_id,
            topic=topic
        )
        
        return True
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "topics": list(self.topic_subscribers.keys()),
            "topic_subscriber_counts": {
                topic: len(subscribers) 
                for topic, subscribers in self.topic_subscribers.items()
            },
            "active_users": len(set(
                meta.get("user_id") 
                for meta in self.connection_metadata.values()
                if meta.get("user_id")
            ))
        }

class LiveMatchService:
    """Service for managing live match data and updates."""
    
    def __init__(self, connection_manager: ConnectionManager, redis_client: Optional[redis.Redis] = None):
        self.connection_manager = connection_manager
        self.redis_client = redis_client
        self.live_matches: Dict[str, LiveMatchUpdate] = {}
        self.match_predictions: Dict[str, PredictionUpdate] = {}
        self.update_tasks: Dict[str, asyncio.Task] = {}
        
    async def start_live_match(self, match_data: Dict[str, Any]) -> str:
        """Start tracking a live match."""
        match_id = match_data.get("match_id", str(uuid.uuid4()))
        
        live_match = LiveMatchUpdate(
            match_id=match_id,
            home_team=match_data["home_team"],
            away_team=match_data["away_team"],
            minute=0,
            home_score=0,
            away_score=0,
            status="pre-match",
            events=[],
            updated_at=datetime.now()
        )
        
        self.live_matches[match_id] = live_match
        
        # Start update task for this match
        self.update_tasks[match_id] = asyncio.create_task(
            self._simulate_live_match_updates(match_id)
        )
        
        # Broadcast match start
        await self.connection_manager.broadcast_to_topic({
            "type": "match_started",
            "match": asdict(live_match)
        }, "live_matches")
        
        logger.info("Live match started", match_id=match_id)
        return match_id
    
    async def update_match_score(self, match_id: str, home_score: int, away_score: int, minute: int):
        """Update match score and broadcast to subscribers."""
        if match_id not in self.live_matches:
            return False
        
        match = self.live_matches[match_id]
        match.home_score = home_score
        match.away_score = away_score
        match.minute = minute
        match.updated_at = datetime.now()
        
        # Add score event
        if home_score != match.home_score or away_score != match.away_score:
            match.events.append({
                "type": "goal",
                "minute": minute,
                "team": match.home_team if home_score > match.home_score else match.away_team,
                "score": f"{home_score}-{away_score}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Cache in Redis if available
        if self.redis_client:
            await self.redis_client.setex(
                f"live_match:{match_id}",
                3600,  # 1 hour TTL
                json.dumps(asdict(match), default=str)
            )
        
        # Broadcast update
        await self.connection_manager.broadcast_to_topic({
            "type": "score_update",
            "match_id": match_id,
            "home_score": home_score,
            "away_score": away_score,
            "minute": minute,
            "events": match.events[-3:]  # Last 3 events
        }, "live_matches")
        
        # Update predictions based on new score
        await self._update_live_predictions(match_id)
        
        return True
    
    async def _update_live_predictions(self, match_id: str):
        """Update predictions based on current match state."""
        if match_id not in self.live_matches:
            return
        
        match = self.live_matches[match_id]
        
        # Simple live prediction logic based on current score and time
        home_score, away_score = match.home_score, match.away_score
        minute = match.minute
        
        # Adjust probabilities based on score and time remaining
        time_factor = max(0.1, (90 - minute) / 90)  # Less time = more certain
        score_diff = home_score - away_score
        
        if score_diff > 0:  # Home team leading
            win_prob = 0.6 + (score_diff * 0.15) * (1 - time_factor)
            loss_prob = 0.2 - (score_diff * 0.05) * (1 - time_factor)
        elif score_diff < 0:  # Away team leading
            win_prob = 0.2 + (score_diff * 0.05) * (1 - time_factor)
            loss_prob = 0.6 - (score_diff * 0.15) * (1 - time_factor)
        else:  # Draw
            win_prob = 0.4
            loss_prob = 0.4
        
        draw_prob = max(0.1, 1.0 - win_prob - loss_prob)
        
        # Normalize
        total = win_prob + draw_prob + loss_prob
        win_prob /= total
        draw_prob /= total
        loss_prob /= total
        
        prediction_update = PredictionUpdate(
            match_id=match_id,
            home_team=match.home_team,
            away_team=match.away_team,
            win_probability=round(win_prob, 3),
            draw_probability=round(draw_prob, 3),
            loss_probability=round(loss_prob, 3),
            confidence=round(1 - time_factor, 3),
            model_used="Live-Adjusted",
            updated_at=datetime.now()
        )
        
        self.match_predictions[match_id] = prediction_update
        
        # Broadcast prediction update
        await self.connection_manager.broadcast_to_topic({
            "type": "prediction_update",
            "prediction": asdict(prediction_update)
        }, "predictions")
    
    async def _simulate_live_match_updates(self, match_id: str):
        """Simulate live match updates for demonstration."""
        try:
            match = self.live_matches[match_id]
            
            # Simulate match progression
            for minute in range(1, 91, 5):  # Every 5 minutes
                if match_id not in self.live_matches:  # Match stopped
                    break
                
                # Random events
                if minute == 1:
                    match.status = "live"
                elif minute == 45:
                    match.status = "half-time"
                    await asyncio.sleep(2)  # Half-time break
                    match.status = "live"
                elif minute == 90:
                    match.status = "full-time"
                
                # Random score updates (low probability)
                if minute > 10 and minute < 85 and len(match.events) < 4:
                    if asyncio.get_event_loop().time() % 7 < 1:  # ~14% chance
                        if asyncio.get_event_loop().time() % 2 < 1:
                            match.home_score += 1
                        else:
                            match.away_score += 1
                        
                        await self.update_match_score(
                            match_id, match.home_score, match.away_score, minute
                        )
                
                match.minute = minute
                match.updated_at = datetime.now()
                
                # Broadcast minute update
                await self.connection_manager.broadcast_to_topic({
                    "type": "minute_update",
                    "match_id": match_id,
                    "minute": minute,
                    "status": match.status
                }, "live_matches")
                
                if match.status == "full-time":
                    break
                
                await asyncio.sleep(2)  # 2 seconds per "minute"
            
            # Final update
            match.status = "full-time"
            await self.connection_manager.broadcast_to_topic({
                "type": "match_finished",
                "match": asdict(match)
            }, "live_matches")
            
        except asyncio.CancelledError:
            logger.info("Live match simulation cancelled", match_id=match_id)
        except Exception as e:
            logger.error("Error in live match simulation", match_id=match_id, error=str(e))
        finally:
            # Clean up
            if match_id in self.update_tasks:
                del self.update_tasks[match_id]
    
    async def stop_live_match(self, match_id: str):
        """Stop tracking a live match."""
        if match_id in self.update_tasks:
            self.update_tasks[match_id].cancel()
            del self.update_tasks[match_id]
        
        if match_id in self.live_matches:
            match = self.live_matches[match_id]
            match.status = "finished"
            
            await self.connection_manager.broadcast_to_topic({
                "type": "match_stopped",
                "match_id": match_id
            }, "live_matches")
            
            del self.live_matches[match_id]
        
        logger.info("Live match stopped", match_id=match_id)
    
    def get_live_matches(self) -> List[Dict[str, Any]]:
        """Get all currently live matches."""
        return [asdict(match) for match in self.live_matches.values()]
    
    def get_match_predictions(self) -> List[Dict[str, Any]]:
        """Get all current match predictions."""
        return [asdict(pred) for pred in self.match_predictions.values()]

# Global instances
connection_manager = ConnectionManager()
live_match_service = LiveMatchService(connection_manager)
