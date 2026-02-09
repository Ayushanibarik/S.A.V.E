import React, { useState, useEffect, useCallback } from 'react';
import { api } from './api/client';
import { HospitalCard } from './components/HospitalCard';
import { AmbulancePanel } from './components/AmbulancePanel';
import { SupplyStatus } from './components/SupplyStatus';
import { MetricsBoard } from './components/MetricsBoard';
import { DecisionLog } from './components/DecisionLog';

/**
 * S.A.V.E Dashboard - Main Application
 * Multi-Agent AI for Disaster Response Coordination
 */
function App() {
    // State
    const [state, setState] = useState(null);
    const [metrics, setMetrics] = useState(null);
    const [improvement, setImprovement] = useState(null);
    const [decisions, setDecisions] = useState([]);
    const [isRunning, setIsRunning] = useState(false);
    const [tick, setTick] = useState(0);
    const [error, setError] = useState(null);
    const [autoRun, setAutoRun] = useState(false);

    // Fetch all data
    const fetchData = useCallback(async () => {
        try {
            const [stateRes, metricsRes, decisionsRes] = await Promise.all([
                api.getState(),
                api.getMetrics(),
                api.getDecisions(20),
            ]);

            setState(stateRes);
            setMetrics(metricsRes.current);
            setImprovement(metricsRes.improvement);
            setDecisions(decisionsRes.decisions || []);
            setTick(stateRes.tick || 0);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch data:', err);
            setError('Failed to connect to backend. Make sure the server is running.');
        }
    }, []);

    // Initialize simulation
    const handleStart = async () => {
        try {
            setError(null);
            await api.startSimulation();
            await fetchData();
            setIsRunning(true);
        } catch (err) {
            setError('Failed to start simulation');
        }
    };

    // Step simulation
    const handleStep = async () => {
        try {
            await api.stepSimulation();
            await fetchData();
        } catch (err) {
            setError('Failed to step simulation');
        }
    };

    // Reset simulation
    const handleReset = async () => {
        try {
            await api.resetSimulation();
            setState(null);
            setMetrics(null);
            setDecisions([]);
            setTick(0);
            setIsRunning(false);
            setAutoRun(false);
        } catch (err) {
            setError('Failed to reset simulation');
        }
    };

    // Auto-run effect
    useEffect(() => {
        let interval;
        if (autoRun && isRunning) {
            interval = setInterval(async () => {
                await handleStep();
            }, 1500); // Step every 1.5 seconds
        }
        return () => clearInterval(interval);
    }, [autoRun, isRunning]);

    // Initial check
    useEffect(() => {
        api.getState().then(() => {
            // Backend is available
        }).catch(() => {
            setError('Backend not available. Start the server with: cd backend && uvicorn app.main:app --reload');
        });
    }, []);

    return (
        <div className="dashboard">
            {/* Header */}
            <header className="dashboard-header">
                <div className="dashboard-title">
                    <h1>S.A.V.E</h1>
                    <span className="subtitle">Multi-Agent Disaster Response Coordination</span>
                </div>

                <div className="dashboard-controls">
                    <div className="tick-counter">
                        <span>Tick:</span>
                        <span className="tick-number">{tick}</span>
                    </div>

                    {!isRunning ? (
                        <button className="btn btn-primary" onClick={handleStart}>
                            ▶ Start Simulation
                        </button>
                    ) : (
                        <>
                            <button className="btn btn-secondary" onClick={handleStep} disabled={autoRun}>
                                ⏭ Step
                            </button>
                            <button
                                className={`btn ${autoRun ? 'btn-danger' : 'btn-primary'}`}
                                onClick={() => setAutoRun(!autoRun)}
                            >
                                {autoRun ? '⏹ Stop Auto' : '⏯ Auto Run'}
                            </button>
                            <button className="btn btn-secondary" onClick={handleReset}>
                                ↺ Reset
                            </button>
                        </>
                    )}
                </div>
            </header>

            {/* Error Alert */}
            {error && (
                <div className="alert critical" style={{ gridColumn: 'span 12' }}>
                    ⚠️ {error}
                </div>
            )}

            {/* Main Dashboard */}
            <main className="dashboard-main">
                {/* Hospitals Grid */}
                <section className="hospitals-grid">
                    {state && state.hospitals ? (
                        Object.values(state.hospitals).map((hospital) => (
                            <HospitalCard key={hospital.id} hospital={hospital} />
                        ))
                    ) : (
                        <div className="card" style={{ gridColumn: 'span 3' }}>
                            <div className="loading">
                                <div className="spinner"></div>
                            </div>
                        </div>
                    )}
                </section>

                {/* Sidebar */}
                <aside className="sidebar">
                    {/* Metrics */}
                    <MetricsBoard metrics={metrics} improvement={improvement} />

                    {/* Ambulances */}
                    {state && (
                        <AmbulancePanel ambulances={state.ambulances} />
                    )}

                    {/* Supply Chain */}
                    {state && (
                        <SupplyStatus supply={state.supply} />
                    )}

                    {/* Decision Log */}
                    <DecisionLog decisions={decisions} />
                </aside>
            </main>
        </div>
    );
}

export default App;
