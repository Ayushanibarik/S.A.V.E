"""
Objective Function: Defines the optimization goal for resource allocation
Minimizes deaths, delays, and overloads
"""

from typing import Dict, List, Any
from ..config.constants import (
    WEIGHT_UNSERVED_CRITICAL,
    WEIGHT_RESPONSE_TIME,
    WEIGHT_OVERLOAD_PENALTY,
    WEIGHT_FAIRNESS,
)


class ObjectiveFunction:
    """
    Objective function that evaluates the quality of an allocation plan.
    
    Minimize:
        (total_unserved_critical_patients × 10) +
        (average_response_time × 2) +
        (hospital_overload_penalty × 5)
    """
    
    def __init__(
        self,
        weight_unserved: float = WEIGHT_UNSERVED_CRITICAL,
        weight_response: float = WEIGHT_RESPONSE_TIME,
        weight_overload: float = WEIGHT_OVERLOAD_PENALTY,
        weight_fairness: float = WEIGHT_FAIRNESS,
    ):
        self.weight_unserved = weight_unserved
        self.weight_response = weight_response
        self.weight_overload = weight_overload
        self.weight_fairness = weight_fairness
    
    def calculate_cost(
        self,
        unserved_critical: int,
        avg_response_time: float,
        overloaded_hospitals: int,
        load_variance: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate the total cost (lower is better).
        Returns breakdown of costs for explainability.
        """
        unserved_cost = unserved_critical * self.weight_unserved
        response_cost = avg_response_time * self.weight_response
        overload_cost = overloaded_hospitals * self.weight_overload
        fairness_cost = load_variance * self.weight_fairness
        
        total_cost = unserved_cost + response_cost + overload_cost + fairness_cost
        
        return {
            "total_cost": round(total_cost, 2),
            "breakdown": {
                "unserved_critical_cost": round(unserved_cost, 2),
                "response_time_cost": round(response_cost, 2),
                "overload_cost": round(overload_cost, 2),
                "fairness_cost": round(fairness_cost, 2),
            },
            "inputs": {
                "unserved_critical": unserved_critical,
                "avg_response_time": round(avg_response_time, 2),
                "overloaded_hospitals": overloaded_hospitals,
                "load_variance": round(load_variance, 4),
            },
        }
    
    def evaluate_allocation(
        self,
        hospitals: Dict[str, Dict],
        waiting_patients: List[Dict],
        response_times: List[float],
    ) -> Dict[str, Any]:
        """
        Evaluate a current allocation state.
        """
        # Count unserved critical patients
        unserved_critical = sum(
            1 for p in waiting_patients 
            if p.get("severity") == "critical" and p.get("status") == "waiting"
        )
        
        # Calculate average response time
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # Count overloaded hospitals
        overloaded = 0
        loads = []
        for h_id, h_state in hospitals.items():
            utilization = 1 - (h_state.get("available_beds", 0) / max(h_state.get("total_beds", 1), 1))
            loads.append(utilization)
            if utilization >= 0.85:
                overloaded += 1
        
        # Calculate load variance (fairness measure)
        load_variance = 0.0
        if loads:
            mean_load = sum(loads) / len(loads)
            load_variance = sum((l - mean_load) ** 2 for l in loads) / len(loads)
        
        return self.calculate_cost(
            unserved_critical,
            avg_response_time,
            overloaded,
            load_variance,
        )
    
    def compare_allocations(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare two allocation states and explain improvement.
        """
        before_cost = before.get("total_cost", 0)
        after_cost = after.get("total_cost", 0)
        
        improvement = before_cost - after_cost
        improvement_pct = (improvement / before_cost * 100) if before_cost > 0 else 0
        
        improved_metrics = []
        before_breakdown = before.get("breakdown", {})
        after_breakdown = after.get("breakdown", {})
        
        for metric in before_breakdown:
            if after_breakdown.get(metric, 0) < before_breakdown.get(metric, 0):
                improved_metrics.append(metric.replace("_cost", "").replace("_", " "))
        
        return {
            "before_cost": before_cost,
            "after_cost": after_cost,
            "improvement": round(improvement, 2),
            "improvement_percentage": round(improvement_pct, 1),
            "improved_metrics": improved_metrics,
            "is_better": after_cost < before_cost,
            "explanation": self._generate_comparison_explanation(before, after, improvement),
        }
    
    def _generate_comparison_explanation(
        self,
        before: Dict,
        after: Dict,
        improvement: float,
    ) -> str:
        """Generate natural language explanation of improvement"""
        if improvement <= 0:
            return "No improvement in this round."
        
        explanations = []
        
        before_inputs = before.get("inputs", {})
        after_inputs = after.get("inputs", {})
        
        # Check what improved
        if after_inputs.get("unserved_critical", 0) < before_inputs.get("unserved_critical", 0):
            diff = before_inputs["unserved_critical"] - after_inputs["unserved_critical"]
            explanations.append(f"{diff} critical patient(s) now receiving care")
        
        if after_inputs.get("avg_response_time", 0) < before_inputs.get("avg_response_time", 0):
            diff = before_inputs["avg_response_time"] - after_inputs["avg_response_time"]
            explanations.append(f"Response time reduced by {round(diff, 1)} minutes")
        
        if after_inputs.get("overloaded_hospitals", 0) < before_inputs.get("overloaded_hospitals", 0):
            diff = before_inputs["overloaded_hospitals"] - after_inputs["overloaded_hospitals"]
            explanations.append(f"{diff} hospital(s) no longer overloaded")
        
        if explanations:
            return ". ".join(explanations) + "."
        else:
            return f"Overall system efficiency improved by {round(improvement, 1)} points."
