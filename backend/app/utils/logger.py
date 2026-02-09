"""
Simulation Logger: Timeline logging with replay capability
Enables "Here's the exact sequence of decisions" flex
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class SimulationLogger:
    """
    Logs all simulation events for timeline replay.
    Provides the ability to show exact decision sequences.
    """
    
    def __init__(self):
        self.events: List[Dict] = []
        self.start_time: Optional[datetime] = None
        self.current_tick: int = 0
    
    def reset(self):
        """Reset logger for new simulation"""
        self.events = []
        self.start_time = None
        self.current_tick = 0
    
    def start(self):
        """Start logging"""
        self.start_time = datetime.now()
        self.log_event("simulation", "start", {"message": "Simulation started"})
    
    def log_event(
        self,
        category: str,
        event_type: str,
        data: Dict[str, Any],
        agent_id: str = None,
    ):
        """Log a simulation event"""
        event = {
            "id": len(self.events),
            "tick": self.current_tick,
            "timestamp": datetime.now().isoformat(),
            "elapsed_ms": self._get_elapsed_ms(),
            "category": category,
            "type": event_type,
            "agent_id": agent_id,
            "data": data,
        }
        self.events.append(event)
        return event
    
    def _get_elapsed_ms(self) -> int:
        """Get milliseconds since simulation start"""
        if not self.start_time:
            return 0
        return int((datetime.now() - self.start_time).total_seconds() * 1000)
    
    def set_tick(self, tick: int):
        """Update current tick"""
        self.current_tick = tick
    
    # Convenience logging methods
    def log_patient_assignment(self, patient_id: str, hospital_id: str, severity: str):
        """Log patient assignment"""
        return self.log_event(
            "allocation",
            "patient_assigned",
            {
                "patient_id": patient_id,
                "hospital_id": hospital_id,
                "severity": severity,
            }
        )
    
    def log_ambulance_dispatch(self, ambulance_id: str, patient_id: str, hospital_id: str, eta: float):
        """Log ambulance dispatch"""
        return self.log_event(
            "dispatch",
            "ambulance_dispatched",
            {
                "ambulance_id": ambulance_id,
                "patient_id": patient_id,
                "hospital_id": hospital_id,
                "eta_minutes": eta,
            },
            agent_id=ambulance_id,
        )
    
    def log_supply_allocation(self, supply_type: str, quantity: int, hospital_id: str):
        """Log supply allocation"""
        return self.log_event(
            "supply",
            "allocated",
            {
                "supply_type": supply_type,
                "quantity": quantity,
                "destination": hospital_id,
            }
        )
    
    def log_negotiation_round(self, round_num: int, decisions: int, duration_ms: int):
        """Log negotiation round completion"""
        return self.log_event(
            "negotiation",
            "round_complete",
            {
                "round": round_num,
                "decisions_made": decisions,
                "duration_ms": duration_ms,
            }
        )
    
    def log_overload_prevented(self, hospital_id: str, action: str):
        """Log overload prevention"""
        return self.log_event(
            "prevention",
            "overload_prevented",
            {
                "hospital_id": hospital_id,
                "action": action,
            },
            agent_id=hospital_id,
        )
    
    def log_failure(self, failure_type: str, details: str):
        """Log a failure event"""
        return self.log_event(
            "failure",
            failure_type,
            {"details": details}
        )
    
    def log_recovery(self, failure_type: str, resolution: str):
        """Log recovery from failure"""
        return self.log_event(
            "recovery",
            failure_type,
            {"resolution": resolution}
        )
    
    # Query methods
    def get_events_by_tick(self, tick: int) -> List[Dict]:
        """Get all events for a specific tick"""
        return [e for e in self.events if e["tick"] == tick]
    
    def get_events_by_category(self, category: str) -> List[Dict]:
        """Get all events of a category"""
        return [e for e in self.events if e["category"] == category]
    
    def get_events_by_agent(self, agent_id: str) -> List[Dict]:
        """Get all events for a specific agent"""
        return [e for e in self.events if e.get("agent_id") == agent_id]
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Get most recent events"""
        return self.events[-limit:]
    
    def get_timeline(self) -> List[Dict]:
        """Get timeline of events grouped by tick"""
        timeline = {}
        for event in self.events:
            tick = event["tick"]
            if tick not in timeline:
                timeline[tick] = []
            timeline[tick].append(event)
        
        return [
            {"tick": tick, "events": events}
            for tick, events in sorted(timeline.items())
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get logging summary"""
        categories = {}
        for event in self.events:
            cat = event["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_events": len(self.events),
            "total_ticks": self.current_tick,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed_seconds": self._get_elapsed_ms() / 1000,
            "events_by_category": categories,
        }
    
    def export_json(self) -> str:
        """Export all events as JSON"""
        return json.dumps({
            "summary": self.get_summary(),
            "events": self.events,
        }, indent=2, default=str)
    
    def generate_replay_script(self) -> List[str]:
        """Generate human-readable replay of key events"""
        script = []
        
        for event in self.events:
            if event["category"] == "simulation":
                continue
            
            timestamp = event["timestamp"].split("T")[1][:8]
            tick = event["tick"]
            
            if event["category"] == "allocation" and event["type"] == "patient_assigned":
                data = event["data"]
                script.append(
                    f"[Tick {tick}] Patient {data['patient_id']} ({data['severity']}) "
                    f"→ {data['hospital_id']}"
                )
            elif event["category"] == "dispatch":
                data = event["data"]
                script.append(
                    f"[Tick {tick}] 🚑 {data['ambulance_id']} dispatched for "
                    f"{data['patient_id']} (ETA: {data['eta_minutes']}min)"
                )
            elif event["category"] == "prevention":
                data = event["data"]
                script.append(
                    f"[Tick {tick}] ⚠️ Overload prevented at {data['hospital_id']}"
                )
            elif event["category"] == "supply":
                data = event["data"]
                script.append(
                    f"[Tick {tick}] 📦 {data['quantity']} {data['supply_type']} "
                    f"→ {data['destination']}"
                )
        
        return script
