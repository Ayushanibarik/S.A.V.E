import React from 'react';

/**
 * HospitalCard - Displays hospital status with bed/ICU/oxygen info
 */
export function HospitalCard({ hospital }) {
    const getStatusClass = () => {
        if (hospital.status === 'critical') return 'critical';
        if (hospital.status === 'warning') return 'warning';
        return 'normal';
    };

    const getProgressColor = (utilization) => {
        if (utilization >= 85) return 'critical';
        if (utilization >= 70) return 'warning';
        return 'normal';
    };

    return (
        <div className={`card hospital-card ${hospital.is_critical ? 'critical' : ''}`}>
            <div className="card-header">
                <span className="hospital-name">{hospital.name}</span>
                <span className={`status-badge ${getStatusClass()}`}>
                    {hospital.status}
                </span>
            </div>

            {/* Bed Utilization */}
            <div className="stat-item" style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span className="stat-label">Beds</span>
                    <span className="stat-value" style={{ fontSize: '0.875rem' }}>
                        {hospital.available_beds}/{hospital.total_beds}
                    </span>
                </div>
                <div className="progress-bar">
                    <div
                        className={`progress-fill ${getProgressColor(hospital.bed_utilization)}`}
                        style={{ width: `${hospital.bed_utilization}%` }}
                    />
                </div>
            </div>

            <div className="hospital-stats">
                <div className="stat-item">
                    <span className="stat-value">{hospital.icu_available}/{hospital.icu_beds}</span>
                    <span className="stat-label">ICU Available</span>
                </div>
                <div className="stat-item">
                    <span className={`stat-value ${hospital.oxygen_units < 30 ? 'pulse' : ''}`}
                        style={{ color: hospital.oxygen_units < 30 ? 'var(--status-critical)' : 'inherit' }}>
                        {hospital.oxygen_units}
                    </span>
                    <span className="stat-label">Oxygen Units</span>
                </div>
                <div className="stat-item">
                    <span className="stat-value">{hospital.doctors_on_duty}</span>
                    <span className="stat-label">Doctors</span>
                </div>
                <div className="stat-item">
                    <span className="stat-value">{hospital.patients_count || 0}</span>
                    <span className="stat-label">Patients</span>
                </div>
            </div>
        </div>
    );
}

export default HospitalCard;
