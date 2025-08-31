"""Event-driven architecture with message queues for scalable processing."""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import structlog
from abc import ABC, abstractmethod
import redis.asyncio as redis

logger = structlog.get_logger()

class EventType(Enum):
    """Event types for the message queue system."""
    PREDICTION_REQUESTED = "prediction_requested"
    PREDICTION_COMPLETED = "prediction_completed"
    MATCH_STARTED = "match_started"
    MATCH_UPDATED = "match_updated"
    MATCH_FINISHED = "match_finished"
    MODEL_RETRAINED = "model_retrained"
    CACHE_INVALIDATED = "cache_invalidated"
    USER_CONNECTED = "user_connected"
    USER_DISCONNECTED = "user_disconnected"
    SYSTEM_ALERT = "system_alert"

@dataclass
class Event:
    """Event message structure."""
    id: str
    type: EventType
    payload: Dict[str, Any]
    timestamp: datetime
    source: str
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    async def handle(self, event: Event) -> bool:
        """Handle an event. Return True if successful, False to retry."""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler can process the given event type."""
        pass

class MessageQueue:
    """Async message queue implementation with Redis backend."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.handlers: Dict[EventType, List[EventHandler]] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.dead_letter_queue: List[Event] = []
        self.metrics = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "handlers_registered": 0
        }
        
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Initialize the message queue with Redis connection."""
        if not self.redis_client:
            self.redis_client = redis.from_url(redis_url)
        
        # Test connection
        try:
            await self.redis_client.ping()
            logger.info("Message queue initialized with Redis")
        except Exception as e:
            logger.warning("Redis not available, using in-memory queue", error=str(e))
            self.redis_client = None
    
    def register_handler(self, event_type: EventType, handler: EventHandler):
        """Register an event handler for a specific event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        self.metrics["handlers_registered"] += 1
        
        logger.info(
            "Event handler registered",
            event_type=event_type.value,
            handler=handler.__class__.__name__
        )
    
    async def publish(self, event_type: EventType, payload: Dict[str, Any], 
                     source: str = "unknown", correlation_id: Optional[str] = None) -> str:
        """Publish an event to the queue."""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            payload=payload,
            timestamp=datetime.now(),
            source=source,
            correlation_id=correlation_id or str(uuid.uuid4())
        )
        
        if self.redis_client:
            # Use Redis for persistent queue
            await self._publish_to_redis(event)
        else:
            # Use in-memory processing
            await self._process_event_immediately(event)
        
        self.metrics["events_published"] += 1
        
        logger.debug(
            "Event published",
            event_id=event.id,
            event_type=event_type.value,
            correlation_id=event.correlation_id
        )
        
        return event.id
    
    async def _publish_to_redis(self, event: Event):
        """Publish event to Redis queue."""
        queue_name = f"events:{event.type.value}"
        event_data = {
            "id": event.id,
            "type": event.type.value,
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "correlation_id": event.correlation_id,
            "retry_count": event.retry_count,
            "max_retries": event.max_retries
        }
        
        await self.redis_client.lpush(queue_name, json.dumps(event_data, default=str))
        
        # Set expiration for the queue (24 hours)
        await self.redis_client.expire(queue_name, 86400)
    
    async def _process_event_immediately(self, event: Event):
        """Process event immediately (in-memory mode)."""
        task = asyncio.create_task(self._handle_event(event))
        self.processing_tasks[event.id] = task
    
    async def start_consumers(self, num_consumers: int = 3):
        """Start consumer tasks to process events from Redis queues."""
        if not self.redis_client:
            logger.info("Redis not available, events will be processed immediately")
            return
        
        consumer_tasks = []
        for i in range(num_consumers):
            task = asyncio.create_task(self._consumer_worker(f"consumer-{i}"))
            consumer_tasks.append(task)
        
        logger.info(f"Started {num_consumers} consumer workers")
        return consumer_tasks
    
    async def _consumer_worker(self, worker_id: str):
        """Worker that consumes events from Redis queues."""
        logger.info(f"Consumer worker {worker_id} started")
        
        while True:
            try:
                # Check all event type queues
                for event_type in EventType:
                    queue_name = f"events:{event_type.value}"
                    
                    # Non-blocking pop from queue
                    result = await self.redis_client.brpop([queue_name], timeout=1)
                    
                    if result:
                        _, event_data = result
                        event_dict = json.loads(event_data)
                        
                        # Reconstruct event object
                        event = Event(
                            id=event_dict["id"],
                            type=EventType(event_dict["type"]),
                            payload=event_dict["payload"],
                            timestamp=datetime.fromisoformat(event_dict["timestamp"]),
                            source=event_dict["source"],
                            correlation_id=event_dict.get("correlation_id"),
                            retry_count=event_dict.get("retry_count", 0),
                            max_retries=event_dict.get("max_retries", 3)
                        )
                        
                        # Process the event
                        await self._handle_event(event)
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except asyncio.CancelledError:
                logger.info(f"Consumer worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in consumer worker {worker_id}", error=str(e))
                await asyncio.sleep(1)  # Back off on error
    
    async def _handle_event(self, event: Event):
        """Handle a single event by calling appropriate handlers."""
        try:
            if event.type not in self.handlers:
                logger.warning("No handlers registered for event type", event_type=event.type.value)
                return
            
            handlers = self.handlers[event.type]
            success_count = 0
            
            for handler in handlers:
                try:
                    if handler.can_handle(event.type):
                        success = await handler.handle(event)
                        if success:
                            success_count += 1
                        else:
                            logger.warning(
                                "Handler failed to process event",
                                handler=handler.__class__.__name__,
                                event_id=event.id
                            )
                except Exception as e:
                    logger.error(
                        "Handler raised exception",
                        handler=handler.__class__.__name__,
                        event_id=event.id,
                        error=str(e)
                    )
            
            if success_count > 0:
                self.metrics["events_processed"] += 1
                logger.debug(
                    "Event processed successfully",
                    event_id=event.id,
                    handlers_succeeded=success_count
                )
            else:
                # Retry logic
                if event.retry_count < event.max_retries:
                    event.retry_count += 1
                    await asyncio.sleep(2 ** event.retry_count)  # Exponential backoff
                    await self._handle_event(event)
                else:
                    # Move to dead letter queue
                    self.dead_letter_queue.append(event)
                    self.metrics["events_failed"] += 1
                    logger.error(
                        "Event moved to dead letter queue",
                        event_id=event.id,
                        retry_count=event.retry_count
                    )
        
        except Exception as e:
            logger.error("Unexpected error handling event", event_id=event.id, error=str(e))
        
        finally:
            # Clean up processing task
            if event.id in self.processing_tasks:
                del self.processing_tasks[event.id]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get queue metrics."""
        return {
            **self.metrics,
            "active_processing_tasks": len(self.processing_tasks),
            "dead_letter_queue_size": len(self.dead_letter_queue),
            "registered_event_types": list(self.handlers.keys())
        }

# Specific Event Handlers

class PredictionEventHandler(EventHandler):
    """Handler for prediction-related events."""
    
    def __init__(self, ml_pipeline=None, websocket_manager=None):
        self.ml_pipeline = ml_pipeline
        self.websocket_manager = websocket_manager
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in [
            EventType.PREDICTION_REQUESTED,
            EventType.PREDICTION_COMPLETED
        ]
    
    async def handle(self, event: Event) -> bool:
        try:
            if event.type == EventType.PREDICTION_REQUESTED:
                return await self._handle_prediction_request(event)
            elif event.type == EventType.PREDICTION_COMPLETED:
                return await self._handle_prediction_completed(event)
            
            return False
            
        except Exception as e:
            logger.error("Error in prediction event handler", error=str(e))
            return False
    
    async def _handle_prediction_request(self, event: Event) -> bool:
        """Handle prediction request event."""
        payload = event.payload
        home_team = payload.get("home_team")
        away_team = payload.get("away_team")
        user_id = payload.get("user_id")
        
        logger.info(
            "Processing prediction request",
            home_team=home_team,
            away_team=away_team,
            user_id=user_id,
            correlation_id=event.correlation_id
        )
        
        # Simulate prediction processing
        await asyncio.sleep(0.5)  # Simulate ML processing time
        
        # Publish completion event
        if hasattr(self, 'message_queue'):
            await self.message_queue.publish(
                EventType.PREDICTION_COMPLETED,
                {
                    "prediction_id": str(uuid.uuid4()),
                    "home_team": home_team,
                    "away_team": away_team,
                    "win_probability": 0.45,
                    "draw_probability": 0.25,
                    "loss_probability": 0.30,
                    "confidence": 0.78,
                    "model_used": "Ensemble",
                    "user_id": user_id
                },
                source="prediction_handler",
                correlation_id=event.correlation_id
            )
        
        return True
    
    async def _handle_prediction_completed(self, event: Event) -> bool:
        """Handle prediction completion event."""
        payload = event.payload
        
        # Broadcast to WebSocket clients if available
        if self.websocket_manager:
            await self.websocket_manager.broadcast_to_topic({
                "type": "prediction_ready",
                "prediction": payload
            }, "predictions")
        
        logger.info(
            "Prediction completed and broadcasted",
            prediction_id=payload.get("prediction_id"),
            correlation_id=event.correlation_id
        )
        
        return True

class MatchEventHandler(EventHandler):
    """Handler for match-related events."""
    
    def __init__(self, live_match_service=None, cache_manager=None):
        self.live_match_service = live_match_service
        self.cache_manager = cache_manager
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in [
            EventType.MATCH_STARTED,
            EventType.MATCH_UPDATED,
            EventType.MATCH_FINISHED
        ]
    
    async def handle(self, event: Event) -> bool:
        try:
            if event.type == EventType.MATCH_STARTED:
                return await self._handle_match_started(event)
            elif event.type == EventType.MATCH_UPDATED:
                return await self._handle_match_updated(event)
            elif event.type == EventType.MATCH_FINISHED:
                return await self._handle_match_finished(event)
            
            return False
            
        except Exception as e:
            logger.error("Error in match event handler", error=str(e))
            return False
    
    async def _handle_match_started(self, event: Event) -> bool:
        """Handle match started event."""
        payload = event.payload
        match_id = payload.get("match_id")
        
        logger.info("Match started", match_id=match_id)
        
        # Initialize live tracking if service available
        if self.live_match_service:
            await self.live_match_service.start_live_match(payload)
        
        return True
    
    async def _handle_match_updated(self, event: Event) -> bool:
        """Handle match update event."""
        payload = event.payload
        match_id = payload.get("match_id")
        
        # Update cache if available
        if self.cache_manager:
            cache_key = f"match:{match_id}"
            await self.cache_manager.set(cache_key, payload, expire=3600)
        
        logger.debug("Match updated", match_id=match_id)
        return True
    
    async def _handle_match_finished(self, event: Event) -> bool:
        """Handle match finished event."""
        payload = event.payload
        match_id = payload.get("match_id")
        
        logger.info("Match finished", match_id=match_id)
        
        # Clean up live tracking
        if self.live_match_service:
            await self.live_match_service.stop_live_match(match_id)
        
        # Invalidate related caches
        if self.cache_manager:
            await self.cache_manager.delete(f"match:{match_id}")
            await self.cache_manager.delete(f"predictions:{match_id}")
        
        return True

class SystemEventHandler(EventHandler):
    """Handler for system-level events."""
    
    def can_handle(self, event_type: EventType) -> bool:
        return event_type in [
            EventType.MODEL_RETRAINED,
            EventType.CACHE_INVALIDATED,
            EventType.SYSTEM_ALERT
        ]
    
    async def handle(self, event: Event) -> bool:
        try:
            if event.type == EventType.MODEL_RETRAINED:
                return await self._handle_model_retrained(event)
            elif event.type == EventType.CACHE_INVALIDATED:
                return await self._handle_cache_invalidated(event)
            elif event.type == EventType.SYSTEM_ALERT:
                return await self._handle_system_alert(event)
            
            return False
            
        except Exception as e:
            logger.error("Error in system event handler", error=str(e))
            return False
    
    async def _handle_model_retrained(self, event: Event) -> bool:
        """Handle model retrained event."""
        payload = event.payload
        model_name = payload.get("model_name")
        accuracy = payload.get("accuracy")
        
        logger.info(
            "Model retrained",
            model_name=model_name,
            accuracy=accuracy
        )
        
        # Could trigger cache invalidation, model deployment, etc.
        return True
    
    async def _handle_cache_invalidated(self, event: Event) -> bool:
        """Handle cache invalidation event."""
        payload = event.payload
        cache_pattern = payload.get("pattern", "*")
        
        logger.info("Cache invalidated", pattern=cache_pattern)
        return True
    
    async def _handle_system_alert(self, event: Event) -> bool:
        """Handle system alert event."""
        payload = event.payload
        alert_level = payload.get("level", "info")
        message = payload.get("message")
        
        logger.log(
            alert_level.upper(),
            "System alert",
            message=message,
            **payload
        )
        
        return True

# Global message queue instance
message_queue = MessageQueue()
