// ============================================================================
// SmartTraffic Application Main Bootstrap
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  console.log("Initializing SmartTraffic OS + DBMS PBL Platform...");

  // Initialize Map
  TrafficMap.init('leaflet-map');

  // Initialize Simulation Engine Controller
  SimulationApp.init();

  // Initialize Comparative Analytics & OS Synchronization Inspector
  AnalyticsApp.init();

  console.log("SmartTraffic System Initialized Successfully.");
});
