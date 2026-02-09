"""
Message Schema: Pydantic models for agent communication
Ensures consistent message format across all agent interactions
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    STATUS_UPDATE = "status_update"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_OFFER = "resource_offer"
    PATIENT_ASSIGNMENT = "patient_assignment"
    SUPPLY_ALLOCATION = "supply_allocation"
    PRIORITY_OVERRIDE = "priority_override"
    EMERGENCY_ALERT = "emergency_alert"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentMessage(BaseModel):
    """Standard message format for agent communication"""
    agent_id: str
    agent_type: str
    message_type: MessageType
    timestamp: datetime = Field(default_factory=datetime.now)
    current_capacity: Dict[str, Any] = Field(default_factory=dict)
    requests: List[Dict[str, Any]] = Field(default_factory=list)
    offers: List[Dict[str, Any]] = Field(default_factory=list)
    priority_score: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class RequestMessage(BaseModel):
    """Resource request from an agent"""
    request_id: str
    requester_id: str
    resource_type: str  # "beds", "oxygen", "ambulance", "supplies"
    quantity: int
    urgency: SeverityLevel = SeverityLevel.MEDIUM
    reason: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class AllocationMessage(BaseModel):
    """Resource allocation decision"""
    allocation_id: str
    from_agent: str
    to_agent: str
    resource_type: str
    quantity: int
    priority: float
    explanation: str
    timestamp: datetime = Field(default_factory=datetime.now)


class PatientAssignment(BaseModel):
    """Patient assignment to hospital via ambulance"""
    patient_id: str
    severity: SeverityLevel
    ambulance_id: str
    source_location: tuple
    destination_hospital: str
    eta_minutes: float
    assigned_at: datetime = Field(default_factory=datetime.now)


class SupplyDelivery(BaseModel):
    """Supply delivery assignment"""
    delivery_id: str
    supply_type: str
    quantity: int
    from_depot: str
    to_hospital: str
    eta_minutes: float
    priority: SeverityLevel = SeverityLevel.MEDIUM
