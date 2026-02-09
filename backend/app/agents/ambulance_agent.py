"""
Ambulance Agent: Manages ambulance routing and patient transport
Handles capacity, ETA calculations, and dynamic rerouting
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math
from ..agents.base_agent import BaseAgent
from ..config.constants import (
    AMBULANCE_CAPACITY,
    AMBULANCE_SPEED,
    FUEL_CRITICAL_LEVEL,
    AGENT_TYPE_AMBULANCE,
)


class AmbulanceAgent(BaseAgent):
    """
    Ambulance agent that handles patient pickup, hospital routing, and delivery.
    Makes decisions on optimal hospital selection based on ETA and availability.
    """
    
    def __init__(
        self,
        agent_id: str,
        location: Tuple[float, float],
        capacity: int = AMBULANCE_CAPACITY,
        fuel: float = 1.0,
        available: bool = True,
    ):
        super().__init__(agent_id, AGENT_TYPE_AMBULANCE, agent_id.upper())
        
        self.location = location
        self.capacity = capacity
        self.current_patients: List[Dict] = []
        self.fuel = fuel  # 0.0 to 1.0
        self.available = available
        self.status = "idle"  # idle, en_route_pickup, en_route_hospital, returning
        
        # Current mission
        self.target_patient: Optional[Dict] = None
        self.target_hospital: Optional[str] = None
        self.destination: Optional[Tuple[float, float]] = None
        self.eta_minutes: float = 0.0
        
        # History
        self.patients_delivered: int = 0
        self.total_distance: float = 0.0
    
    @property
    def is_available(self) -> bool:
        """Check if ambulance is available for new assignments"""
        return (
            self.available and 
            self.status == "idle" and 
            len(self.current_patients) < self.capacity and
            self.fuel > FUEL_CRITICAL_LEVEL
        )
    
    @property
    def fuel_status(self) -> str:
        """Get fuel status level"""
        if self.fuel < FUEL_CRITICAL_LEVEL:
            return "critical"
        elif self.fuel < 0.3:
            return "low"
        else:
            return "ok"
    
    def get_state(self) -> Dict[str, Any]:
        """Return current state for dashboard/API"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "location": self.location,
            "capacity": self.capacity,
            "current_load": len(self.current_patients),
            "fuel": round(self.fuel * 100, 1),
            "fuel_status": self.fuel_status,
            "status": self.status,
            "available": self.is_available,
            "target_hospital": self.target_hospital,
            "eta_minutes": round(self.eta_minutes, 1),
            "patients_delivered": self.patients_delivered,
        }
    
    def generate_message(self) -> Dict[str, Any]:
        """Generate status message for negotiation"""
        message = self.get_base_message()
        message.update({
            "message_type": "status_update",
            "current_capacity": {
                "available_slots": self.capacity - len(self.current_patients),
                "fuel_level": self.fuel,
            },
            "requests": self._generate_requests(),
            "offers": self._generate_offers(),
            "priority_score": self.calculate_priority_score(),
        })
        return message
    
    def _generate_requests(self) -> List[Dict]:
        """Generate requests (e.g., fuel if low)"""
        requests = []
        if self.fuel < 0.3:
            requests.append({
                "resource": "fuel",
                "urgency": "high" if self.fuel < FUEL_CRITICAL_LEVEL else "medium",
            })
        return requests
    
    def _generate_offers(self) -> List[Dict]:
        """Generate offers to transport patients"""
        offers = []
        if self.is_available:
            offers.append({
                "resource": "patient_transport",
                "capacity": self.capacity - len(self.current_patients),
                "location": self.location,
            })
        return offers
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """Process incoming message"""
        msg_type = message.get("message_type", "")
        
        if msg_type == "patient_assignment":
            self._handle_patient_assignment(message)
        elif msg_type == "reroute":
            self._handle_reroute(message)
    
    def _handle_patient_assignment(self, message: Dict):
        """Handle new patient pickup assignment"""
        patient = message.get("patient")
        hospital_id = message.get("hospital_id")
        hospital_location = message.get("hospital_location")
        
        if self.is_available and patient:
            self.assign_mission(patient, hospital_id, hospital_location)
    
    def _handle_reroute(self, message: Dict):
        """Handle rerouting to different hospital"""
        new_hospital = message.get("hospital_id")
        new_location = message.get("hospital_location")
        reason = message.get("reason", "capacity change")
        
        old_hospital = self.target_hospital
        self.target_hospital = new_hospital
        self.destination = new_location
        self._calculate_eta()
        
        self.log_action("rerouted", {
            "from_hospital": old_hospital,
            "to_hospital": new_hospital,
            "reason": reason,
        })
    
    def assign_mission(self, patient: Dict, hospital_id: str, hospital_location: Tuple):
        """Assign a patient pickup and delivery mission"""
        self.target_patient = patient
        self.target_hospital = hospital_id
        self.status = "en_route_pickup"
        self.destination = patient.get("location")
        self._calculate_eta()
        
        self.log_action("mission_assigned", {
            "patient_id": patient.get("id"),
            "target_hospital": hospital_id,
            "eta": self.eta_minutes,
        })
    
    def _calculate_eta(self):
        """Calculate ETA to current destination"""
        if self.destination:
            distance = self._calculate_distance(self.location, self.destination)
            self.eta_minutes = (distance / AMBULANCE_SPEED) * 60
    
    def _calculate_distance(self, from_loc: Tuple, to_loc: Tuple) -> float:
        """Calculate distance between two points"""
        return math.sqrt(
            (to_loc[0] - from_loc[0])**2 + 
            (to_loc[1] - from_loc[1])**2
        )
    
    def calculate_eta_to_hospital(self, hospital_location: Tuple, patient_location: Tuple = None) -> float:
        """Calculate total ETA: current position -> patient -> hospital"""
        if patient_location:
            pickup_distance = self._calculate_distance(self.location, patient_location)
            delivery_distance = self._calculate_distance(patient_location, hospital_location)
            total_distance = pickup_distance + delivery_distance
        else:
            total_distance = self._calculate_distance(self.location, hospital_location)
        
        return (total_distance / AMBULANCE_SPEED) * 60
    
    def update(self, tick: int) -> List[Dict[str, Any]]:
        """Update ambulance state for a simulation tick"""
        actions = []
        
        if self.status == "en_route_pickup" and self.destination:
            # Move toward patient
            arrived = self._move_toward(self.destination)
            if arrived:
                # Pick up patient
                if self.target_patient:
                    self.current_patients.append(self.target_patient)
                    self.status = "en_route_hospital"
                    # Now head to hospital - destination will be set by orchestrator
                    actions.append({
                        "type": "patient_picked_up",
                        "patient_id": self.target_patient.get("id"),
                        "ambulance_id": self.agent_id,
                    })
        
        elif self.status == "en_route_hospital" and self.destination:
            # Move toward hospital
            arrived = self._move_toward(self.destination)
            if arrived:
                # Deliver patients
                for patient in self.current_patients:
                    self.patients_delivered += 1
                    actions.append({
                        "type": "patient_delivered",
                        "patient_id": patient.get("id"),
                        "hospital_id": self.target_hospital,
                        "ambulance_id": self.agent_id,
                    })
                
                self.current_patients = []
                self.target_patient = None
                self.target_hospital = None
                self.status = "idle"
                self.destination = None
        
        # Consume fuel
        if self.status != "idle":
            self.fuel = max(0, self.fuel - 0.02)
        
        self.last_updated = datetime.now()
        return actions
    
    def _move_toward(self, target: Tuple, speed_factor: float = 5.0) -> bool:
        """Move toward target location, return True if arrived"""
        dx = target[0] - self.location[0]
        dy = target[1] - self.location[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < speed_factor:
            self.location = target
            return True
        
        # Move proportionally
        ratio = speed_factor / distance
        new_x = self.location[0] + dx * ratio
        new_y = self.location[1] + dy * ratio
        self.location = (new_x, new_y)
        self.total_distance += speed_factor
        
        self._calculate_eta()
        return False
    
    def calculate_priority_score(self) -> float:
        """Calculate priority score for negotiation"""
        score = 0.5
        
        # Higher priority if currently transporting critical patient
        for patient in self.current_patients:
            if patient.get("severity") == "critical":
                score += 0.3
                break
        
        # Lower priority if low fuel
        if self.fuel < FUEL_CRITICAL_LEVEL:
            score -= 0.2
        
        return max(0, min(1, score))
