// ============================================================================
// SmartTraffic API Client
// ============================================================================

const API_BASE = '/api';

const Api = {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    try {
      const response = await fetch(url, { ...options, headers });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || `HTTP error ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  // Junctions
  getJunctions() {
    return this.request('/junctions');
  },
  getJunction(id) {
    return this.request(`/junctions/${id}`);
  },

  // Roads
  getRoads() {
    return this.request('/roads');
  },
  toggleRoadClosure(id) {
    return this.request(`/roads/${id}/toggle-closure`, { method: 'POST' });
  },

  // Vehicles
  getVehicles(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/vehicles${query ? '?' + query : ''}`);
  },
  createVehicle(vehicleData) {
    return this.request('/vehicles', {
      method: 'POST',
      body: JSON.stringify(vehicleData),
    });
  },
  createVehiclesBatch(data) {
    return this.request('/vehicles/batch', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  updateVehicle(id, data) {
    return this.request(`/vehicles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  deleteVehicle(id) {
    return this.request(`/vehicles/${id}`, { method: 'DELETE' });
  },
  clearVehicles(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/vehicles/clear${query ? '?' + query : ''}`, { method: 'POST' });
  },


  // Simulations
  getSimulations() {
    return this.request('/simulations');
  },
  createSimulation(data) {
    return this.request('/simulations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  startSimulation(id, payload = {}) {
    return this.request(`/simulations/${id}/start`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  pauseSimulation(id) {
    return this.request(`/simulations/${id}/pause`, { method: 'POST' });
  },
  resumeSimulation(id) {
    return this.request(`/simulations/${id}/resume`, { method: 'POST' });
  },
  resetSimulation(id) {
    return this.request(`/simulations/${id}/reset`, { method: 'POST' });
  },
  getSimulationState(id) {
    return this.request(`/simulations/${id}/state`);
  },

  // Signals
  setManualSignal(data) {
    return this.request('/signals/manual', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  setAutomaticSignal(data) {
    return this.request('/signals/automatic', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Incidents
  getIncidents(simId) {
    const query = simId ? `?simulation_id=${simId}` : '';
    return this.request(`/incidents${query}`);
  },
  createIncident(data) {
    return this.request('/incidents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  resolveIncident(id) {
    return this.request(`/incidents/${id}/resolve`, { method: 'PUT' });
  },

  // Analytics
  getAnalyticsSummary() {
    return this.request('/analytics');
  },
  getAnalyticsBenchmark(simId = 1, quantum = 2) {
    return this.request(`/analytics/compare?simulation_id=${simId}&quantum=${quantum}`);
  },

  // System
  runSyncTest() {
    return this.request('/system/sync-test');
  },
  getHealth() {
    return this.request('/system/health');
  },
};
