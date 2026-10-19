// ============================================================================
// SmartTraffic Interactive Leaflet Map Module
// ============================================================================

const TrafficMap = {
  map: null,
  junctionMarkers: {},
  roadPolylines: [],
  incidentMarkers: [],

  init(elementId = 'leaflet-map') {
    if (this.map) return;

    // Centered on Dehradun City Grid
    this.map = L.map(elementId).setView([30.318, 78.028], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors | GEU SmartTraffic',
      maxZoom: 18,
    }).addTo(this.map);
  },

  update(junctions = [], roads = [], incidents = []) {
    if (!this.map) return;

    this.renderRoads(roads, junctions);
    this.renderJunctions(junctions);
    this.renderIncidents(incidents, junctions);
  },

  renderJunctions(junctions) {
    junctions.forEach((j) => {
      const lat = parseFloat(j.location_lat);
      const lng = parseFloat(j.location_lng);

      const activeDir = j.active_direction || 'NORTH';
      const activeState = (j.signals && j.signals[activeDir]) ? j.signals[activeDir].state : 'RED';
      const color = activeState === 'GREEN' ? '#10b981' : activeState === 'YELLOW' ? '#f59e0b' : '#ef4444';

      const totalQueued = j.queues ? (j.queues.NORTH + j.queues.SOUTH + j.queues.EAST + j.queues.WEST) : 0;

      const popupContent = `
        <div style="font-family: inherit; font-size: 0.85rem; line-height: 1.4;">
          <h4 style="color: #143769; font-weight: 700; margin-bottom: 4px;">${j.name}</h4>
          <p><strong>Active Phase:</strong> <span style="color: ${color}; font-weight: bold;">${activeDir} (${activeState})</span></p>
          <p><strong>Capacity:</strong> ${j.capacity} vehicles</p>
          <p><strong>Total Queued:</strong> ${totalQueued}</p>
          <div style="margin-top: 6px; font-size: 0.75rem; color: #475569;">
            N: ${j.queues ? j.queues.NORTH : 0} | S: ${j.queues ? j.queues.SOUTH : 0} | 
            E: ${j.queues ? j.queues.EAST : 0} | W: ${j.queues ? j.queues.WEST : 0}
          </div>
          <div style="margin-top: 8px; display: flex; gap: 4px; padding-top: 6px; border-top: 1px solid #e2e8f0;">
            <button class="btn btn-primary" style="padding: 3px 8px; font-size: 0.74rem; cursor: pointer;" onclick="SimulationApp.openAddVehicleModal(${j.id})">+ Add Vehicle</button>
            <button class="btn btn-danger" style="padding: 3px 8px; font-size: 0.74rem; cursor: pointer;" onclick="SimulationApp.quickAddEmergency(${j.id})">🚨 Ambulance</button>
          </div>
        </div>
      `;

      if (this.junctionMarkers[j.id]) {
        // Update existing marker icon & popup
        this.junctionMarkers[j.id].setLatLng([lat, lng]);
        this.junctionMarkers[j.id].setStyle({ fillColor: color, color: '#143769' });
        this.junctionMarkers[j.id].setPopupContent(popupContent);
      } else {
        // Create new circle marker
        const marker = L.circleMarker([lat, lng], {
          radius: 12,
          fillColor: color,
          color: '#143769',
          weight: 3,
          opacity: 1,
          fillOpacity: 0.85,
        }).addTo(this.map);

        marker.bindPopup(popupContent);
        marker.bindTooltip(`<b>${j.name}</b><br>Green: ${activeDir}`, { permanent: false, direction: 'top' });

        this.junctionMarkers[j.id] = marker;
      }
    });
  },

  renderRoads(roads, junctions) {
    // Clear old road lines
    this.roadPolylines.forEach((line) => this.map.removeLayer(line));
    this.roadPolylines = [];

    const jMap = {};
    junctions.forEach((j) => {
      jMap[j.id] = [parseFloat(j.location_lat), parseFloat(j.location_lng)];
    });

    roads.forEach((road) => {
      const srcCoord = jMap[road.source_junction_id];
      const dstCoord = jMap[road.dest_junction_id];

      if (srcCoord && dstCoord) {
        const isClosed = road.is_closed === 1;
        const color = isClosed ? '#ef4444' : '#3b82f6';
        const dashArray = isClosed ? '6, 8' : null;

        const polyline = L.polyline([srcCoord, dstCoord], {
          color: color,
          weight: isClosed ? 5 : 4,
          opacity: 0.75,
          dashArray: dashArray,
        }).addTo(this.map);

        polyline.bindPopup(`
          <div style="font-size: 0.85rem;">
            <strong>${road.name}</strong><br>
            Direction: ${road.direction} | Lanes: ${road.lanes}<br>
            Speed Limit: ${road.speed_limit} km/h | Length: ${road.length_meters}m<br>
            Status: <span style="color: ${isClosed ? '#ef4444' : '#10b981'}; font-weight: bold;">
              ${isClosed ? 'CLOSED (Incident)' : 'OPEN'}
            </span>
          </div>
        `);

        this.roadPolylines.push(polyline);
      }
    });
  },

  renderIncidents(incidents, junctions) {
    this.incidentMarkers.forEach((m) => this.map.removeLayer(m));
    this.incidentMarkers = [];

    const jMap = {};
    junctions.forEach((j) => {
      jMap[j.id] = [parseFloat(j.location_lat), parseFloat(j.location_lng)];
    });

    incidents.filter((i) => i.is_active === 1).forEach((inc) => {
      const coord = jMap[inc.junction_id];
      if (coord) {
        // Offset slightly to prevent covering junction marker
        const offsetCoord = [coord[0] + 0.002, coord[1] + 0.002];
        const iconHtml = `<div style="background: #dc2626; color: white; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">!</div>`;
        const customIcon = L.divIcon({ html: iconHtml, className: 'incident-div-icon', iconSize: [22, 22] });

        const marker = L.marker(offsetCoord, { icon: customIcon }).addTo(this.map);
        marker.bindPopup(`
          <div style="font-size: 0.85rem;">
            <strong style="color: #dc2626;">[INCIDENT] ${inc.incident_type}</strong><br>
            Severity: <b>${inc.severity}</b><br>
            Description: ${inc.description}<br>
            Junction: ${inc.junction_name || 'Junction ' + inc.junction_id}
          </div>
        `);

        this.incidentMarkers.push(marker);
      }
    });
  },
};
