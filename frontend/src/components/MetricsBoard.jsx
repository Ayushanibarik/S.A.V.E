import React from 'react';

/**
 * MetricsBoard - Displays key performance metrics
 */
export function MetricsBoard({ metrics, improvement }) {
    if (!metrics) {
        return (
            <div className="card">
                <div className="card-header">
                    <span className="card-title">📊 Live Metrics</span>
                </div>
                <div className="loading">Waiting for simulation...</div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">📊 Live Metrics</span>
            </div>

            <div className="metrics-panel">
                <div className="metric-card highlight">
                    <div className="metric-value">{metrics.lives_saved}</div>
                    <div className="metric-label">Lives Saved</div>
                </div>
                <div className="metric-card">
                    <div className="metric-value">{metrics.patients_served}</div>
                    <div className="metric-label">Patients Served</div>
                </div>
                <div className="metric-card">
                    <div className="metric-value">{metrics.overloads_prevented}</div>
                    <div className="metric-label">Overloads Prevented</div>
                </div>
                <div className="metric-card">
                    <div className="metric-value">{metrics.average_response_time_min || 0}</div>
                    <div className="metric-label">Avg Response (min)</div>
                </div>
            </div>

            {improvement && improvement.patients_handled_percentage > 0 && (
                <div style={{
                    marginTop: '1rem',
                    padding: '0.75rem',
                    background: 'var(--status-normal-bg)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.85rem',
                    color: 'var(--status-normal)'
                }}>
                    ✓ {improvement.patients_handled_percentage}% of patients served •
                    {improvement.critical_saved_percentage}% critical cases handled
                </div>
            )}
        </div>
    );
}

export default MetricsBoard;
