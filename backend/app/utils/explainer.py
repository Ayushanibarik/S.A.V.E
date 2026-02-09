"""
Decision Explainer: Generates human-readable clinical explanations for decisions
Uses medical terminology for trust and credibility in healthcare settings
"""

from typing import Dict, List, Any, Optional
from ..config.constants import ESI_LEVELS, SEVERITY_TO_ESI


class DecisionExplainer:
    """
    Generates natural language explanations for system decisions.
    Uses clinical terminology appropriate for healthcare professionals.
    Provides transparency and audit trail for medical decision support.
    """
    
    def __init__(self):
        self.explanations: List[Dict] = []
    
    def reset(self):
        """Reset explanations for new simulation"""
        self.explanations = []
    
    def _get_esi_description(self, severity_or_esi) -> str:
        """Get ESI triage category description"""
        if isinstance(severity_or_esi, int):
            esi = severity_or_esi
        else:
            esi = SEVERITY_TO_ESI.get(severity_or_esi, 3)
        return f"ESI-{esi} ({ESI_LEVELS[esi]['name']})"
    
    def explain_patient_assignment(
        self,
        patient_id: str,
        patient_severity: str,
        assigned_hospital: str,
        hospital_name: str,
        distance: float,
        capacity_available: int,
        alternative_hospitals: List[str] = None,
        esi_level: int = None,
    ) -> Dict[str, Any]:
        """Explain why a patient was assigned to a specific hospital using clinical terminology"""
        
        esi = esi_level or SEVERITY_TO_ESI.get(patient_severity, 3)
        triage_desc = self._get_esi_description(esi)
        
        reasons = []
        
        # Clinical distance reasoning
        if distance < 10:
            reasons.append(f"nearest definitive care facility ({round(distance, 1)}km)")
        elif distance < 25:
            reasons.append(f"accessible facility within response radius ({round(distance, 1)}km)")
        else:
            reasons.append(f"available capacity despite distance ({round(distance, 1)}km)")
        
        # Capacity reasoning with clinical context
        if capacity_available > 20:
            reasons.append(f"adequate bed availability ({capacity_available} beds)")
        elif capacity_available > 5:
            reasons.append(f"sufficient capacity to ensure safe admission ({capacity_available} beds)")
        else:
            reasons.append("limited but available capacity")
        
        # ESI-specific reasoning
        if esi <= 2:
            reasons.append("ICU availability and oxygen reserve confirmed")
        
        # Alternative consideration
        if alternative_hospitals:
            reasons.append(f"optimal choice among {len(alternative_hospitals)} assessed facilities")
        
        explanation_text = (
            f"Patient {patient_id} ({triage_desc}) transferred to {hospital_name}. "
            f"Clinical rationale: {'; '.join(reasons)}."
        )
        
        explanation = {
            "type": "patient_assignment",
            "patient_id": patient_id,
            "esi_level": esi,
            "triage_category": ESI_LEVELS[esi]["name"],
            "hospital": assigned_hospital,
            "text": explanation_text,
            "explanation": explanation_text,
            "short": f"Patient {patient_id} ({triage_desc}) → {hospital_name}",
        }
        
        self.explanations.append(explanation)
        return explanation
    
    def explain_reroute(
        self,
        patient_id: str,
        from_hospital: str,
        to_hospital: str,
        reason: str,
        esi_level: int = None,
    ) -> Dict[str, Any]:
        """Explain patient diversion using clinical terminology"""
        
        reason_map = {
            "overload": "surge protocol activated at original destination",
            "oxygen_shortage": "oxygen reserves insufficient for safe care delivery",
            "icu_full": "critical care saturation at original facility",
            "faster_delivery": "alternative pathway reduces time to definitive care",
            "load_balancing": "regional load distribution to maintain system capacity",
            "diversion": "mandatory patient diversion per facility status",
        }
        
        clinical_reason = reason_map.get(reason, reason)
        triage_desc = self._get_esi_description(esi_level) if esi_level else ""
        
        explanation_text = (
            f"Patient diversion approved: {patient_id} {triage_desc} "
            f"redirected from {from_hospital} to {to_hospital}. "
            f"Clinical rationale: {clinical_reason}."
        )
        
        explanation = {
            "type": "patient_diversion",
            "patient_id": patient_id,
            "from": from_hospital,
            "to": to_hospital,
            "text": explanation_text,
            "explanation": explanation_text,
            "short": f"Patient diversion: {patient_id} → {to_hospital}",
        }
        
        self.explanations.append(explanation)
        return explanation
    
    def explain_supply_allocation(
        self,
        supply_type: str,
        quantity: int,
        from_depot: str,
        to_hospital: str,
        urgency: str,
        reason: str = "",
        hours_remaining: float = None,
    ) -> Dict[str, Any]:
        """Explain supply allocation using clinical terminology"""
        
        urgency_text = {
            "critical": "emergent resupply",
            "high": "priority resupply",
            "medium": "scheduled resupply",
            "low": "routine restocking",
        }
        
        supply_descriptions = {
            "oxygen": "medical oxygen",
            "blood_products": "blood products",
            "medications": "essential medications",
            "ppe": "personal protective equipment",
            "iv_fluids": "IV fluids",
        }
        
        supply_desc = supply_descriptions.get(supply_type, supply_type)
        urgency_desc = urgency_text.get(urgency, urgency)
        
        hours_context = ""
        if hours_remaining is not None:
            hours_context = f" Current reserve: ≈{round(hours_remaining, 1)} hours at current consumption."
        
        explanation_text = (
            f"{supply_desc.capitalize()} reallocation: {quantity} units dispatched to {to_hospital} "
            f"({urgency_desc}).{hours_context} {reason}".strip()
        )
        
        explanation = {
            "type": "supply_allocation",
            "supply": supply_type,
            "quantity": quantity,
            "destination": to_hospital,
            "urgency": urgency,
            "text": explanation_text,
            "explanation": explanation_text,
            "short": f"Supply dispatch: {quantity} {supply_desc} → {to_hospital}",
        }
        
        self.explanations.append(explanation)
        return explanation
    
    def explain_ambulance_dispatch(
        self,
        ambulance_id: str,
        patient_id: str,
        hospital_id: str,
        eta_minutes: float,
        distance: float = None,
        esi_level: int = None,
    ) -> Dict[str, Any]:
        """Explain ambulance dispatch decision using clinical terminology"""
        
        eta_text = f"ETA: {round(eta_minutes)} minutes"
        if distance:
            eta_text += f" ({round(distance, 1)}km)"
        
        triage_context = ""
        golden_hour = ""
        if esi_level:
            triage_context = f" for {self._get_esi_description(esi_level)} patient"
            if esi_level <= 2 and eta_minutes < 60:
                golden_hour = " Golden hour compliance maintained."
            elif esi_level <= 2:
                golden_hour = " Extended transport time documented."
        
        explanation_text = (
            f"Ambulance unit {ambulance_id} deployed{triage_context} to {hospital_id}. "
            f"{eta_text}.{golden_hour}"
        )
        
        explanation = {
            "type": "ambulance_dispatch",
            "ambulance": ambulance_id,
            "patient": patient_id,
            "hospital": hospital_id,
            "eta_minutes": eta_minutes,
            "text": explanation_text,
            "explanation": explanation_text,
            "short": f"Ambulance {ambulance_id} dispatched: {patient_id} → {hospital_id} ({round(eta_minutes)}min)",
        }
        
        self.explanations.append(explanation)
        return explanation
    
    def explain_surge_activation(
        self,
        hospital_id: str,
        hospital_name: str,
        trigger: str,
        actions: List[str] = None,
    ) -> Dict[str, Any]:
        """Explain surge protocol activation"""
        
        trigger_descriptions = {
            "bed_capacity": "bed utilization exceeded surge threshold",
            "icu_saturation": "critical care saturation detected",
            "oxygen_shortage": "oxygen reserves below safe operating threshold",
            "staffing": "staffing ratios below clinical standards",
            "mass_casualty": "mass-casualty incident declared",
        }
        
        trigger_desc = trigger_descriptions.get(trigger, trigger)
        actions_text = ""
        if actions:
            actions_text = f" Actions initiated: {'; '.join(actions)}."
        
        explanation_text = (
            f"Surge protocol activated at {hospital_name}. "
            f"Trigger: {trigger_desc}.{actions_text}"
        )
        
        explanation = {
            "type": "surge_activation",
            "hospital": hospital_id,
            "trigger": trigger,
            "text": explanation_text,
            "explanation": explanation_text,
            "short": f"Surge protocol: {hospital_name}",
        }
        
        self.explanations.append(explanation)
        return explanation
    
    def explain_overload_prevention(
        self,
        hospital_id: str,
        hospital_name: str,
        action_taken: str,
        patients_redirected: int = 0,
    ) -> Dict[str, Any]:
        """Explain how facility overload was prevented"""
        
        actions = {
            "redirect": f"{patients_redirected} patients diverted to alternate facilities",
            "supply_boost": "emergent medical supplies dispatched",
            "capacity_expansion": "surge capacity resources activated",
            "load_balance": "regional patient distribution rebalanced",
            "diversion_order": "patient diversion order issued",
        }
        
        action_desc = actions.get(action_taken, action_taken)
        
        explanation_text = (
            f"Facility overload prevented at {hospital_name}. "
            f"Intervention: {action_desc}. "
            f"Continuity of care maintained."
        )
        
        explanation = {
            "type": "overload_prevention",
            "hospital": hospital_id,
            "action": action_taken,
            "text": explanation_text,
            "explanation": explanation_text,
            "short": f"Overload prevented: {hospital_name}",
        }
        
        self.explanations.append(explanation)
        return explanation
    
    def explain_government_override(
        self,
        override_type: str,
        target: str,
        directive: str,
    ) -> Dict[str, Any]:
        """Explain regional authority directive"""
        
        override_descriptions = {
            "priority_escalation": "Regional priority escalation",
            "resource_reallocation": "Resource reallocation directive",
            "facility_designation": "Facility designation order",
            "surge_declaration": "Regional surge declaration",
            "mutual_aid": "Mutual aid activation",
        }
        
        type_desc = override_descriptions.get(override_type, override_type)
        
        explanation_text = (
            f"Regional authority directive: {type_desc} affecting {target}. "
            f"Directive: {directive}"
        )
        
        explanation = {
            "type": "government_override",
            "override_type": override_type,
            "target": target,
            "text": explanation_text,
            "explanation": explanation_text,
            "short": f"Authority directive: {type_desc}",
        }
        
        self.explanations.append(explanation)
        return explanation
    
    def explain_icu_escalation(
        self,
        region: str,
        available_icu: int,
        action: str,
    ) -> Dict[str, Any]:
        """Explain ICU capacity escalation to regional authority"""
        
        explanation_text = (
            f"No ICU capacity available within {region}. "
            f"System-wide ICU availability: {available_icu} beds. "
            f"Escalation initiated: {action}."
        )
        
        explanation = {
            "type": "icu_escalation",
            "region": region,
            "available_icu": available_icu,
            "text": explanation_text,
            "explanation": explanation_text,
            "short": f"ICU escalation: {region} ({available_icu} beds available)",
        }
        
        self.explanations.append(explanation)
        return explanation
    
    def get_recent_explanations(self, limit: int = 20) -> List[Dict]:
        """Get recent explanations for decision log"""
        return self.explanations[-limit:]
    
    def get_explanations_by_type(self, exp_type: str) -> List[Dict]:
        """Get explanations filtered by type"""
        return [e for e in self.explanations if e.get("type") == exp_type]
    
    def generate_summary(self) -> str:
        """Generate a clinical summary of recent system actions"""
        if not self.explanations:
            return "System monitoring active. No interventions required."
        
        recent = self.explanations[-10:]
        
        counts = {}
        for exp in recent:
            exp_type = exp.get("type", "other")
            counts[exp_type] = counts.get(exp_type, 0) + 1
        
        parts = []
        if counts.get("patient_assignment", 0):
            parts.append(f"{counts['patient_assignment']} patient transfer(s)")
        if counts.get("patient_diversion", 0) or counts.get("reroute", 0):
            diverts = counts.get("patient_diversion", 0) + counts.get("reroute", 0)
            parts.append(f"{diverts} patient diversion(s)")
        if counts.get("supply_allocation", 0):
            parts.append(f"{counts['supply_allocation']} supply dispatch(es)")
        if counts.get("overload_prevention", 0):
            parts.append(f"{counts['overload_prevention']} overload intervention(s)")
        if counts.get("surge_activation", 0):
            parts.append(f"{counts['surge_activation']} surge activation(s)")
        if counts.get("ambulance_dispatch", 0):
            parts.append(f"{counts['ambulance_dispatch']} ambulance deployment(s)")
        
        if parts:
            return "Recent system actions: " + ", ".join(parts) + "."
        return "System monitoring active."
