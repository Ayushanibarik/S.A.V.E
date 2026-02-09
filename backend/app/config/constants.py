"""
System-wide constants for S.A.V.E Disaster Response System
Enhanced with medical-grade standards and clinical protocols
"""

# Simulation Settings
SIMULATION_TICK_INTERVAL = 5  # seconds between simulation steps
MAX_SIMULATION_TICKS = 100

# ============================================================================
# EMERGENCY SEVERITY INDEX (ESI) - Standard 5-level triage system
# Based on AHRQ Emergency Severity Index Guidelines
# ============================================================================
ESI_LEVELS = {
    1: {
        "name": "Resuscitation",
        "description": "Immediate life-saving intervention required",
        "examples": ["Cardiac arrest", "Respiratory failure", "Severe trauma"],
        "target_response_min": 0,  # Immediate
        "priority_weight": 1.0,
    },
    2: {
        "name": "Emergent",
        "description": "High-risk situation or severe pain/distress",
        "examples": ["Acute MI", "Stroke", "Major fractures", "Severe burns"],
        "target_response_min": 10,  # Golden hour critical
        "priority_weight": 0.85,
    },
    3: {
        "name": "Urgent",
        "description": "Requires multiple resources, stable vitals",
        "examples": ["Moderate lacerations", "Abdominal pain", "High fever"],
        "target_response_min": 30,
        "priority_weight": 0.6,
    },
    4: {
        "name": "Less Urgent",
        "description": "Requires one resource, non-urgent condition",
        "examples": ["Minor fractures", "Sprains", "Simple lacerations"],
        "target_response_min": 60,
        "priority_weight": 0.35,
    },
    5: {
        "name": "Non-Urgent",
        "description": "Requires no resources, could be seen in primary care",
        "examples": ["Minor cuts", "Cold symptoms", "Prescription refills"],
        "target_response_min": 120,
        "priority_weight": 0.15,
    },
}

# Legacy severity mapping (for backward compatibility)
SEVERITY_TO_ESI = {
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
    "minor": 5,
}

ESI_TO_SEVERITY = {v: k for k, v in SEVERITY_TO_ESI.items()}

# Priority Levels (legacy support, now derived from ESI)
PRIORITY_CRITICAL = ESI_LEVELS[1]["priority_weight"]
PRIORITY_HIGH = ESI_LEVELS[2]["priority_weight"]
PRIORITY_MEDIUM = ESI_LEVELS[3]["priority_weight"]
PRIORITY_LOW = ESI_LEVELS[4]["priority_weight"]

# ============================================================================
# CLINICAL HOSPITAL THRESHOLDS
# Based on standard healthcare facility guidelines
# ============================================================================

# Bed utilization thresholds
HOSPITAL_OVERLOAD_THRESHOLD = 0.85  # 85% capacity = surge protocol warning
HOSPITAL_CRITICAL_THRESHOLD = 0.95  # 95% capacity = diversion recommended
HOSPITAL_DIVERSION_THRESHOLD = 0.98  # 98% = mandatory patient diversion

# ICU thresholds
ICU_WARNING_THRESHOLD = 0.75   # 75% ICU = escalation planning
ICU_CRITICAL_THRESHOLD = 0.90  # 90% ICU = critical care saturation
ICU_NURSE_RATIO_STANDARD = 2   # 1 nurse per 2 ICU patients (standard)
ICU_NURSE_RATIO_CRITICAL = 1   # 1:1 for critical patients

# ============================================================================
# OXYGEN MANAGEMENT
# Medical oxygen consumption rates per minute by ESI level
# ============================================================================

OXYGEN_CONSUMPTION_LPM = {
    1: 15.0,  # ESI-1: High-flow oxygen / ventilator (10-15 L/min)
    2: 8.0,   # ESI-2: Non-rebreather mask (8-10 L/min)
    3: 4.0,   # ESI-3: Simple face mask (4-6 L/min)
    4: 2.0,   # ESI-4: Nasal cannula (1-4 L/min)
    5: 0.0,   # ESI-5: No supplemental oxygen
}

