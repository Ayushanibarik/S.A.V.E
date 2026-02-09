"""
Event Bus: Central message router for agent communication
Provides publish/subscribe pattern with timestamped logging
"""

from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from collections import defaultdict
import json


class EventBus:
    """
    Central message router that enables decoupled agent communication.
    Features:
    - Publish/subscribe pattern
    - Message history for replay
    - Topic-based routing
    - Timestamped logging
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - one event bus for the entire system"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._message_history: List[Dict[str, Any]] = []
        self._agent_registry: Dict[str, Any] = {}
        self._initialized = True
    
    def reset(self):
        """Reset the event bus (for new simulation)"""
        self._subscribers = defaultdict(list)
        self._message_history = []
        self._agent_registry = {}
    
    def register_agent(self, agent_id: str, agent: Any) -> None:
        """Register an agent with the event bus"""
        self._agent_registry[agent_id] = agent
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Get a registered agent by ID"""
        return self._agent_registry.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, Any]:
        """Get all registered agents"""
        return self._agent_registry.copy()
    
    def subscribe(self, topic: str, callback: Callable) -> None:
        """Subscribe to a topic with a callback function"""
        self._subscribers[topic].append(callback)
    
    def unsubscribe(self, topic: str, callback: Callable) -> None:
        """Unsubscribe from a topic"""
        if callback in self._subscribers[topic]:
            self._subscribers[topic].remove(callback)
    
    def publish(self, topic: str, message: Dict[str, Any], sender_id: str = "") -> None:
        """
        Publish a message to a topic.
        All subscribers will receive the message.
        """
        timestamped_message = {
            "topic": topic,
            "sender_id": sender_id,
            "timestamp": datetime.now().isoformat(),
            "payload": message
        }
        
        # Log the message
        self._message_history.append(timestamped_message)
        
        # Notify all subscribers
        for callback in self._subscribers[topic]:
            try:
                callback(message)
            except Exception as e:
                print(f"Error in subscriber callback: {e}")
    
    def broadcast(self, message: Dict[str, Any], sender_id: str = "", exclude: List[str] = None) -> None:
        """
        Broadcast a message to all registered agents.
        Optionally exclude certain agents.
        """
        exclude = exclude or []
        
        for agent_id, agent in self._agent_registry.items():
            if agent_id not in exclude and agent_id != sender_id:
                if hasattr(agent, 'receive_message'):
                    agent.receive_message(message)
        
        # Log broadcast
        self._message_history.append({
            "type": "broadcast",
            "sender_id": sender_id,
            "timestamp": datetime.now().isoformat(),
            "payload": message,
            "excluded": exclude
        })
    
    def get_message_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent message history"""
        return self._message_history[-limit:]
    
    def get_messages_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all messages sent by a specific agent"""
        return [
            msg for msg in self._message_history 
            if msg.get("sender_id") == agent_id
        ]
    
    def get_messages_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific topic"""
        return [
            msg for msg in self._message_history 
            if msg.get("topic") == topic
        ]
    
    def export_history(self) -> str:
        """Export message history as JSON for timeline replay"""
        return json.dumps(self._message_history, indent=2, default=str)
