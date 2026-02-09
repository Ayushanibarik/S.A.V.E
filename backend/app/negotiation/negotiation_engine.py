"""
Negotiation Engine: Resolves conflicts between agent bids
Handles resource allocation through weighted scoring
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import math


class NegotiationEngine:
    """
    Negotiation engine that resolves conflicts between agent requests and offers.
    Uses weighted scoring to make allocation decisions.
    """
    
    def __init__(self):
        self.negotiation_rounds: List[Dict] = []
        self.current_round: int = 0
        self.allocation_history: List[Dict] = []
    
    def reset(self):
        """Reset for new simulation"""
        self.negotiation_rounds = []
        self.current_round = 0
        self.allocation_history = []
    
    def run_negotiation(
        self,
        hospital_messages: List[Dict],
        ambulance_messages: List[Dict],
        supply_message: Dict,
        government_priorities: Dict,
        waiting_patients: List[Dict],
    ) -> Dict[str, Any]:
        """
        Run a negotiation round to determine resource allocations.
        Returns allocation decisions.
        """
        self.current_round += 1
        
        round_result = {
            "round": self.current_round,
            "timestamp": datetime.now().isoformat(),
            "patient_assignments": [],
            "supply_allocations": [],
            "ambulance_assignments": [],
            "decisions_explained": [],
        }
        
        # Step 1: Match patients to hospitals based on capacity and priority
        patient_assignments = self._assign_patients_to_hospitals(
            waiting_patients,
            hospital_messages,
            ambulance_messages,
            government_priorities,
        )
        round_result["patient_assignments"] = patient_assignments
        
        # Step 2: Allocate supplies based on hospital requests
        supply_allocations = self._allocate_supplies(
            hospital_messages,
            supply_message,
            government_priorities,
        )
        round_result["supply_allocations"] = supply_allocations
        
        # Step 3: Assign ambulances to patients
        ambulance_assignments = self._assign_ambulances(
            patient_assignments,
            ambulance_messages,
            hospital_messages,
        )
        round_result["ambulance_assignments"] = ambulance_assignments
        
        # Generate explanations
        round_result["decisions_explained"] = self._generate_explanations(round_result)
        
        self.negotiation_rounds.append(round_result)
        return round_result
    
    def _assign_patients_to_hospitals(
        self,
        patients: List[Dict],
        hospitals: List[Dict],
        ambulances: List[Dict],
        priorities: Dict,
    ) -> List[Dict]:
        """Assign patients to hospitals based on capacity and priority"""
        assignments = []
        
        # Sort patients by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_patients = sorted(
            patients,
            key=lambda p: severity_order.get(p.get("severity", "medium"), 2)
        )
        
        # Build hospital capacity map
        hospital_capacity = {}
        for h in hospitals:
            h_id = h.get("agent_id")
            capacity = h.get("current_capacity", {})
            hospital_capacity[h_id] = {
                "beds": capacity.get("available_beds", 0),
                "icu": capacity.get("icu_available", 0),
                "location": h.get("location", (50, 50)),
                "priority_score": h.get("priority_score", 0.5),
                "name": h.get("name", h_id),
            }
        
        for patient in sorted_patients[:10]:  # Process up to 10 patients per round
            best_hospital = self._find_best_hospital(
                patient,
                hospital_capacity,
                priorities,
            )
            
            if best_hospital:
                assignment = {
                    "patient_id": patient.get("id"),
                    "patient_severity": patient.get("severity"),
                    "patient_location": patient.get("location"),
                    "assigned_hospital": best_hospital["id"],
                    "hospital_name": best_hospital["name"],
                    "score": best_hospital["score"],
                    "reason": best_hospital["reason"],
                }
                assignments.append(assignment)
                
                # Update capacity tracking
                if patient.get("severity") == "critical":
                    hospital_capacity[best_hospital["id"]]["icu"] -= 1
                else:
                    hospital_capacity[best_hospital["id"]]["beds"] -= 1
        
        return assignments
    
    def _find_best_hospital(
        self,
        patient: Dict,
        hospital_capacity: Dict,
        priorities: Dict,
    ) -> Optional[Dict]:
        """Find the best hospital for a patient"""
        patient_loc = patient.get("location", (50, 50))
        patient_severity = patient.get("severity", "medium")
        
        candidates = []
        
        for h_id, h_data in hospital_capacity.items():
            # Check capacity
            if patient_severity == "critical":
                if h_data["icu"] <= 0:
                    continue
            else:
                if h_data["beds"] <= 0:
                    continue
            
            # Calculate score
            # Lower distance = better (normalized)
            distance = self._calculate_distance(patient_loc, h_data["location"])
            distance_score = max(0, 1 - (distance / 100))
            
            # Capacity score (prefer hospitals with more capacity)
            capacity_score = (h_data["beds"] + h_data["icu"] * 2) / 50
            capacity_score = min(1, capacity_score)
            
            # Government priority adjustment
            priority_mult = priorities.get("multipliers", {}).get(h_id, 1.0)
            
            # Final score
            total_score = (
                distance_score * 0.4 +
                capacity_score * 0.4 +
                (1 - h_data["priority_score"]) * 0.2  # Lower priority_score = less stressed
            ) * priority_mult
            
            candidates.append({
                "id": h_id,
                "name": h_data["name"],
                "score": total_score,
                "distance": distance,
                "capacity": h_data["beds"],
                "reason": f"Distance: {round(distance, 1)}km, Capacity: {h_data['beds']} beds",
            })
        
        if candidates:
            best = max(candidates, key=lambda c: c["score"])
            return best
        
        return None
    
    def _allocate_supplies(
        self,
        hospitals: List[Dict],
        supply: Dict,
        priorities: Dict,
    ) -> List[Dict]:
        """Allocate supplies to hospitals based on requests and priority"""
        allocations = []
        
        # Collect all requests
        all_requests = []
        for h in hospitals:
            for req in h.get("requests", []):
                all_requests.append({
                    **req,
                    "hospital_id": h.get("agent_id"),
                    "hospital_name": h.get("name"),
                    "hospital_priority": h.get("priority_score", 0.5),
                })
        
        # Sort by urgency and priority
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_requests.sort(
            key=lambda r: (
                urgency_order.get(r.get("urgency", "medium"), 2),
                -r.get("hospital_priority", 0)
            )
        )
        
        # Available supplies
        available = supply.get("current_capacity", {}).get("inventory", {})
        
        for req in all_requests[:5]:  # Process up to 5 requests per round
            resource = req.get("resource")
            if resource == "ambulance_diversion":
                continue  # Handle separately
            
            quantity = req.get("quantity", 10)
            available_qty = available.get(resource, 0)
            
            if available_qty > 0:
                allocated = min(quantity, available_qty)
                available[resource] = available_qty - allocated
                
                allocations.append({
                    "hospital_id": req["hospital_id"],
                    "hospital_name": req["hospital_name"],
                    "resource": resource,
                    "quantity": allocated,
                    "urgency": req.get("urgency"),
                    "reason": req.get("reason", ""),
                })
        
        return allocations
    
    def _assign_ambulances(
        self,
        patient_assignments: List[Dict],
        ambulances: List[Dict],
        hospitals: List[Dict],
    ) -> List[Dict]:
        """Assign available ambulances to patient pickups"""
        assignments = []
        
        # Get available ambulances
        available_ambulances = [
            a for a in ambulances 
            if a.get("current_capacity", {}).get("available_slots", 0) > 0
        ]
        
        # Build hospital location map
        hospital_locations = {}
        for h in hospitals:
            hospital_locations[h.get("agent_id")] = h.get("location", (50, 50))
        
        for assignment in patient_assignments:
            if not available_ambulances:
                break
            
            patient_loc = assignment.get("patient_location", (50, 50))
            hospital_id = assignment.get("assigned_hospital")
            hospital_loc = hospital_locations.get(hospital_id, (50, 50))
            
            # Find nearest available ambulance
            best_amb = None
            best_eta = float('inf')
            
            for amb in available_ambulances:
                amb_loc = amb.get("location", (50, 50))
                # Calculate ETA: ambulance -> patient -> hospital
                eta = self._calculate_eta(amb_loc, patient_loc, hospital_loc)
                
                if eta < best_eta:
                    best_eta = eta
                    best_amb = amb
            
            if best_amb:
                amb_assignment = {
                    "ambulance_id": best_amb.get("agent_id"),
                    "patient_id": assignment.get("patient_id"),
                    "hospital_id": hospital_id,
                    "pickup_location": patient_loc,
                    "hospital_location": hospital_loc,
                    "eta_minutes": round(best_eta, 1),
                }
                assignments.append(amb_assignment)
                available_ambulances.remove(best_amb)
        
        return assignments
    
    def _calculate_distance(self, loc1: Tuple, loc2: Tuple) -> float:
        """Calculate Euclidean distance"""
        return math.sqrt((loc2[0] - loc1[0])**2 + (loc2[1] - loc1[1])**2)
    
    def _calculate_eta(self, amb_loc: Tuple, patient_loc: Tuple, hospital_loc: Tuple) -> float:
        """Calculate ETA in minutes (ambulance -> patient -> hospital)"""
        speed = 40  # km/h
        d1 = self._calculate_distance(amb_loc, patient_loc)
        d2 = self._calculate_distance(patient_loc, hospital_loc)
        total_distance = d1 + d2
        hours = total_distance / speed
        return hours * 60
    
    def _generate_explanations(self, round_result: Dict) -> List[Dict]:
        """Generate natural language explanations for decisions"""
        explanations = []
        
        for pa in round_result.get("patient_assignments", []):
            exp = {
                "type": "patient_assignment",
                "explanation": (
                    f"Patient {pa['patient_id']} ({pa['patient_severity']}) assigned to "
                    f"{pa['hospital_name']} because {pa['reason']}"
                ),
            }
            explanations.append(exp)
        
        for sa in round_result.get("supply_allocations", []):
            exp = {
                "type": "supply_allocation",
                "explanation": (
                    f"{sa['quantity']} units of {sa['resource']} allocated to "
                    f"{sa['hospital_name']} due to {sa.get('urgency', 'standard')} urgency"
                ),
            }
            explanations.append(exp)
        
        for aa in round_result.get("ambulance_assignments", []):
            exp = {
                "type": "ambulance_dispatch",
                "explanation": (
                    f"Ambulance {aa['ambulance_id']} dispatched for patient {aa['patient_id']} "
                    f"to {aa['hospital_id']} (ETA: {aa['eta_minutes']} min)"
                ),
            }
            explanations.append(exp)
        
        return explanations
    
    def get_round_summary(self) -> Dict[str, Any]:
        """Get summary of the latest negotiation round"""
        if not self.negotiation_rounds:
            return {"message": "No negotiations yet"}
        
        latest = self.negotiation_rounds[-1]
        return {
            "round": latest["round"],
            "patients_assigned": len(latest["patient_assignments"]),
            "supplies_allocated": len(latest["supply_allocations"]),
            "ambulances_dispatched": len(latest["ambulance_assignments"]),
            "explanations": latest["decisions_explained"],
        }
