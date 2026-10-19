-- ============================================================================
-- SmartTraffic Seed Data
-- Graphic Era (Deemed to be University) - Academic Session 2026-27
-- Dehradun City Grid
-- ============================================================================

USE smarttraffic;

-- Seed Users (password is hashed for 'admin123' / 'operator123')
INSERT INTO users (username, password_hash, role, full_name) VALUES
('admin', 'pbkdf2:sha256:600000$admin$2b988f5f661ff9fc83f2a898b049d5a711451f478a2e58e658428d0b28489e8f', 'admin', 'System Administrator'),
('kshitij', 'pbkdf2:sha256:600000$operator$c392f397732db4ab0999553f1d87e076634fe7946914587635678a1bc1b4765d', 'operator', 'Kshitij Kukreti (Lead)'),
('abhay', 'pbkdf2:sha256:600000$operator$c392f397732db4ab0999553f1d87e076634fe7946914587635678a1bc1b4765d', 'operator', 'Abhay Pratap Singh Negi'),
('abhyudaya', 'pbkdf2:sha256:600000$operator$c392f397732db4ab0999553f1d87e076634fe7946914587635678a1bc1b4765d', 'operator', 'Abhyudaya Bhandari');

-- Seed 4 Interconnected Dehradun Junctions
INSERT INTO junctions (id, name, location_lat, location_lng, capacity, active_direction, current_phase, status) VALUES
(1, 'Ghanta Ghar (Clock Tower)', 30.3255000, 78.0437000, 60, 'NORTH', 'PHASE_NORTH_GREEN', 'ACTIVE'),
(2, 'Ballupur Chowk', 30.3398000, 78.0165000, 50, 'EAST', 'PHASE_EAST_GREEN', 'ACTIVE'),
(3, 'ISBT Dehradun', 30.2863000, 77.9996000, 80, 'SOUTH', 'PHASE_SOUTH_GREEN', 'ACTIVE'),
(4, 'Prince Chowk', 30.3174000, 78.0371000, 45, 'WEST', 'PHASE_WEST_GREEN', 'ACTIVE');

-- Seed Roads interconnecting the 4 junctions
INSERT INTO roads (id, name, source_junction_id, dest_junction_id, direction, lanes, speed_limit, length_meters, is_closed) VALUES
(1, 'Rajpur Road Express', 1, 2, 'WEST', 3, 50, 2400, 0),
(2, 'Chakrata Link Road', 2, 1, 'EAST', 3, 50, 2400, 0),
(3, 'Haridwar Road Arterial', 1, 4, 'SOUTH', 2, 45, 1100, 0),
(4, 'Court Road Connecting', 4, 1, 'NORTH', 2, 45, 1100, 0),
(5, 'Saharanpur Highway', 4, 3, 'SOUTH', 4, 60, 4200, 0),
(6, 'Transport Nagar Corridor', 3, 4, 'NORTH', 4, 60, 4200, 0),
(7, 'Balliwala Flyover Route', 2, 3, 'SOUTH', 3, 55, 5100, 0),
(8, 'GMS Road Bypass', 3, 2, 'NORTH', 3, 55, 5100, 0);

-- Seed Traffic Signals (4 directions for each of the 4 junctions = 16 signals)
INSERT INTO traffic_signals (junction_id, direction, state, green_time, min_green, max_green) VALUES
-- Junction 1: Ghanta Ghar
(1, 'NORTH', 'GREEN', 25, 10, 60),
(1, 'SOUTH', 'RED',   15, 10, 60),
(1, 'EAST',  'RED',   15, 10, 60),
(1, 'WEST',  'RED',   15, 10, 60),
-- Junction 2: Ballupur Chowk
(2, 'NORTH', 'RED',   15, 10, 60),
(2, 'SOUTH', 'RED',   15, 10, 60),
(2, 'EAST',  'GREEN', 20, 10, 60),
(2, 'WEST',  'RED',   15, 10, 60),
-- Junction 3: ISBT Dehradun
(3, 'NORTH', 'RED',   15, 10, 60),
(3, 'SOUTH', 'GREEN', 30, 10, 60),
(3, 'EAST',  'RED',   15, 10, 60),
(3, 'WEST',  'RED',   15, 10, 60),
-- Junction 4: Prince Chowk
(4, 'NORTH', 'RED',   15, 10, 60),
(4, 'SOUTH', 'RED',   15, 10, 60),
(4, 'EAST',  'RED',   15, 10, 60),
(4, 'WEST',  'GREEN', 15, 10, 60);

