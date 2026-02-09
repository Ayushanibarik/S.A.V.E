"""
Government Agent: Authority agent that enforces priorities and overrides
Handles disaster severity, fairness rules, and intervention
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from ..agents.base_agent import BaseAgent
from ..config.constants import (
    AGENT_TYPE_GOVERNMENT,
    WEIGHT_FAIRNESS,
)


class GovernmentAgent(BaseAgent):
    """
    Government/Authority agent that enforces system-wide policies.
    Does not negotiate - it intervenes and overrides when necessary.
    """
    
    def __init__(
        self,
        agent_id: str = "gov_authority",
        disaster_severity: float = 0.5,
        fairness_weight: float = 0.7,
    ):
        super().__init__(agent_id, AGENT_TYPE_GOVERNMENT, "Government Authority")
        
        self.disaster_severity = disaster_severity  # 0.0 to 1.0
        
        # Priority rules
        self.priority_rules = {
            "critical_patients_first": True,
            "balance_hospital_load": True,
            "preserve_oxygen_reserves": True,
            "prioritize_children_elderly": True,
        }
        
        self.fairness_weight = fairness_weight
        
        # Infrastructure status
        self.critical_infrastructure = {
            "power_grid": "operational",
            "water_supply": "operational",
            "communication": "operational",
            "roads": "partially_blocked",
        }
        
        # Policy overrides issued
        self.active_overrides: List[Dict] = []
        self.override_history: List[Dict] = []
        
        # Tracked violations
        self.violations: List[Dict] = []
    
    @property
    def severity_level(self) -> str:
        """Get severity level string"""
        if self.disaster_severity >= 0.8:
            return "critical"
        elif self.disaster_severity >= 0.5:
            return "high"
        elif self.disaster_severity >= 0.3:
            return "medium"
        return "low"
    
    def get_state(self) -> Dict[str, Any]:
        """Return current state for dashboard/API"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "disaster_severity": self.disaster_severity,
            "severity_level": self.severity_level,
            "priority_rules": self.priority_rules,
            "fairness_weight": self.fairness_weight,
            "infrastructure": self.critical_infrastructure,
            "active_overrides": len(self.active_overrides),
            "violations_detected": len(self.violations),
        }
    
    def generate_message(self) -> Dict[str, Any]:
        """Generate policy broadcast message"""
        message = self.get_base_message()
        message.update({
            "message_type": "policy_broadcast",
            "current_capacity": {},
            "requests": [],
            "offers": [],
            "priority_score": 1.0,  # Government always highest priority
            "policies": {
                "disaster_severity": self.disaster_severity,
                "priority_rules": self.priority_rules,
                "fairness_weight": self.fairness_weight,
            },
        })
        return message
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """Process incoming reports and status updates"""
        msg_type = message.get("message_type", "")
        
        if msg_type == "status_update":
            self._evaluate_status(message)
        elif msg_type == "emergency_alert":
            self._handle_emergency(message)
    
    def _evaluate_status(self, message: Dict):
        """Evaluate agent status for policy violations"""
        agent_id = message.get("agent_id")
        capacity = message.get("current_capacity", {})
        
        # Check for fairness violations (e.g., hospital refusing too many patients)
        # This is simplified - in reality would track over time
        pass
    
    def _handle_emergency(self, message: Dict):
        """Handle emergency escalation"""
        self.disaster_severity = min(1.0, self.disaster_severity + 0.1)
        self.log_action("emergency_escalation", {
            "source": message.get("agent_id"),
            "new_severity": self.disaster_severity,
        })
    
    def evaluate_allocation(self, allocation: Dict, hospitals: Dict) -> Dict[str, Any]:
        """Evaluate if an allocation plan meets government priorities"""
        evaluation = {
            "approved": True,
            "modifications": [],
            "warnings": [],
        }
        
        # Check fairness - ensure load is balanced
        if self.priority_rules.get("balance_hospital_load"):
            loads = []
            for h_id, h_state in hospitals.items():
                utilization = 1 - (h_state.get("available_beds", 0) / max(h_state.get("total_beds", 1), 1))
                loads.append((h_id, utilization))
            
            if loads:
                max_load = max(l[1] for l in loads)
                min_load = min(l[1] for l in loads)
                
                if max_load - min_load > 0.4:  # More than 40% difference
                    evaluation["warnings"].append({
                        "type": "load_imbalance",
                        "message": f"Hospital load imbalance detected ({round(max_load*100)}% vs {round(min_load*100)}%)",
                        "recommendation": "Redirect patients to underutilized hospitals",
                    })
        
        # Check oxygen preservation
        if self.priority_rules.get("preserve_oxygen_reserves"):
            for h_id, h_state in hospitals.items():
                if h_state.get("oxygen_units", 0) < 20:
                    evaluation["warnings"].append({
                        "type": "oxygen_critical",
                        "hospital": h_id,
                        "message": f"Critical oxygen shortage at {h_id}",
                        "recommendation": "Emergency oxygen resupply required",
                    })
        
        return evaluation
    
    def calculate_priority_multipliers(self, hospitals: Dict) -> Dict[str, float]:
        """Calculate priority multipliers for each hospital based on policies"""
        multipliers = {}
        
        for h_id, h_state in hospitals.items():
            base = 1.0
            
            # Boost priority for critical hospitals
            if h_state.get("is_critical"):
                base *= 1.5
            
            # Boost for low oxygen
            if h_state.get("oxygen_units", 100) < 30:
                base *= 1.3
            
            # Reduce priority if already getting many resources (fairness)
            # This is simplified
            
            multipliers[h_id] = base
        
        return multipliers
    
    def issue_override(self, override_type: str, target_agent: str, directive: Dict) -> Dict:
        """Issue a policy override to an agent"""
        override = {
            "id": f"override_{len(self.override_history):03d}",
            "type": override_type,
            "target": target_agent,
            "directive": directive,
            "issued_at": datetime.now().isoformat(),
            "status": "active",
        }
        
        self.active_overrides.append(override)
        
        self.log_action("override_issued", override)
        
        return {
            "agent_id": self.agent_id,
            "message_type": "priority_override",
            "override": override,
        }
    
    def update(self, tick: int) -> List[Dict[str, Any]]:
        """Update government agent state"""
        actions = []
        
        # Gradually reduce severity if situation improving
        # (In real scenario would be based on actual conditions)
        if tick % 10 == 0 and self.disaster_severity > 0.3:
            self.disaster_severity = max(0.3, self.disaster_severity - 0.02)
        
        # Clear expired overrides
        expired = [o for o in self.active_overrides if o.get("status") == "completed"]
        for o in expired:
            self.active_overrides.remove(o)
            self.override_history.append(o)
        
        self.last_updated = datetime.now()
        return actions
    
    def calculate_priority_score(self) -> float:
        """Government always has highest priority"""
        return 1.0
    
    def generate_situation_report(self, hospitals: Dict, ambulances: Dict, supply: Dict) -> Dict[str, Any]:
        """Generate a situation report for the dashboard"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "disaster_severity": self.disaster_severity,
            "severity_level": self.severity_level,
            "infrastructure": self.critical_infrastructure,
            "hospital_summary": {
                "total": len(hospitals),
                "critical": sum(1 for h in hospitals.values() if h.get("is_critical")),
                "overloaded": sum(1 for h in hospitals.values() if h.get("is_overloaded")),
            },
            "ambulance_summary": {
                "total": len(ambulances),
                "available": sum(1 for a in ambulances.values() if a.get("available")),
                "en_route": sum(1 for a in ambulances.values() if a.get("status") != "idle"),
            },
            "active_policies": list(k for k, v in self.priority_rules.items() if v),
            "active_overrides": len(self.active_overrides),
        }
        
        return report
