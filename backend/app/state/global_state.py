"""
Global State: Single source of truth for the entire system
Enables before/after comparison, metrics calculation, and timeline replay
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from copy import deepcopy
import json


class GlobalState:
    """
    Centralized state store for the S.A.V.E system.
    Maintains snapshots for before/after comparison.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - one global state for the entire system"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.current_tick: int = 0
        self.simulation_started: Optional[datetime] = None
        self.simulation_status: str = "idle"  # idle, running, paused, completed
        
        # Agent states (keyed by agent_id)
        self.hospitals: Dict[str, Dict[str, Any]] = {}
        self.ambulances: Dict[str, Dict[str, Any]] = {}
        self.supply: Dict[str, Any] = {}
        self.government: Dict[str, Any] = {}
        
        # Patient tracking
        self.patients: Dict[str, Dict[str, Any]] = {}
        self.served_patients: List[str] = []
        self.unserved_critical: List[str] = []
        
        # Decision history
        self.decisions: List[Dict[str, Any]] = []
        self.allocations: List[Dict[str, Any]] = []
        
        # Snapshots for before/after comparison
        self._snapshots: List[Dict[str, Any]] = []
        self._before_state: Optional[Dict[str, Any]] = None
        
        # Metrics
        self.metrics: Dict[str, Any] = {
            "lives_saved": 0,
            "total_patients_served": 0,
            "critical_patients_served": 0,
            "average_response_time": 0.0,
            "overloads_avoided": 0,
            "supplies_delivered": 0,
            "total_response_times": [],
        }
        
        self._initialized = True
    
    def reset(self):
        """Reset the global state for a new simulation"""
        self.current_tick = 0
        self.simulation_started = None
        self.simulation_status = "idle"
        self.hospitals = {}
        self.ambulances = {}
        self.supply = {}
        self.government = {}
        self.patients = {}
        self.served_patients = []
        self.unserved_critical = []
        self.decisions = []
        self.allocations = []
        self._snapshots = []
        self._before_state = None
        self.metrics = {
            "lives_saved": 0,
            "total_patients_served": 0,
            "critical_patients_served": 0,
            "average_response_time": 0.0,
            "overloads_avoided": 0,
            "supplies_delivered": 0,
            "total_response_times": [],
        }
    
    def start_simulation(self):
        """Mark simulation as started"""
        self.simulation_started = datetime.now()
        self.simulation_status = "running"
        self.take_snapshot("simulation_start")
    
    def take_snapshot(self, label: str = "") -> Dict[str, Any]:
        """Take a snapshot of current state for comparison"""
        snapshot = {
            "label": label,
            "tick": self.current_tick,
            "timestamp": datetime.now().isoformat(),
            "hospitals": deepcopy(self.hospitals),
            "ambulances": deepcopy(self.ambulances),
            "supply": deepcopy(self.supply),
            "metrics": deepcopy(self.metrics),
            "unserved_critical_count": len(self.unserved_critical),
        }
        self._snapshots.append(snapshot)
        return snapshot
    
    def save_before_state(self):
        """Save state before negotiation/optimization for comparison"""
        self._before_state = self.take_snapshot("before_optimization")
    
    def get_before_after_comparison(self) -> Dict[str, Any]:
        """Get before/after comparison of the last optimization"""
        if not self._before_state:
            return {"error": "No before state saved"}
        
        after_state = self.take_snapshot("after_optimization")
        
        return {
            "before": self._before_state,
            "after": after_state,
            "changes": self._calculate_changes(self._before_state, after_state)
        }
    
    def _calculate_changes(self, before: Dict, after: Dict) -> Dict[str, Any]:
        """Calculate what changed between two states"""
        changes = {
            "patients_served_delta": after["metrics"]["total_patients_served"] - before["metrics"]["total_patients_served"],
            "critical_served_delta": after["metrics"]["critical_patients_served"] - before["metrics"]["critical_patients_served"],
            "overloads_avoided_delta": after["metrics"]["overloads_avoided"] - before["metrics"]["overloads_avoided"],
            "hospital_changes": [],
        }
        
        for h_id, h_state in after["hospitals"].items():
            if h_id in before["hospitals"]:
                b_state = before["hospitals"][h_id]
                if h_state.get("available_beds", 0) != b_state.get("available_beds", 0):
                    changes["hospital_changes"].append({
                        "hospital_id": h_id,
                        "beds_before": b_state.get("available_beds", 0),
                        "beds_after": h_state.get("available_beds", 0),
                    })
        
        return changes
    
    def update_hospital(self, hospital_id: str, state: Dict[str, Any]):
        """Update a hospital's state"""
        self.hospitals[hospital_id] = state
    
    def update_ambulance(self, ambulance_id: str, state: Dict[str, Any]):
        """Update an ambulance's state"""
        self.ambulances[ambulance_id] = state
    
    def update_supply(self, state: Dict[str, Any]):
        """Update supply chain state"""
        self.supply = state
    
    def update_government(self, state: Dict[str, Any]):
        """Update government agent state"""
        self.government = state
    
    def add_decision(self, decision: Dict[str, Any]):
        """Add a decision to the log"""
        decision["tick"] = self.current_tick
        decision["timestamp"] = datetime.now().isoformat()
        self.decisions.append(decision)
    
    def add_allocation(self, allocation: Dict[str, Any]):
        """Add an allocation to the log"""
        allocation["tick"] = self.current_tick
        allocation["timestamp"] = datetime.now().isoformat()
        self.allocations.append(allocation)
    
    def mark_patient_served(self, patient_id: str, was_critical: bool = False):
        """Mark a patient as served"""
        self.served_patients.append(patient_id)
        self.metrics["total_patients_served"] += 1
        if was_critical:
            self.metrics["critical_patients_served"] += 1
            self.metrics["lives_saved"] += 1
            if patient_id in self.unserved_critical:
                self.unserved_critical.remove(patient_id)
    
    def add_response_time(self, response_time: float):
        """Add a response time measurement"""
        self.metrics["total_response_times"].append(response_time)
        if self.metrics["total_response_times"]:
            self.metrics["average_response_time"] = sum(self.metrics["total_response_times"]) / len(self.metrics["total_response_times"])
    
    def record_overload_avoided(self):
        """Record that an overload was avoided"""
        self.metrics["overloads_avoided"] += 1
    
    def increment_tick(self):
        """Move to next simulation tick"""
        self.current_tick += 1
    
    def get_full_state(self) -> Dict[str, Any]:
        """Get complete system state for API response"""
        return {
            "tick": self.current_tick,
            "status": self.simulation_status,
            "started_at": self.simulation_started.isoformat() if self.simulation_started else None,
            "hospitals": self.hospitals,
            "ambulances": self.ambulances,
            "supply": self.supply,
            "government": self.government,
            "metrics": self.metrics,
            "unserved_critical_count": len(self.unserved_critical),
            "total_patients": len(self.patients),
            "served_patients": len(self.served_patients),
        }
    
    def get_recent_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent decisions for the dashboard"""
        return self.decisions[-limit:]
    
    def export_state(self) -> str:
        """Export full state as JSON"""
        return json.dumps(self.get_full_state(), indent=2, default=str)
