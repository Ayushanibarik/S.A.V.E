"""
Demo Scenario Configuration: Flood in District X
Enhanced with medically-realistic values and clinical parameters
"""

from typing import Dict, List, Any

# Scenario Metadata
SCENARIO_NAME = "Flood in District X"
SCENARIO_DESCRIPTION = "Major flooding has caused 120+ injuries across the district. Mass-casualty incident declared."

# ============================================================================
# HOSPITAL CONFIGURATIONS
# Values based on standard hospital capacity and staffing guidelines
# Oxygen in liters, reflecting realistic portable and bulk tank capacity
# ============================================================================

HOSPITALS_CONFIG: List[Dict[str, Any]] = [
    {
        "id": "hospital_a",
        "name": "City General Hospital",
        "location": (25, 30),
        "total_beds": 100,
        "available_beds": 10,  # At surge capacity
        "icu_beds": 10,
        "icu_available": 1,   # Critical care nearly saturated
        "oxygen_units": 3000,  # ~3 E-cylinders worth (critical reserve)
        "doctors_on_duty": 12,
        "nurses_on_duty": 36,  # Standard 1:3 ratio with physicians
        "patient_inflow_rate": 8,  # ESI-2/3 patients per tick (mass casualty)
        "trauma_center": True,
        "helipad": True,
    },
    {
        "id": "hospital_b",
        "name": "District Medical Center",
        "location": (60, 45),
        "total_beds": 80,
        "available_beds": 45,  # Significant capacity available
        "icu_beds": 8,
        "icu_available": 6,   # ICU capacity available for transfers
        "oxygen_units": 8000,  # Adequate bulk supply (~8 hours at surge)
        "doctors_on_duty": 8,
        "nurses_on_duty": 24,
        "patient_inflow_rate": 2,  # Normal baseline
        "trauma_center": False,
        "helipad": False,
    },
    {
        "id": "hospital_c",
        "name": "Emergency Care Unit",
        "location": (40, 70),
        "total_beds": 50,
        "available_beds": 20,
        "icu_beds": 4,
        "icu_available": 0,   # ICU at capacity - no critical admits
        "oxygen_units": 4000,  # Moderate reserve
        "doctors_on_duty": 6,
        "nurses_on_duty": 18,
        "patient_inflow_rate": 3,
        "trauma_center": False,
        "helipad": False,
    },
]

# ============================================================================
# AMBULANCE CONFIGURATIONS
# Capacity, fuel, and positioning for emergency response
# ============================================================================

AMBULANCES_CONFIG: List[Dict[str, Any]] = [
    {"id": "AMB-1", "location": (30, 35), "capacity": 2, "fuel": 0.9, "available": True, "type": "ALS"},
    {"id": "AMB-2", "location": (55, 40), "capacity": 2, "fuel": 0.75, "available": True, "type": "ALS"},
    {"id": "AMB-3", "location": (45, 65), "capacity": 2, "fuel": 0.85, "available": True, "type": "BLS"},
    {"id": "AMB-4", "location": (20, 50), "capacity": 2, "fuel": 0.6, "available": True, "type": "BLS"},
    {"id": "AMB-5", "location": (70, 30), "capacity": 2, "fuel": 0.95, "available": True, "type": "ALS"},
]

# ============================================================================
# SUPPLY CHAIN CONFIGURATION
# Central depot inventory for emergency medical supplies
# ============================================================================

SUPPLY_CONFIG: Dict[str, Any] = {
    "id": "supply_central",
    "name": "Central Supply Depot",
    "location": (50, 50),
    "inventory": {
        "oxygen": 20000,        # Liters (sufficient for ~10 hours at surge)
        "blood_products": 200,   # Units (O-negative + typed)
        "medications": 500,      # Standard emergency kits
        "iv_fluids": 1000,       # Bags of NS/LR
        "water": 1000,           # Liters potable water
        "food": 500,             # MRE equivalents
    },
    "delivery_vehicles": 4,
    "max_delivery_capacity": 100,  # Units per delivery
}

# ============================================================================
# GOVERNMENT/AUTHORITY CONFIGURATION
# Regional authority settings and policy rules
# ============================================================================

GOVERNMENT_CONFIG: Dict[str, Any] = {
    "id": "regional_authority",
    "disaster_severity": 0.8,  # 80% severity (major incident)
    "incident_type": "flood",
    "priority_rules": {
        "critical_patients_first": True,
        "balance_hospital_load": True,
        "preserve_oxygen_reserves": True,
        "golden_hour_compliance": True,
        "mutual_aid_activated": False,
    },
    "fairness_weight": 0.7,
    "escalation_threshold_icu": 0,  # Escalate when regional ICU hits 0
}

# ============================================================================
# INITIAL CASUALTIES
# Patient distribution by ESI level for mass-casualty scenario
# ESI-1: Immediate/resuscitation
# ESI-2: Emergent
# ESI-3: Urgent
# ESI-4: Less urgent
# ESI-5: Non-urgent
# ============================================================================

INITIAL_CASUALTIES: List[Dict[str, Any]] = [
    # ESI-1: 10 patients (immediate - drowning recovery, cardiac arrest)
    {"id": f"patient_{i}", "esi_level": 1, "severity": "critical", "location": (20 + i*2, 25 + i)} 
    for i in range(10)
] + [
    # ESI-2: 20 patients (emergent - severe trauma, hypothermia)
    {"id": f"patient_{i+10}", "esi_level": 2, "severity": "critical", "location": (25 + i*2, 30 + i)} 
    for i in range(20)
] + [
    # ESI-3: 40 patients (urgent - fractures, lacerations requiring sutures)
    {"id": f"patient_{i+30}", "esi_level": 3, "severity": "high", "location": (35 + i*2, 40 + i)} 
    for i in range(40)
] + [
    # ESI-4: 30 patients (less urgent - minor injuries, contusions)
    {"id": f"patient_{i+70}", "esi_level": 4, "severity": "medium", "location": (50 + i, 55 + i%10)} 
    for i in range(30)
] + [
    # ESI-5: 20 patients (non-urgent - minor issues, anxiety, shelter needs)
    {"id": f"patient_{i+100}", "esi_level": 5, "severity": "low", "location": (60 + i%15, 60 + i%8)} 
    for i in range(20)
]

# ============================================================================
# DISASTER ZONES
# Geographic areas of impact with severity levels
# ============================================================================

DISASTER_ZONES = [
    {"center": (25, 30), "radius": 15, "severity": "critical", "description": "Flash flood impact zone"},
    {"center": (40, 50), "radius": 20, "severity": "high", "description": "Building collapse area"},
    {"center": (60, 35), "radius": 10, "severity": "medium", "description": "Secondary flooding"},
]

# ============================================================================
# RESPONSE TIME TARGETS (minutes)
# Based on EMS and trauma care standards
# ============================================================================

RESPONSE_TARGETS = {
    1: 0,   # ESI-1: Immediate
    2: 10,  # ESI-2: 10 minutes
    3: 30,  # ESI-3: 30 minutes
    4: 60,  # ESI-4: 60 minutes
    5: 120, # ESI-5: 2 hours acceptable
}