# Oxygen reserve thresholds (in hours at current consumption rate)
OXYGEN_RESERVE_CRITICAL_HOURS = 4   # Less than 4 hours = critical shortage
OXYGEN_RESERVE_WARNING_HOURS = 8    # Less than 8 hours = request resupply
OXYGEN_CRITICAL_LEVEL = 20          # Legacy: minimum units for operation

# Standard medical oxygen cylinder capacities (liters)
OXYGEN_CYLINDER_CAPACITY = {
    "D": 425,     # Small portable
    "E": 680,     # Standard portable
    "M": 3450,    # Large hospital
    "H": 6900,    # Bulk hospital
}

# ============================================================================
# AMBULANCE AND TRANSPORT
# Response time targets based on emergency medical services standards
# ============================================================================

AMBULANCE_CAPACITY = 2  # patients per ambulance
AMBULANCE_SPEED_URBAN = 35   # km/h in urban areas
AMBULANCE_SPEED_RURAL = 60   # km/h in rural areas
AMBULANCE_SPEED = 40         # km/h average (legacy)

# EMS Response time targets (minutes)
RESPONSE_TIME_TARGET_URBAN = 8     # 8 minutes for urban areas
RESPONSE_TIME_TARGET_SUBURBAN = 12  # 12 minutes for suburban
RESPONSE_TIME_TARGET_RURAL = 15    # 15 minutes for rural areas

# Golden hour: 60 minutes from injury to definitive care
GOLDEN_HOUR_MINUTES = 60
PLATINUM_10_MINUTES = 10  # First 10 minutes are most critical

# Fuel and operational thresholds
FUEL_CRITICAL_LEVEL = 0.15  # 15% fuel = return to base
FUEL_WARNING_LEVEL = 0.25   # 25% fuel = plan for refuel

# ============================================================================
# SUPPLY CHAIN SETTINGS
# Based on hospital logistics standards
# ============================================================================

DELIVERY_BASE_TIME = 30  # minutes for standard delivery
PRIORITY_DELIVERY_MULTIPLIER = 0.5  # 50% faster for critical supplies

# Blood product reserves (units, targets per facility)
BLOOD_RESERVE_CRITICAL = 10    # Minimum O-negative units
BLOOD_RESERVE_TARGET = 50      # Target reserves for major facilities

# Medical supply categories
SUPPLY_CATEGORIES = {
    "oxygen": {"unit": "liters", "critical_days": 2},
    "blood_products": {"unit": "units", "critical_days": 3},
    "medications": {"unit": "doses", "critical_days": 5},
    "ppe": {"unit": "sets", "critical_days": 7},
    "iv_fluids": {"unit": "bags", "critical_days": 3},
}

# ============================================================================
# OPTIMIZATION WEIGHTS
# For multi-objective optimization function
# ============================================================================

WEIGHT_UNSERVED_CRITICAL = 10  # Highest priority: unserved ESI-1/2 patients
WEIGHT_RESPONSE_TIME = 2       # Response time compliance
WEIGHT_OVERLOAD_PENALTY = 5    # Preventing hospital surges
WEIGHT_FAIRNESS = 3            # Load distribution equity
WEIGHT_GOLDEN_HOUR = 8         # Golden hour compliance

# ============================================================================
# STAFFING RATIOS (per shift)
# Based on professional nursing standards
# ============================================================================

NURSE_PATIENT_RATIO_ED = 4      # 1 nurse per 4 ED patients
NURSE_PATIENT_RATIO_ICU = 2     # 1 nurse per 2 ICU patients (standard)
NURSE_PATIENT_RATIO_MEDSURG = 5 # 1 nurse per 5 med-surg patients
PHYSICIAN_PATIENT_RATIO_ED = 10 # 1 physician per 10 ED patients

# ============================================================================
# MAP AND GEOGRAPHY
# ============================================================================

MAP_WIDTH = 100   # km
MAP_HEIGHT = 100  # km

# ============================================================================
# AGENT TYPES
# ============================================================================

AGENT_TYPE_HOSPITAL = "hospital"
AGENT_TYPE_AMBULANCE = "ambulance"
AGENT_TYPE_SUPPLY = "supply"
AGENT_TYPE_GOVERNMENT = "government"
