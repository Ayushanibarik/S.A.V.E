/**
 * API Client for S.A.V.E Backend
 * Handles all communication with the FastAPI backend
 */

const API_BASE = 'http://localhost:8000';

class ApiClient {
    constructor(baseUrl = API_BASE) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                ...options,
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Simulation Control
    async startSimulation() {
        return this.request('/simulate/start', { method: 'POST' });
    }

    async stepSimulation() {
        return this.request('/simulate/step', { method: 'POST' });
    }

    async runSimulation(ticks = 5) {
        return this.request(`/simulate/run/${ticks}`, { method: 'POST' });
    }

    async resetSimulation() {
        return this.request('/simulate/reset', { method: 'POST' });
    }

    // State Retrieval
    async getState() {
        return this.request('/state');
    }

    async getMetrics() {
        return this.request('/metrics');
    }

    async getDecisions(limit = 20) {
        return this.request(`/decisions?limit=${limit}`);
    }

    async getComparison() {
        return this.request('/comparison');
    }

    async getFailures() {
        return this.request('/failures');
    }

    async getTimeline() {
        return this.request('/timeline');
    }

    // Individual Resources
    async getHospitals() {
        return this.request('/hospitals');
    }

    async getAmbulances() {
        return this.request('/ambulances');
    }

    async getSupply() {
        return this.request('/supply');
    }

    async getGovernment() {
        return this.request('/government');
    }
}

export const api = new ApiClient();
export default api;
