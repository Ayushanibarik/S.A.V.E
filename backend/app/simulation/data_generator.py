"""
Data Generator: Creates fake disaster data for simulation
Generates injuries, severity levels, demand spikes, and patient inflow
"""

import random
from typing import Dict, List, Any, Tuple
from datetime import datetime
import math


class DataGenerator:
    """
    Generates simulated disaster data for the S.A.V.E system.
    Creates realistic patterns of injuries, demands, and events.
    """
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
        self.tick = 0
    
    def generate_initial_casualties(self, count: int, disaster_zones: List[Dict]) -> List[Dict[str, Any]]:
        """Generate initial casualty list based on disaster zones"""
        casualties = []
        severity_distribution = {"critical": 0.15, "high": 0.30, "medium": 0.35, "low": 0.20}
        
        for i in range(count):
            # Pick a random zone weighted by severity
            zone = random.choice(disaster_zones)
            
            # Generate location near zone center
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, zone["radius"])
            location = (
                zone["center"][0] + distance * math.cos(angle),
                zone["center"][1] + distance * math.sin(angle)
            )
            
            # Determine severity
            severity = self._weighted_choice(severity_distribution)
            
            casualties.append({
                "id": f"patient_{i:03d}",
                "severity": severity,
                "location": location,
                "zone": zone["severity"],
                "status": "waiting",
                "assigned_ambulance": None,
                "assigned_hospital": None,
                "created_at": datetime.now().isoformat(),
            })
        
        return casualties
    
    def _weighted_choice(self, weights: Dict[str, float]) -> str:
        """Make a weighted random choice"""
        total = sum(weights.values())
        r = random.uniform(0, total)
        cumulative = 0
        for key, weight in weights.items():
            cumulative += weight
            if r <= cumulative:
                return key
        return list(weights.keys())[-1]
    
    def generate_patient_inflow(self, base_rate: float, severity_multiplier: float = 1.0) -> List[Dict[str, Any]]:
        """Generate new patients for a simulation tick"""
        # Poisson-like distribution for patient arrivals
        num_new = max(0, int(random.gauss(base_rate * severity_multiplier, base_rate * 0.3)))
        
        new_patients = []
        for i in range(num_new):
            severity = self._weighted_choice({
                "critical": 0.10 * severity_multiplier,
                "high": 0.25,
                "medium": 0.40,
                "low": 0.25
            })
            
            new_patients.append({
                "id": f"patient_tick{self.tick}_{i:02d}",
                "severity": severity,
                "location": (random.uniform(10, 90), random.uniform(10, 90)),
                "status": "waiting",
                "created_at": datetime.now().isoformat(),
            })
        
        return new_patients
    
    def generate_supply_demand(self, hospitals: Dict) -> Dict[str, int]:
        """Generate supply demand based on hospital states"""
        total_demand = {
            "oxygen": 0,
            "medicine": 0,
            "food": 0,
            "water": 0,
        }
        
        for h_id, h_state in hospitals.items():
            # Oxygen demand based on ICU usage
            icu_usage = 1 - (h_state.get("icu_available", 1) / max(h_state.get("icu_beds", 1), 1))
            total_demand["oxygen"] += int(20 * icu_usage + random.randint(5, 15))
            
            # Medicine demand based on patient count
            patient_load = 1 - (h_state.get("available_beds", 1) / max(h_state.get("total_beds", 1), 1))
            total_demand["medicine"] += int(10 * patient_load + random.randint(2, 8))
            
            # Basic supplies
            total_demand["food"] += random.randint(10, 30)
            total_demand["water"] += random.randint(20, 50)
        
        return total_demand
    
    def generate_disaster_event(self) -> Dict[str, Any]:
        """Generate a random disaster event that affects the simulation"""
        event_types = [
            {"type": "aftershock", "severity_increase": 0.2, "duration": 3},
            {"type": "road_blocked", "affected_routes": 2, "duration": 5},
            {"type": "power_outage", "affected_hospitals": 1, "duration": 4},
            {"type": "supply_delay", "delay_minutes": 30, "duration": 2},
            {"type": "casualty_surge", "extra_patients": 15, "duration": 1},
        ]
        
        if random.random() < 0.15:  # 15% chance of event per tick
            event = random.choice(event_types)
            event["tick"] = self.tick
            event["timestamp"] = datetime.now().isoformat()
            return event
        
        return None
    
    def update_tick(self):
        """Advance to next simulation tick"""
        self.tick += 1
    
    def calculate_travel_time(self, from_loc: Tuple[float, float], to_loc: Tuple[float, float], speed: float = 40) -> float:
        """Calculate travel time between two points in minutes"""
        distance = math.sqrt((to_loc[0] - from_loc[0])**2 + (to_loc[1] - from_loc[1])**2)
        # Assume 1 unit = 1 km, speed in km/h
        time_hours = distance / speed
        return time_hours * 60  # Return in minutes
    
    def generate_ambulance_eta(self, ambulance_loc: Tuple, patient_loc: Tuple, hospital_loc: Tuple) -> Dict[str, float]:
        """Calculate ETA for ambulance pickup and hospital delivery"""
        pickup_time = self.calculate_travel_time(ambulance_loc, patient_loc)
        delivery_time = self.calculate_travel_time(patient_loc, hospital_loc)
        
        return {
            "pickup_eta": round(pickup_time, 1),
            "delivery_eta": round(pickup_time + delivery_time, 1),
            "total_time": round(pickup_time + delivery_time, 1),
        }
