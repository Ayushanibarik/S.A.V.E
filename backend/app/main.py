"""
S.A.V.E - Multi-Agent Disaster Response System
FastAPI Backend Entry Point

Endpoints:
- POST /simulate/start - Initialize simulation
- POST /simulate/step - Advance one tick
- GET /state - Current system state
- GET /metrics - Performance metrics
- GET /decisions - Recent decisions with explanations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import asyncio

from .simulation.simulator import Simulator

# Initialize FastAPI app
app = FastAPI(
    title="S.A.V.E - Disaster Response AI",
    description="Multi-Agent AI for Disaster Response Coordination",
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global simulator instance
simulator = Simulator()


@app.get("/")
async def root():
    """Health check and welcome message"""
    return {
        "name": "S.A.V.E - Disaster Response AI",
        "status": "online",
        "description": "Multi-Agent AI for coordinating hospitals, ambulances, supplies, and authorities during disasters",
        "pitch": "Disaster response fails not because of lack of resources, but lack of coordination.",
    }


@app.post("/simulate/start")
async def start_simulation():
    """Initialize a new simulation with the demo scenario"""
    try:
        result = simulator.initialize()
        return {
            "success": True,
            "message": "Simulation initialized successfully",
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate/step")
async def simulation_step():
    """Execute one simulation tick"""
    try:
        result = simulator.step()
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate/run/{ticks}")
async def run_simulation(ticks: int = 5):
    """Run multiple simulation ticks"""
    if ticks < 1 or ticks > 20:
        raise HTTPException(status_code=400, detail="Ticks must be between 1 and 20")
    
    results = []
    for _ in range(ticks):
        result = simulator.step()
        results.append(result)
    
    return {
        "success": True,
        "ticks_executed": ticks,
        "final_tick": simulator.tick,
        "results": results,
    }


@app.get("/state")
async def get_state():
    """Get current system state for dashboard"""
    try:
        state = simulator.get_state()
        return {
            "success": True,
            **state,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get current performance metrics"""
    try:
        metrics = simulator.get_metrics()
        improvement = simulator.get_improvement_summary()
        
        return {
            "success": True,
            "current": metrics,
            "improvement": improvement,
            "summary": simulator.metrics.generate_judge_summary(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/decisions")
async def get_decisions(limit: int = 20):
    """Get recent decisions with explanations"""
    try:
        decisions = simulator.get_decisions(limit)
        return {
            "success": True,
            "count": len(decisions),
            "decisions": decisions,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/comparison")
async def get_comparison():
    """Get before/after comparison of last optimization"""
    try:
        comparison = simulator.get_comparison()
        return {
            "success": True,
            **comparison,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/failures")
async def get_failures():
    """Get current failure status and alerts"""
    try:
        failures = simulator.get_failure_status()
        return {
            "success": True,
            **failures,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/timeline")
async def get_timeline():
    """Get event timeline for replay"""
    try:
        timeline = simulator.get_timeline()
        return {
            "success": True,
            "timeline": timeline,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hospitals")
async def get_hospitals():
    """Get all hospital states"""
    try:
        hospitals = {h_id: h.get_state() for h_id, h in simulator.hospitals.items()}
        return {
            "success": True,
            "count": len(hospitals),
            "hospitals": hospitals,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ambulances")
async def get_ambulances():
    """Get all ambulance states"""
    try:
        ambulances = {a_id: a.get_state() for a_id, a in simulator.ambulances.items()}
        return {
            "success": True,
            "count": len(ambulances),
            "ambulances": ambulances,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/supply")
async def get_supply():
    """Get supply chain state"""
    try:
        supply = simulator.supply.get_state() if simulator.supply else {}
        return {
            "success": True,
            **supply,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/government")
async def get_government():
    """Get government agent state and policies"""
    try:
        gov = simulator.government.get_state() if simulator.government else {}
        return {
            "success": True,
            **gov,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/simulate/reset")
async def reset_simulation():
    """Reset simulation to initial state"""
    try:
        simulator.reset()
        return {
            "success": True,
            "message": "Simulation reset successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# For running with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
