"""
Constraints: Enforces system constraints on allocations
Prevents invalid states like negative beds or over-capacity ambulances
"""

from typing import Dict, List, Any, Tuple
from ..config.constants import (
    OXYGEN_CRITICAL_LEVEL,
    AMBULANCE_CAPACITY,
)


class ConstraintChecker:
    """
    Constraint checker that validates allocation decisions.
    Ensures no allocation violates system constraints.
    """
    
    def __init__(self):
        self.violations: List[Dict] = []
    
    def reset(self):
        """Reset violations for new round"""
        self.violations = []
    
    def check_all_constraints(
        self,
        hospitals: Dict[str, Dict],
        ambulances: Dict[str, Dict],
        supply: Dict,
        proposed_allocations: List[Dict],
    ) -> Tuple[bool, List[Dict]]:
        """
        Check all constraints against proposed allocations.
        Returns (is_valid, list_of_violations)
        """
        self.reset()
        
        # Check hospital constraints
        self._check_hospital_constraints(hospitals)
        
        # Check ambulance constraints
        self._check_ambulance_constraints(ambulances)
        
        # Check supply constraints
        self._check_supply_constraints(supply)
        
        # Check allocation-specific constraints
        for allocation in proposed_allocations:
            self._check_allocation_constraints(allocation, hospitals, ambulances)
        
        is_valid = len(self.violations) == 0
        return is_valid, self.violations
    
    def _check_hospital_constraints(self, hospitals: Dict[str, Dict]):
        """Check hospital capacity constraints"""
        for h_id, h_state in hospitals.items():
            # Bed capacity cannot be negative
            if h_state.get("available_beds", 0) < 0:
                self.violations.append({
                    "type": "hospital_capacity",
                    "agent": h_id,
                    "constraint": "available_beds >= 0",
                    "actual": h_state.get("available_beds"),
                    "severity": "critical",
                })
            
            # ICU cannot be negative
            if h_state.get("icu_available", 0) < 0:
                self.violations.append({
                    "type": "hospital_icu",
                    "agent": h_id,
                    "constraint": "icu_available >= 0",
                    "actual": h_state.get("icu_available"),
                    "severity": "critical",
                })
            
            # Oxygen warning (soft constraint)
            if h_state.get("oxygen_units", 100) < OXYGEN_CRITICAL_LEVEL:
                self.violations.append({
                    "type": "hospital_oxygen",
                    "agent": h_id,
                    "constraint": f"oxygen >= {OXYGEN_CRITICAL_LEVEL}",
                    "actual": h_state.get("oxygen_units"),
                    "severity": "warning",
                })
    
    def _check_ambulance_constraints(self, ambulances: Dict[str, Dict]):
        """Check ambulance capacity constraints"""
        for a_id, a_state in ambulances.items():
            current_load = a_state.get("current_load", 0)
            capacity = a_state.get("capacity", AMBULANCE_CAPACITY)
            
            # Cannot exceed capacity
            if current_load > capacity:
                self.violations.append({
                    "type": "ambulance_capacity",
                    "agent": a_id,
                    "constraint": f"load <= {capacity}",
                    "actual": current_load,
                    "severity": "critical",
                })
            
            # Fuel warning
            if a_state.get("fuel", 100) < 15:
                self.violations.append({
                    "type": "ambulance_fuel",
                    "agent": a_id,
                    "constraint": "fuel >= 15%",
                    "actual": a_state.get("fuel"),
                    "severity": "warning",
                })
    
    def _check_supply_constraints(self, supply: Dict):
        """Check supply inventory constraints"""
        inventory = supply.get("inventory", {})
        
        for supply_type, quantity in inventory.items():
            if quantity < 0:
                self.violations.append({
                    "type": "supply_inventory",
                    "resource": supply_type,
                    "constraint": f"{supply_type} >= 0",
                    "actual": quantity,
                    "severity": "critical",
                })
    
    def _check_allocation_constraints(
        self,
        allocation: Dict,
        hospitals: Dict,
        ambulances: Dict,
    ):
        """Check constraints on a specific allocation"""
        allocation_type = allocation.get("type")
        
        if allocation_type == "patient_assignment":
            hospital_id = allocation.get("assigned_hospital")
            patient_severity = allocation.get("patient_severity")
            
            if hospital_id and hospital_id in hospitals:
                h_state = hospitals[hospital_id]
                
                # Critical patients need ICU
                if patient_severity == "critical" and h_state.get("icu_available", 0) <= 0:
                    self.violations.append({
                        "type": "allocation_invalid",
                        "allocation": allocation,
                        "constraint": "Critical patient needs ICU",
                        "reason": "No ICU available",
                        "severity": "critical",
                    })
                
                # Regular patients need beds
                elif patient_severity != "critical" and h_state.get("available_beds", 0) <= 0:
                    self.violations.append({
                        "type": "allocation_invalid",
                        "allocation": allocation,
                        "constraint": "Patient needs available bed",
                        "reason": "No beds available",
                        "severity": "critical",
                    })
    
    def get_violations_summary(self) -> Dict[str, Any]:
        """Get summary of all violations"""
        critical = [v for v in self.violations if v.get("severity") == "critical"]
        warnings = [v for v in self.violations if v.get("severity") == "warning"]
        
        return {
            "total_violations": len(self.violations),
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "is_valid": len(critical) == 0,
            "critical_violations": critical,
            "warnings": warnings,
        }
    
    def filter_valid_allocations(
        self,
        proposed: List[Dict],
        hospitals: Dict,
        ambulances: Dict,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter allocations to only those that satisfy constraints.
        Returns (valid_allocations, rejected_allocations)
        """
        valid = []
        rejected = []
        
        # Track remaining capacity
        remaining_beds = {h_id: h.get("available_beds", 0) for h_id, h in hospitals.items()}
        remaining_icu = {h_id: h.get("icu_available", 0) for h_id, h in hospitals.items()}
        
        for allocation in proposed:
            hospital_id = allocation.get("assigned_hospital")
            severity = allocation.get("patient_severity")
            
            if severity == "critical":
                if remaining_icu.get(hospital_id, 0) > 0:
                    remaining_icu[hospital_id] -= 1
                    valid.append(allocation)
                else:
                    allocation["rejection_reason"] = "No ICU capacity"
                    rejected.append(allocation)
            else:
                if remaining_beds.get(hospital_id, 0) > 0:
                    remaining_beds[hospital_id] -= 1
                    valid.append(allocation)
                else:
                    allocation["rejection_reason"] = "No bed capacity"
                    rejected.append(allocation)
        
        return valid, rejected
