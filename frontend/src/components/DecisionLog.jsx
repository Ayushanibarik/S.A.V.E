import React from 'react';

/**
 * DecisionLog - Scrolling log of decisions with explanations
 */
export function DecisionLog({ decisions }) {
    if (!decisions || decisions.length === 0) {
        return (
            <div className="card">
                <div className="card-header">
                    <span className="card-title">📋 Decision Log</span>
                </div>
                <div style={{ padding: '1rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                    No decisions yet. Start the simulation to see live decisions.
                </div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">📋 Decision Log</span>
                <span className="status-badge info">{decisions.length} decisions</span>
            </div>

            <div className="decision-log">
                {[...decisions].reverse().map((decision, idx) => (
                    <div
                        key={idx}
                        className={`decision-item ${decision.type} slide-in`}
                    >
                        {decision.short || decision.text}
                    </div>
                ))}
            </div>
        </div>
    );
}

export default DecisionLog;
