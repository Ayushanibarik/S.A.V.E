import React from 'react';

/**
 * SupplyStatus - Displays supply chain inventory and delivery status
 */
export function SupplyStatus({ supply }) {
    if (!supply || !supply.inventory) {
        return (
            <div className="card">
                <div className="card-header">
                    <span className="card-title">📦 Supply Chain</span>
                </div>
                <div className="loading">Loading supply data...</div>
            </div>
        );
    }

    const getStatusColor = (status) => {
        if (status === 'critical') return 'var(--status-critical)';
        if (status === 'low') return 'var(--status-warning)';
        return 'var(--status-normal)';
    };

    const inventoryStatus = supply.inventory_status || {};

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">📦 Supply Chain</span>
                <span className="status-badge info">
                    {supply.vehicles_available}/{supply.delivery_vehicles} Vehicles
                </span>
            </div>

            <div className="supply-grid">
                <div className="supply-item">
                    <div className="supply-value" style={{ color: getStatusColor(inventoryStatus.oxygen) }}>
                        {supply.inventory.oxygen}
                    </div>
                    <div className="supply-label">Oxygen</div>
                </div>
                <div className="supply-item">
                    <div className="supply-value" style={{ color: getStatusColor(inventoryStatus.medicine) }}>
                        {supply.inventory.medicine}
                    </div>
                    <div className="supply-label">Medicine</div>
                </div>
                <div className="supply-item">
                    <div className="supply-value" style={{ color: getStatusColor(inventoryStatus.food) }}>
                        {supply.inventory.food}
                    </div>
                    <div className="supply-label">Food</div>
                </div>
                <div className="supply-item">
                    <div className="supply-value" style={{ color: getStatusColor(inventoryStatus.water) }}>
                        {supply.inventory.water}
                    </div>
                    <div className="supply-label">Water</div>
                </div>
            </div>

            <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Active Deliveries: {supply.active_deliveries || 0} •
                Pending: {supply.pending_requests || 0} •
                Completed: {supply.completed_deliveries || 0}
            </div>
        </div>
    );
}

export default SupplyStatus;
