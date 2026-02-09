# S.A.V.E - Multi-Agent Disaster Response AI 🚨

> **"Disaster response fails not because of lack of resources, but lack of coordination."**

## 🏆 What is This?

S.A.V.E (Smart Autonomous Virtual Emergency system) is a **multi-agent AI coordination system** that models real-world emergency decision-makers (hospitals, ambulances, supply chains, government) as autonomous agents that:

1. **Observe** their local state (beds, oxygen, fuel, inventory)
2. **Communicate** via a shared event bus
3. **Negotiate** under constraints (capacity, distance, priority)
4. **Produce** globally optimized response plans

### The Problem We Solve

Traditional disaster response suffers from **coordination collapse**:
- Hospital A is overloaded while Hospital B sits empty
- Ambulances waste time on suboptimal routes
- Supplies run out at critical locations while sitting unused elsewhere
- No one sees the full picture until it's too late

### Our Solution

A **multi-agent negotiation system** where each entity operates autonomously but collaborates toward global optimization. The system prevents chaos by finding the Nash equilibrium of resource allocation.

---

## 🚀 Quick Start

### 1. Start the Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies and run
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Open the Dashboard

Navigate to **http://localhost:5173** and click **"Start Simulation"**

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/simulate/start` | Initialize simulation |
| `POST` | `/simulate/step` | Execute one tick |
| `POST` | `/simulate/run/{n}` | Run n ticks |
| `GET` | `/state` | Full system state |
| `GET` | `/metrics` | Performance metrics |
| `GET` | `/decisions` | Decision explanations |
| `GET` | `/comparison` | Before/after comparison |
| `GET` | `/hospitals` | Hospital states |
| `GET` | `/ambulances` | Ambulance states |
| `GET` | `/supply` | Supply chain state |
| `POST` | `/simulate/reset` | Reset simulation |

---

## 🧩 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Hospital   │  │  Ambulance  │  │   Supply    │         │
│  │   Agent     │  │    Agent    │  │   Agent     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│                 ┌─────────────────┐                         │
│                 │    Event Bus    │                         │
│                 └────────┬────────┘                         │
│                          ▼                                  │
│                 ┌─────────────────┐                         │
│                 │  Negotiation    │                         │
│                 │    Engine       │                         │
│                 └────────┬────────┘                         │
│                          ▼                                  │
│                 ┌─────────────────┐                         │
│                 │  Global State   │                         │
│                 └─────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    React Dashboard                          │
│  ┌─────────────┐ ┌────────────┐ ┌─────────────────┐        │
│  │  Hospitals  │ │ Ambulances │ │  Decision Log   │        │
│  │   Cards     │ │   Panel    │ │  (Explanations) │        │
│  └─────────────┘ └────────────┘ └─────────────────┘        │
│  ┌─────────────┐ ┌────────────────────────────────┐        │
│  │   Supply    │ │       Live Metrics Board       │        │
│  │   Status    │ │   Lives Saved | Response Time  │        │
│  └─────────────┘ └────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Demo Scenario: Flood in District X

**Initial State:**
- 🏥 120 injured casualties
- 🏨 Hospital A: Overloaded (90%+ utilization)
- 🏨 Hospital B: Underutilized (40% utilization)
- ⚠️ Hospital A: Oxygen shortage imminent

**What Happens:**
1. **Tick 1-3**: System detects overload at Hospital A
2. **Tick 4-6**: Negotiation engine reroutes patients to Hospital B
3. **Tick 7-10**: Supply agent dispatches oxygen to critical hospitals
4. **Tick 11+**: System stabilizes, all critical patients served

**Result:**
- ✅ Lives saved through load balancing
- ✅ Overloads prevented
- ✅ Response time optimized
- ✅ Oxygen shortages avoided

---

## 📊 Key Metrics We Track

| Metric | Description |
|--------|-------------|
| **Lives Saved** | Critical patients successfully treated |
| **Overloads Prevented** | Hospitals saved from overflow |
| **Avg Response Time** | Time from injury to hospital admission |
| **Patients Served** | Total patients processed |
| **Reroutes** | Dynamic redirections for optimization |

---

## 🔧 Tech Stack

- **Backend**: Python, FastAPI, Pydantic
- **Frontend**: React, Vite, CSS
- **Communication**: Event Bus (pub/sub pattern)
- **State**: Singleton Global State
- **Optimization**: Greedy heuristic with weighted scoring

---

## 📁 Project Structure

```
S.A.V.E/
├── backend/
│   ├── app/
│   │   ├── agents/          # Hospital, Ambulance, Supply, Government
│   │   ├── communication/   # Event Bus, Message Schemas
│   │   ├── config/          # Constants, Scenario
│   │   ├── metrics/         # Performance tracking
│   │   ├── negotiation/     # Allocation engine
│   │   ├── optimization/    # Objective function, Constraints
│   │   ├── simulation/      # Main loop, Data generator
│   │   ├── state/           # Global state singleton
│   │   ├── utils/           # Explainer, Logger, Failure handler
│   │   └── main.py          # FastAPI entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/             # Backend client
│   │   ├── components/      # React components
│   │   ├── App.jsx          # Main dashboard
│   │   ├── index.css        # Premium dark theme
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 🏅 Why We Win

1. **Multi-Agent Architecture** - Not a single script, but autonomous collaborating entities
2. **Explainable Decisions** - Every action has a human-readable explanation
3. **Real-Time Dashboard** - Watch the magic happen live
4. **Constraint-Aware** - Respects real-world limits (beds, oxygen, fuel)
5. **Failure Resilient** - Graceful degradation protocols
6. **Quantified Impact** - Judge-friendly metrics (lives saved, overloads prevented)

---

## 👥 Team

Built with ❤️ for the hackathon by the S.A.V.E team.

---

*"In chaos, coordination is survival."*
