"""
Simulator: Main simulation orchestration loop
Ties together all agents, negotiation, and optimization
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import time

from ..agents.hospital_agent import HospitalAgent
from ..agents.ambulance_agent import AmbulanceAgent
from ..agents.supply_agent import SupplyAgent
from ..agents.government_agent import GovernmentAgent
from ..communication.event_bus import EventBus
from ..state.global_state import GlobalState
from ..negotiation.negotiation_engine import NegotiationEngine
from ..optimization.objective import ObjectiveFunction
from ..optimization.constraints import ConstraintChecker
from ..metrics.metrics_tracker import MetricsTracker
from ..utils.explainer import DecisionExplainer
from ..utils.failure_handler import FailureHandler
from ..utils.logger import SimulationLogger
from ..simulation.data_generator import DataGenerator
from ..config.scenario import (
    HOSPITALS_CONFIG,
    AMBULANCES_CONFIG,
    SUPPLY_CONFIG,
    GOVERNMENT_CONFIG,
    DISASTER_ZONES,
)


class Simulator:
    """
    Main simulation orchestrator.
    This is the engine that makes everything move.
    """
    
    def __init__(self):
        # Core components
        self.event_bus = EventBus()
        self.global_state = GlobalState()
        self.negotiation_engine = NegotiationEngine()
        self.objective = ObjectiveFunction()
        self.constraints = ConstraintChecker()
        self.metrics = MetricsTracker()
        self.explainer = DecisionExplainer()
        self.failure_handler = FailureHandler()
        self.logger = SimulationLogger()
        self.data_generator = DataGenerator()
        
        # Agents
        self.hospitals: Dict[str, HospitalAgent] = {}
        self.ambulances: Dict[str, AmbulanceAgent] = {}
        self.supply: Optional[SupplyAgent] = None
        self.government: Optional[GovernmentAgent] = None
        
        # Simulation state
        self.tick: int = 0
        self.running: bool = False
        self.waiting_patients: List[Dict] = []
        
    def reset(self):
        """Reset everything for a new simulation"""
        self.event_bus.reset()
        self.global_state.reset()
        self.negotiation_engine.reset()
        self.metrics.reset()
        self.explainer.reset()
        self.failure_handler = FailureHandler()
        self.logger.reset()
        self.data_generator = DataGenerator()
        
        self.hospitals = {}
        self.ambulances = {}
        self.supply = None
        self.government = None
        self.tick = 0
        self.running = False
        self.waiting_patients = []
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize all agents from scenario config"""
        self.reset()
        
        # Create Hospital Agents
        for h_config in HOSPITALS_CONFIG:
            hospital = HospitalAgent(
                agent_id=h_config["id"],
                name=h_config["name"],
                location=h_config["location"],
                total_beds=h_config["total_beds"],
                available_beds=h_config["available_beds"],
                icu_beds=h_config["icu_beds"],
                icu_available=h_config["icu_available"],
                oxygen_units=h_config["oxygen_units"],
                doctors_on_duty=h_config["doctors_on_duty"],
                patient_inflow_rate=h_config["patient_inflow_rate"],
            )
            self.hospitals[h_config["id"]] = hospital
            self.event_bus.register_agent(h_config["id"], hospital)
        
        # Create Ambulance Agents
        for a_config in AMBULANCES_CONFIG:
            ambulance = AmbulanceAgent(
                agent_id=a_config["id"],
                location=tuple(a_config["location"]),
                capacity=a_config["capacity"],
                fuel=a_config["fuel"],
                available=a_config["available"],
            )
            self.ambulances[a_config["id"]] = ambulance
            self.event_bus.register_agent(a_config["id"], ambulance)
        
        # Create Supply Agent
        self.supply = SupplyAgent(
            agent_id=SUPPLY_CONFIG["id"],
            name=SUPPLY_CONFIG["name"],
            location=tuple(SUPPLY_CONFIG["location"]),
            food_units=SUPPLY_CONFIG["food_units"],
            water_units=SUPPLY_CONFIG["water_units"],
            oxygen_units=SUPPLY_CONFIG["oxygen_units"],
            medicine_units=SUPPLY_CONFIG["medicine_units"],
            delivery_vehicles=SUPPLY_CONFIG["delivery_vehicles"],
        )
        self.event_bus.register_agent(SUPPLY_CONFIG["id"], self.supply)
        
        # Create Government Agent
        self.government = GovernmentAgent(
            agent_id=GOVERNMENT_CONFIG["id"],
            disaster_severity=GOVERNMENT_CONFIG["disaster_severity"],
            fairness_weight=GOVERNMENT_CONFIG["fairness_weight"],
        )
        self.event_bus.register_agent(GOVERNMENT_CONFIG["id"], self.government)
        
        # Generate initial casualties
        self.waiting_patients = self.data_generator.generate_initial_casualties(
            count=120,
            disaster_zones=DISASTER_ZONES,
        )
        
        # Record initial state
        self._sync_global_state()
        self.metrics.start()
        self.metrics.record_initial_state(
            {h.agent_id: h.get_state() for h in self.hospitals.values()},
            self.waiting_patients,
        )
        self.metrics.patients_waiting = len(self.waiting_patients)
        
        # Start logging
        self.logger.start()
        self.global_state.start_simulation()
        self.running = True
        
        return {
            "status": "initialized",
            "hospitals": len(self.hospitals),
            "ambulances": len(self.ambulances),
            "initial_patients": len(self.waiting_patients),
            "critical_patients": sum(1 for p in self.waiting_patients if p["severity"] == "critical"),
        }
    
    def step(self) -> Dict[str, Any]:
        """Execute one simulation tick"""
        if not self.running:
            return {"error": "Simulation not running. Call initialize() first."}
        
        self.tick += 1
        self.logger.set_tick(self.tick)
        self.global_state.current_tick = self.tick
        
        step_result = {
            "tick": self.tick,
            "timestamp": datetime.now().isoformat(),
            "actions": [],
            "decisions": [],
            "alerts": [],
        }
        
        # Save state before optimization
        self.global_state.save_before_state()
        
        # Step 1: Generate new patient inflow
        if self.tick % 3 == 0:  # Every 3 ticks
            new_patients = self.data_generator.generate_patient_inflow(
                base_rate=2.0,
                severity_multiplier=self.government.disaster_severity,
            )
            self.waiting_patients.extend(new_patients)
            self.metrics.patients_waiting = len(self.waiting_patients)
        
        # Step 2: Collect agent messages
        hospital_messages = [h.generate_message() for h in self.hospitals.values()]
        ambulance_messages = [a.generate_message() for a in self.ambulances.values()]
        supply_message = self.supply.generate_message()
        
        # Add location info to hospital messages
        for msg in hospital_messages:
            h = self.hospitals.get(msg["agent_id"])
            if h:
                msg["location"] = h.location
                msg["name"] = h.name
        
        # Step 3: Run negotiation
        gov_priorities = {
            "multipliers": self.government.calculate_priority_multipliers(
                {h.agent_id: h.get_state() for h in self.hospitals.values()}
            )
        }
        
        negotiation_result = self.negotiation_engine.run_negotiation(
            hospital_messages=hospital_messages,
            ambulance_messages=ambulance_messages,
            supply_message=supply_message,
            government_priorities=gov_priorities,
            waiting_patients=[p for p in self.waiting_patients if p["status"] == "waiting"],
        )
        
        # Step 4: Apply allocations
        for pa in negotiation_result.get("patient_assignments", []):
            hospital_id = pa["assigned_hospital"]
            hospital = self.hospitals.get(hospital_id)
            
            if hospital and hospital.can_accept_patient(pa["patient_severity"]):
                # Accept patient
                patient_id = pa["patient_id"]
                hospital.accept_patient(patient_id, pa["patient_severity"])
                
                # Mark patient as assigned
                for p in self.waiting_patients:
                    if p["id"] == patient_id:
                        p["status"] = "assigned"
                        p["assigned_hospital"] = hospital_id
                        break
                
                # Log and explain
                self.logger.log_patient_assignment(patient_id, hospital_id, pa["patient_severity"])
                self.explainer.explain_patient_assignment(
                    patient_id=patient_id,
                    patient_severity=pa["patient_severity"],
                    assigned_hospital=hospital_id,
                    hospital_name=pa.get("hospital_name", hospital_id),
                    distance=10.0,  # Simplified
                    capacity_available=hospital.available_beds,
                )
                
                # Record metrics
                self.metrics.record_patient_served(
                    {"severity": pa["patient_severity"]},
                    response_time=pa.get("score", 10.0) * 5,
                )
                
                step_result["actions"].append({
                    "type": "patient_assigned",
                    "patient": patient_id,
                    "hospital": hospital_id,
                })
        
        # Step 5: Dispatch ambulances
        for aa in negotiation_result.get("ambulance_assignments", []):
            ambulance = self.ambulances.get(aa["ambulance_id"])
            hospital = self.hospitals.get(aa["hospital_id"])
            
            if ambulance and ambulance.is_available and hospital:
                patient_data = None
                for p in self.waiting_patients:
                    if p["id"] == aa["patient_id"]:
                        patient_data = p
                        break
                
                if patient_data:
                    ambulance.assign_mission(
                        patient=patient_data,
                        hospital_id=aa["hospital_id"],
                        hospital_location=hospital.location,
                    )
                    ambulance.destination = hospital.location
                    
                    self.logger.log_ambulance_dispatch(
                        aa["ambulance_id"],
                        aa["patient_id"],
                        aa["hospital_id"],
                        aa["eta_minutes"],
                    )
                    
                    self.explainer.explain_ambulance_dispatch(
                        ambulance_id=aa["ambulance_id"],
                        patient_id=aa["patient_id"],
                        hospital_id=aa["hospital_id"],
                        eta_minutes=aa["eta_minutes"],
                    )
        
        # Step 6: Process supply allocations
        for sa in negotiation_result.get("supply_allocations", []):
            hospital = self.hospitals.get(sa["hospital_id"])
            if hospital and sa["resource"] == "oxygen":
                # Add pending supply request
                self.supply.pending_requests.append({
                    "requester_id": sa["hospital_id"],
                    "requester_location": hospital.location,
                    "supply_type": sa["resource"],
                    "quantity": sa["quantity"],
                    "urgency": sa.get("urgency", "medium"),
                })
        
        # Process pending supply deliveries
        deliveries = self.supply.process_pending_requests()
        for delivery in deliveries:
            self.logger.log_supply_allocation(
                delivery["supply_type"],
                delivery["quantity"],
                delivery["destination_id"],
            )
            self.metrics.record_supply_delivery()
        
        # Step 7: Update all agents
        for hospital in self.hospitals.values():
            hospital.update(self.tick)
        
        for ambulance in self.ambulances.values():
            actions = ambulance.update(self.tick)
            for action in actions:
                if action["type"] == "patient_delivered":
                    step_result["actions"].append(action)
        
        self.supply.update(self.tick)
        self.government.update(self.tick)
        
        # Step 8: Check for failures
        failures = self.failure_handler.check_and_handle_failures(
            {h.agent_id: h.get_state() for h in self.hospitals.values()},
            {a.agent_id: a.get_state() for a in self.ambulances.values()},
            self.supply.get_state(),
        )
        for failure_response in failures:
            step_result["alerts"].append(failure_response)
        
        # Step 9: Check for overload prevention
        for hospital in self.hospitals.values():
            state = hospital.get_state()
            if state["bed_utilization"] > 80 and state["bed_utilization"] < 90:
                self.metrics.record_overload_prevented(hospital.agent_id)
                self.logger.log_overload_prevented(hospital.agent_id, "load_balancing")
                self.explainer.explain_overload_prevention(
                    hospital.agent_id,
                    hospital.name,
                    "load_balance",
                )
        
        # Sync global state
        self._sync_global_state()
        self.metrics.record_tick(
            self.tick,
            {h.agent_id: h.get_state() for h in self.hospitals.values()},
            {a.agent_id: a.get_state() for a in self.ambulances.values()},
        )
        
        # Add decisions to result
        step_result["decisions"] = negotiation_result.get("decisions_explained", [])
        
        # Update data generator tick
        self.data_generator.update_tick()
        
        return step_result
    
    def _sync_global_state(self):
        """Sync all agent states to global state"""
        for h_id, hospital in self.hospitals.items():
            self.global_state.update_hospital(h_id, hospital.get_state())
        
        for a_id, ambulance in self.ambulances.items():
            self.global_state.update_ambulance(a_id, ambulance.get_state())
        
        if self.supply:
            self.global_state.update_supply(self.supply.get_state())
        
        if self.government:
            self.global_state.update_government(self.government.get_state())
    
    def get_state(self) -> Dict[str, Any]:
        """Get full system state for API"""
        return {
            "tick": self.tick,
            "running": self.running,
            "hospitals": {h_id: h.get_state() for h_id, h in self.hospitals.items()},
            "ambulances": {a_id: a.get_state() for a_id, a in self.ambulances.items()},
            "supply": self.supply.get_state() if self.supply else {},
            "government": self.government.get_state() if self.government else {},
            "waiting_patients": len([p for p in self.waiting_patients if p["status"] == "waiting"]),
            "total_patients": len(self.waiting_patients),
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.get_current_metrics()
    
    def get_decisions(self, limit: int = 20) -> List[Dict]:
        """Get recent decisions with explanations"""
        return self.explainer.get_recent_explanations(limit)
    
    def get_comparison(self) -> Dict[str, Any]:
        """Get before/after comparison"""
        return self.global_state.get_before_after_comparison()
    
    def get_improvement_summary(self) -> Dict[str, Any]:
        """Get improvement summary for dashboard"""
        return self.metrics.get_improvement_summary()
    
    def get_failure_status(self) -> Dict[str, Any]:
        """Get current failure status"""
        return self.failure_handler.get_failure_summary()
    
    def get_timeline(self) -> List[Dict]:
        """Get event timeline"""
        return self.logger.get_timeline()
