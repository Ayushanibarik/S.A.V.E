"""
Hospital Agent: Manages hospital resources and patient decisions
Handles beds, ICU, oxygen, and accept/reject logic
Enhanced with ESI triage support and clinical-grade oxygen modeling
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from ..agents.base_agent import BaseAgent
from ..config.constants import (
    HOSPITAL_OVERLOAD_THRESHOLD,
    HOSPITAL_CRITICAL_THRESHOLD,
    HOSPITAL_DIVERSION_THRESHOLD,
    ICU_CRITICAL_THRESHOLD,
    ICU_WARNING_THRESHOLD,
    OXYGEN_CRITICAL_LEVEL,
    OXYGEN_CONSUMPTION_LPM,
    OXYGEN_RESERVE_CRITICAL_HOURS,
    OXYGEN_RESERVE_WARNING_HOURS,
    AGENT_TYPE_HOSPITAL,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    ESI_LEVELS,
    SEVERITY_TO_ESI,
    NURSE_PATIENT_RATIO_ICU,
)


class HospitalAgent(BaseAgent):
    """
    Hospital agent that manages bed capacity, ICU, oxygen, and patient acceptance.
    Makes decisions on accepting/rejecting patients and requesting resources.
    Implements ESI 1-5 triage acuity levels and clinical oxygen consumption modeling.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        location: tuple,
        total_beds: int,
        available_beds: int,
        icu_beds: int,
        icu_available: int,
        oxygen_units: int,
        doctors_on_duty: int,
        patient_inflow_rate: float = 1.0,
        nurses_on_duty: int = None,
    ):
        super().__init__(agent_id, AGENT_TYPE_HOSPITAL, name)
        
        self.location = location
        self.total_beds = total_beds
        self.available_beds = available_beds
        self.icu_beds = icu_beds
        self.icu_available = icu_available
        self.oxygen_units = oxygen_units  # Total liters available
        self.doctors_on_duty = doctors_on_duty
        self.patient_inflow_rate = patient_inflow_rate
        self.nurses_on_duty = nurses_on_duty or (doctors_on_duty * 3)  # Estimate if not provided
        
        # Patient tracking with ESI levels
        self.patients_admitted: List[Dict[str, Any]] = []  # Now stores {id, esi_level, admitted_at}
        self.pending_requests: List[Dict] = []
        self.incoming_ambulances: List[str] = []
        
    @property
    def bed_utilization(self) -> float:
        """Calculate bed utilization percentage"""
        return 1 - (self.available_beds / max(self.total_beds, 1))
    
    @property
    def icu_utilization(self) -> float:
        """Calculate ICU utilization percentage"""
        return 1 - (self.icu_available / max(self.icu_beds, 1))
    
    @property
    def icu_patients(self) -> int:
        """Number of patients currently in ICU"""
        return self.icu_beds - self.icu_available
    
    @property
    def current_oxygen_consumption_lpm(self) -> float:
        """Calculate current oxygen consumption in liters per minute based on patient acuity"""
        total_lpm = 0.0
        for patient in self.patients_admitted:
            esi = patient.get("esi_level", 3)
            total_lpm += OXYGEN_CONSUMPTION_LPM.get(esi, 4.0)
        # ICU patients not in admitted list also consume oxygen
        total_lpm += self.icu_patients * OXYGEN_CONSUMPTION_LPM[1]
        return total_lpm
    
    @property
    def oxygen_hours_remaining(self) -> float:
        """Calculate hours of oxygen remaining at current consumption rate"""
        consumption_lpm = self.current_oxygen_consumption_lpm
        if consumption_lpm <= 0:
            return 999.0  # Effectively unlimited if no consumption
        return self.oxygen_units / (consumption_lpm * 60)
    
    @property
    def oxygen_status(self) -> str:
        """Get oxygen reserve status: critical, warning, or adequate"""
        hours = self.oxygen_hours_remaining
        if hours <= OXYGEN_RESERVE_CRITICAL_HOURS:
            return "critical"
        elif hours <= OXYGEN_RESERVE_WARNING_HOURS:
            return "warning"
        return "adequate"
    
    @property
    def nurse_patient_ratio(self) -> float:
        """Calculate current nurse-to-patient ratio for ICU"""
        if self.icu_patients == 0:
            return float('inf')
        # Assume 40% of nurses are ICU-assigned
        icu_nurses = self.nurses_on_duty * 0.4
        return icu_nurses / self.icu_patients
    
    @property
    def staffing_adequate(self) -> bool:
        """Check if nurse staffing meets standard ratios"""
        return self.nurse_patient_ratio >= (1 / NURSE_PATIENT_RATIO_ICU)
    
    @property
    def is_overloaded(self) -> bool:
        """Check if hospital is at overload threshold"""
        return self.bed_utilization >= HOSPITAL_OVERLOAD_THRESHOLD
    
    @property
    def is_critical(self) -> bool:
        """Check if hospital is at critical capacity (surge protocol required)"""
        return (
            self.bed_utilization >= HOSPITAL_CRITICAL_THRESHOLD or
            self.icu_utilization >= ICU_CRITICAL_THRESHOLD or
            self.oxygen_status == "critical"
        )
    
    @property
    def requires_diversion(self) -> bool:
        """Check if mandatory patient diversion is required"""
        return (
            self.bed_utilization >= HOSPITAL_DIVERSION_THRESHOLD or
            self.icu_available == 0 or
            self.oxygen_hours_remaining <= 2
        )
    
    @property
    def status_level(self) -> str:
        """Get status level for dashboard display"""
        if self.requires_diversion:
            return "diversion"
        elif self.is_critical:
            return "critical"
        elif self.is_overloaded:
            return "warning"
        else:
            return "operational"
    
    @property
    def clinical_status(self) -> str:
        """Get detailed clinical status description"""
        if self.requires_diversion:
            return "CRITICAL – PATIENT DIVERSION REQUIRED"
        elif self.is_critical:
            return "CRITICAL – AT CAPACITY"
        elif self.is_overloaded:
            return "LIMITED CAPACITY"
        else:
            return "OPERATIONAL – ACCEPTING ADMISSIONS"
    
    def get_state(self) -> Dict[str, Any]:
        """Return current state for dashboard/API with clinical metrics"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "location": self.location,
            "total_beds": self.total_beds,
            "available_beds": self.available_beds,
            "bed_utilization": round(self.bed_utilization * 100, 1),
            "icu_beds": self.icu_beds,
            "icu_available": self.icu_available,
            "icu_utilization": round(self.icu_utilization * 100, 1),
            "oxygen_units": self.oxygen_units,
            "oxygen_consumption_lpm": round(self.current_oxygen_consumption_lpm, 1),
            "oxygen_hours_remaining": round(self.oxygen_hours_remaining, 1),
            "oxygen_status": self.oxygen_status,
            "doctors_on_duty": self.doctors_on_duty,
            "nurses_on_duty": self.nurses_on_duty,
            "nurse_patient_ratio": round(self.nurse_patient_ratio, 2) if self.icu_patients > 0 else None,
            "staffing_adequate": self.staffing_adequate,
            "status": self.status_level,
            "clinical_status": self.clinical_status,
            "is_overloaded": self.is_overloaded,
            "is_critical": self.is_critical,
            "requires_diversion": self.requires_diversion,
            "patients_count": len(self.patients_admitted),
            "icu_patients": self.icu_patients,
            "incoming_ambulances": len(self.incoming_ambulances),
            "patient_inflow_rate": self.patient_inflow_rate,
        }
    
    def generate_message(self) -> Dict[str, Any]:
        """Generate status message for negotiation"""
        message = self.get_base_message()
        message.update({
            "message_type": "status_update",
            "current_capacity": {
                "available_beds": self.available_beds,
                "icu_available": self.icu_available,
                "oxygen_units": self.oxygen_units,
                "oxygen_hours_remaining": self.oxygen_hours_remaining,
            },
            "requests": self._generate_requests(),
            "offers": self._generate_offers(),
            "priority_score": self.calculate_priority_score(),
        })
        return message
    
    def _generate_requests(self) -> List[Dict]:
        """Generate resource requests based on current needs"""
        requests = []
        
        # Request oxygen if low (based on hours remaining)
        if self.oxygen_status != "adequate":
            hours = self.oxygen_hours_remaining
            urgency = "critical" if hours <= OXYGEN_RESERVE_CRITICAL_HOURS else "high"
            requests.append({
                "resource": "oxygen",
                "quantity": 100,  # Request standard resupply
                "urgency": urgency,
                "reason": f"Oxygen reserve at {round(hours, 1)} hours at current consumption",
            })
        
        # Request ambulance diversion if saturated
        if self.requires_diversion:
            requests.append({
                "resource": "patient_diversion",
                "quantity": 1,
                "urgency": "critical",
                "reason": f"Critical care saturation – {self.clinical_status}",
            })
        elif self.is_overloaded:
            requests.append({
                "resource": "surge_support",
                "quantity": 1,
                "urgency": "high",
                "reason": f"Surge protocol active – {round(self.bed_utilization*100)}% capacity",
            })
        
        # Request staffing if inadequate
        if not self.staffing_adequate and self.icu_patients > 0:
            requests.append({
                "resource": "nursing_staff",
                "quantity": 2,
                "urgency": "high",
                "reason": f"ICU nurse ratio below standard: 1:{round(1/self.nurse_patient_ratio, 1)}",
            })
        
        return requests
    
    def _generate_offers(self) -> List[Dict]:
        """Generate resource offers if hospital has surplus"""
        offers = []
        
        # Offer to accept patients if under-utilized
        if self.bed_utilization < 0.5:
            offers.append({
                "resource": "bed_capacity",
                "quantity": int(self.available_beds * 0.5),
                "priority": "medium",
                "description": "Available beds for patient transfer",
            })
        
        # Offer ICU if available
        if self.icu_utilization < 0.6:
            offers.append({
                "resource": "icu_capacity",
                "quantity": self.icu_available,
                "priority": "high",
                "description": "ICU beds available for critical patients",
            })
        
        return offers
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """Process incoming message from another agent"""
        msg_type = message.get("message_type", "")
        
        if msg_type == "patient_assignment":
            self._handle_patient_assignment(message)
        elif msg_type == "supply_allocation":
            self._handle_supply_allocation(message)
        elif msg_type == "priority_override":
            self._handle_priority_override(message)
    
    def _handle_patient_assignment(self, message: Dict):
        """Handle incoming patient assignment with ESI triage"""
        patient_id = message.get("patient_id")
        severity = message.get("severity", "medium")
        esi_level = message.get("esi_level") or SEVERITY_TO_ESI.get(severity, 3)
        
        if self.can_accept_patient(esi_level):
            self.accept_patient(patient_id, esi_level)
            self.log_action("patient_accepted", {
                "patient_id": patient_id,
                "esi_level": esi_level,
                "triage_category": ESI_LEVELS[esi_level]["name"],
            })
        else:
            self.log_action("patient_rejected", {
                "patient_id": patient_id,
                "esi_level": esi_level,
                "reason": "Critical care saturation" if esi_level <= 2 else "No capacity",
            })
    
    def _handle_supply_allocation(self, message: Dict):
        """Handle incoming supply delivery"""
        supply_type = message.get("supply_type")
        quantity = message.get("quantity", 0)
        
        if supply_type == "oxygen":
            self.oxygen_units += quantity
            self.log_action("supply_received", {
                "type": "oxygen",
                "quantity": quantity,
                "new_total": self.oxygen_units,
                "hours_remaining": round(self.oxygen_hours_remaining, 1),
            })
    
    def _handle_priority_override(self, message: Dict):
        """Handle government priority override"""
        # Implement policy changes
        pass
    
    def can_accept_patient(self, esi_level: int) -> bool:
        """Check if hospital can accept a patient based on ESI level"""
        # ESI 1-2 require ICU and adequate oxygen
        if esi_level <= 2:
            return (
                self.icu_available > 0 and 
                self.oxygen_hours_remaining > OXYGEN_RESERVE_CRITICAL_HOURS and
                not self.requires_diversion
            )
        else:
            return self.available_beds > 0 and not self.requires_diversion
    
    def accept_patient(self, patient_id: str, esi_level: int) -> bool:
        """Accept a patient into the hospital with ESI tracking"""
        if not self.can_accept_patient(esi_level):
            return False
        
        patient_record = {
            "id": patient_id,
            "esi_level": esi_level,
            "admitted_at": datetime.now().isoformat(),
            "triage_category": ESI_LEVELS[esi_level]["name"],
        }
        
        if esi_level <= 2:
            # Critical/emergent patients go to ICU
            self.icu_available -= 1
            patient_record["unit"] = "ICU"
        else:
            self.available_beds -= 1
            patient_record["unit"] = "General"
        
        self.patients_admitted.append(patient_record)
        return True
    
    def update(self, tick: int) -> List[Dict[str, Any]]:
        """Update hospital state for a simulation tick"""
        actions = []
        
        # Consume oxygen based on current patient acuity (per tick = ~5 min simulation time)
        oxygen_consumed = self.current_oxygen_consumption_lpm * 5  # 5 minutes per tick
        self.oxygen_units = max(0, self.oxygen_units - oxygen_consumed)
        
        # Patients may be discharged (simplified: every 5 ticks)
        if tick % 5 == 0 and self.patients_admitted:
            # Discharge lowest acuity patient first
            self.patients_admitted.sort(key=lambda p: -p.get("esi_level", 3))
            discharged = self.patients_admitted.pop()
            
            if discharged.get("unit") == "ICU":
                self.icu_available = min(self.icu_available + 1, self.icu_beds)
            else:
                self.available_beds = min(self.available_beds + 1, self.total_beds)
            
            actions.append({
                "type": "patient_discharged",
                "patient_id": discharged["id"],
                "esi_level": discharged.get("esi_level"),
            })
        
        self.last_updated = datetime.now()
        return actions
    
    def calculate_priority_score(self) -> float:
        """Calculate priority score for negotiation (higher = more urgent need)"""
        score = 0.0
        
        # Bed utilization impact
        score += self.bed_utilization * 0.25
        
        # ICU criticality (higher weight)
        score += self.icu_utilization * 0.30
        
        # Oxygen shortage (based on hours remaining)
        if self.oxygen_status == "critical":
            score += 0.30
        elif self.oxygen_status == "warning":
            score += 0.15
        
        # Staffing adequacy
        if not self.staffing_adequate:
            score += 0.10
        
        # Patient inflow pressure
        score += min(0.05, self.patient_inflow_rate * 0.01)
        
        return min(1.0, score)
