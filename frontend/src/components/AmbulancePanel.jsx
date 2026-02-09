import React from 'react';

/**
 * AmbulancePanel - Shows ambulance status and current missions
 */
export function AmbulancePanel({ ambulances }) {
    const ambulanceList = Object.values(ambulances || {});

    const getStatusIcon = (status) => {
        switch (status) {
            case 'idle': return '🟢';
            case 'en_route_pickup': return '🔵';
            case 'en_route_hospital': return '🟠';
            default: return '⚪';
        }
    };

    const getStatusText = (ambulance) => {
        if (ambulance.status === 'idle') return 'Available';
        if (ambulance.status === 'en_route_pickup') return `Picking up patient`;
        if (ambulance.status === 'en_route_hospital') return `→ ${ambulance.target_hospital || 'Hospital'}`;
        return ambulance.status;
    };

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">🚑 Ambulances</span>
                <span className="status-badge info">
                    {ambulanceList.filter(a => a.available).length}/{ambulanceList.length} Available
                </span>
            </div>

            <div className="ambulance-list">
                {ambulanceList.map((ambulance) => (
                    <div key={ambulance.id} className="ambulance-item">
                        <div>
                            <span className="ambulance-id">
                                {getStatusIcon(ambulance.status)} {ambulance.id.toUpperCase()}
                            </span>
                            <div className="ambulance-status">
                                {getStatusText(ambulance)}
                                {ambulance.eta_minutes > 0 && ` (ETA: ${ambulance.eta_minutes}min)`}
                            </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '0.75rem', color: ambulance.fuel < 30 ? 'var(--status-warning)' : 'var(--text-muted)' }}>
                                ⛽ {ambulance.fuel}%
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                {ambulance.patients_delivered} delivered
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default AmbulancePanel;
