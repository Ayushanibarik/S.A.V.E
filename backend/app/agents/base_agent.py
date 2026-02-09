"""
Base Agent: Abstract base class for all agents in the S.A.V.E system
All agents inherit from this class for consistent interface and behavior
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BaseAgent(ABC):
    """
    Abstract base class defining the common interface for all agents.
    Ensures consistent behavior across Hospital, Ambulance, Supply, and Government agents.
    """
    
    def __init__(self, agent_id: str, agent_type: str, name: str = ""):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.name = name or agent_id
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self._message_queue: List[Dict[str, Any]] = []
        self._action_log: List[Dict[str, Any]] = []
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Return current state of the agent for dashboard display"""
        pass
    
    @abstractmethod
    def generate_message(self) -> Dict[str, Any]:
        """
        Generate a message to broadcast to other agents.
        Message format:
        {
            "agent_id": str,
            "agent_type": str,
            "timestamp": datetime,
            "current_capacity": dict,
            "requests": list,
            "offers": list,
            "priority_score": float
        }
        """
        pass
    
    @abstractmethod
    def receive_message(self, message: Dict[str, Any]) -> None:
        """Process an incoming message from another agent"""
        pass
    
    @abstractmethod
    def update(self, tick: int) -> List[Dict[str, Any]]:
        """
        Update agent state for a simulation tick.
        Returns a list of actions taken.
        """
        pass
    
    @abstractmethod
    def calculate_priority_score(self) -> float:
        """Calculate this agent's priority score for negotiation"""
        pass
    
    def log_action(self, action_type: str, details: Dict[str, Any]) -> None:
        """Log an action for timeline replay"""
        self._action_log.append({
            "timestamp": datetime.now(),
            "agent_id": self.agent_id,
            "action_type": action_type,
            "details": details
        })
    
    def get_action_log(self) -> List[Dict[str, Any]]:
        """Return action history for this agent"""
        return self._action_log.copy()
    
    def queue_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the processing queue"""
        self._message_queue.append(message)
    
    def process_message_queue(self) -> List[Dict[str, Any]]:
        """Process all queued messages and return responses"""
        responses = []
        while self._message_queue:
            msg = self._message_queue.pop(0)
            self.receive_message(msg)
        return responses
    
    def get_base_message(self) -> Dict[str, Any]:
        """Get base message structure with common fields"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "name": self.name,
            "timestamp": datetime.now().isoformat(),
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, name={self.name})"