-- Seed Initial Baseline Simulation
INSERT INTO simulations (id, name, algorithm, quantum, scenario, signal_mode, speed, status, current_tick, total_vehicles, completed_vehicles, avg_waiting_time, avg_turnaround_time, throughput) VALUES
(1, 'Baseline Demo Simulation', 'ADAPTIVE', 2, 'NORMAL', 'AUTOMATIC', 1.0, 'CREATED', 0, 12, 0, 0.00, 0.00, 0.000);

-- Seed 12 Diverse Vehicles for Simulation 1
INSERT INTO vehicles (simulation_id, plate_number, vehicle_type, junction_id, source, destination, direction, arrival_time, burst_time, remaining_time, initial_priority, priority, is_emergency, status) VALUES
(1, 'UK07-AX-1011', 'Car',        1, 'Paltan Bazaar', 'Rajpur Road',  'NORTH', 0, 3, 3, 3, 3, 0, 'WAITING'),
(1, 'UK07-EM-9999', 'Ambulance',  1, 'Doon Hospital', 'Max Hospital', 'NORTH', 1, 2, 2, 1, 1, 1, 'WAITING'),
(1, 'UK07-PA-4022', 'Bus',        1, 'Rispana Pull',  'Clock Tower',  'SOUTH', 1, 5, 5, 2, 2, 0, 'WAITING'),
(1, 'UK07-BX-3044', 'Car',        1, 'Subhash Road',  'Chakrata Rd',  'EAST',  2, 3, 3, 4, 4, 0, 'WAITING'),

(1, 'UK07-TX-8801', 'Truck',      2, 'Premnagar',     'Ballupur',     'WEST',  0, 4, 4, 4, 4, 0, 'WAITING'),
(1, 'UK07-FT-1010', 'Fire Truck', 2, 'Fire Station',  'IMA BloodBank','EAST',  1, 3, 3, 1, 1, 1, 'WAITING'),
(1, 'UK07-CX-7722', 'Car',        2, 'Vasant Vihar',  'Kaulagarh',    'NORTH', 2, 2, 2, 3, 3, 0, 'WAITING'),

(1, 'UK07-PB-5501', 'Bus',        3, 'Haridwar By',   'ISBT Terminal','SOUTH', 0, 6, 6, 2, 2, 0, 'WAITING'),
(1, 'UK07-PV-0012', 'Police',     3, 'Patel Nagar',   'Cantonment',   'NORTH', 1, 2, 2, 1, 1, 1, 'WAITING'),
(1, 'UK07-DX-6633', 'Car',        3, 'Kargi Chowk',   'ISBT Flyover', 'WEST',  3, 3, 3, 3, 3, 0, 'WAITING'),

(1, 'UK07-EX-2211', 'Motorcycle', 4, 'Railway Stn',   'Gandhi Road',  'EAST',  0, 2, 2, 4, 4, 0, 'WAITING'),
(1, 'UK07-FX-4499', 'Car',        4, 'Saharanpur Rd', 'Prince Chowk', 'WEST',  1, 3, 3, 3, 3, 0, 'WAITING');

-- Seed a Sample Active Incident
INSERT INTO traffic_incidents (simulation_id, junction_id, road_id, incident_type, severity, description, is_active, reported_time) VALUES
(1, 2, 2, 'CONGESTION', 'MEDIUM', 'Moderate peak hour buildup along Chakrata Road towards Ballupur', 1, 0);
