-- ============================================================================
-- SmartTraffic DBMS Schema
-- Graphic Era (Deemed to be University) - Academic Session 2026-27
-- Team ID: OSDBMS-V-2026-T217
-- Normalized Relational Database (3NF)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS smarttraffic CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smarttraffic;

-- Disable foreign key checks during creation
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS performance_metrics;
DROP TABLE IF EXISTS scheduling_results;
DROP TABLE IF EXISTS traffic_incidents;
DROP TABLE IF EXISTS signal_events;
DROP TABLE IF EXISTS vehicle_events;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS simulations;
DROP TABLE IF EXISTS traffic_signals;
DROP TABLE IF EXISTS roads;
DROP TABLE IF EXISTS junctions;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- 1. USERS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'operator', 'viewer') NOT NULL DEFAULT 'operator',
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2. JUNCTIONS TABLE
-- Represents physical road intersections
-- ----------------------------------------------------------------------------
CREATE TABLE junctions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location_lat DECIMAL(10, 7) NOT NULL,
    location_lng DECIMAL(10, 7) NOT NULL,
    capacity INT NOT NULL DEFAULT 50,
    active_direction ENUM('NORTH', 'SOUTH', 'EAST', 'WEST') NOT NULL DEFAULT 'NORTH',
    current_phase VARCHAR(30) NOT NULL DEFAULT 'ALL_RED',
    status ENUM('ACTIVE', 'CONGESTED', 'MAINTENANCE', 'BLOCKED') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3. ROADS TABLE
-- Interconnects junctions with physical attributes
-- ----------------------------------------------------------------------------
CREATE TABLE roads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    source_junction_id INT NOT NULL,
    dest_junction_id INT NOT NULL,
    direction ENUM('NORTH', 'SOUTH', 'EAST', 'WEST') NOT NULL,
    lanes INT NOT NULL DEFAULT 2,
    speed_limit INT NOT NULL DEFAULT 50,
    length_meters INT NOT NULL DEFAULT 1200,
    is_closed TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_junction_id) REFERENCES junctions(id) ON DELETE CASCADE,
    FOREIGN KEY (dest_junction_id) REFERENCES junctions(id) ON DELETE CASCADE,
    CONSTRAINT chk_lanes CHECK (lanes > 0),
    CONSTRAINT chk_speed CHECK (speed_limit > 0)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 4. TRAFFIC SIGNALS TABLE
-- State of signal per junction and approach direction
-- ----------------------------------------------------------------------------
CREATE TABLE traffic_signals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    junction_id INT NOT NULL,
    direction ENUM('NORTH', 'SOUTH', 'EAST', 'WEST') NOT NULL,
    state ENUM('RED', 'YELLOW', 'GREEN') NOT NULL DEFAULT 'RED',
    green_time INT NOT NULL DEFAULT 15,
    min_green INT NOT NULL DEFAULT 5,
    max_green INT NOT NULL DEFAULT 60,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (junction_id) REFERENCES junctions(id) ON DELETE CASCADE,
    UNIQUE KEY uk_junction_direction (junction_id, direction)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 5. SIMULATIONS TABLE
-- Represents a simulation session run
-- ----------------------------------------------------------------------------
CREATE TABLE simulations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    algorithm ENUM('FCFS', 'PRIORITY', 'ROUND_ROBIN', 'ADAPTIVE') NOT NULL DEFAULT 'ADAPTIVE',
    quantum INT NOT NULL DEFAULT 2,
    scenario ENUM('NORMAL', 'HEAVY', 'EMERGENCY', 'ACCIDENT', 'ROAD_CLOSURE', 'BUS_PRIORITY', 'MIXED') NOT NULL DEFAULT 'NORMAL',
    signal_mode ENUM('AUTOMATIC', 'MANUAL') NOT NULL DEFAULT 'AUTOMATIC',
    speed DECIMAL(3,1) NOT NULL DEFAULT 1.0,
    status ENUM('CREATED', 'RUNNING', 'PAUSED', 'COMPLETED', 'RESET') NOT NULL DEFAULT 'CREATED',
    current_tick INT NOT NULL DEFAULT 0,
    total_vehicles INT NOT NULL DEFAULT 0,
    completed_vehicles INT NOT NULL DEFAULT 0,
    avg_waiting_time DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    avg_turnaround_time DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    throughput DECIMAL(6,3) NOT NULL DEFAULT 0.000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6. VEHICLES TABLE
-- Entities modeled as processes competing for intersection (CPU)
-- ----------------------------------------------------------------------------
CREATE TABLE vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    simulation_id INT NOT NULL,
    plate_number VARCHAR(20) NOT NULL,
    vehicle_type ENUM('Car', 'Bus', 'Truck', 'Motorcycle', 'Ambulance', 'Fire Truck', 'Police') NOT NULL DEFAULT 'Car',
    junction_id INT NOT NULL,
    source VARCHAR(60) NOT NULL DEFAULT 'Origin',
    destination VARCHAR(60) NOT NULL DEFAULT 'Destination',
    direction ENUM('NORTH', 'SOUTH', 'EAST', 'WEST') NOT NULL,
    arrival_time INT NOT NULL DEFAULT 0,
    burst_time INT NOT NULL DEFAULT 2,
    remaining_time INT NOT NULL DEFAULT 2,
    initial_priority INT NOT NULL DEFAULT 3,
    priority INT NOT NULL DEFAULT 3,
    is_emergency TINYINT(1) NOT NULL DEFAULT 0,
    status ENUM('WAITING', 'RUNNING', 'COMPLETED', 'BLOCKED') NOT NULL DEFAULT 'WAITING',
    waiting_time INT NOT NULL DEFAULT 0,
    turnaround_time INT NOT NULL DEFAULT 0,
    completion_time INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE,
    FOREIGN KEY (junction_id) REFERENCES junctions(id) ON DELETE CASCADE,
    INDEX idx_sim_status (simulation_id, status),
    INDEX idx_sim_arrival (simulation_id, arrival_time)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 7. VEHICLE EVENTS TABLE
-- Audit log of vehicle state transitions (arrived, queued, aged, started, completed)
-- ----------------------------------------------------------------------------
CREATE TABLE vehicle_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    simulation_id INT NOT NULL,
    event_type ENUM('ARRIVED', 'QUEUED', 'AGING_APPLIED', 'STARTED', 'PREEMPTED', 'COMPLETED', 'BLOCKED') NOT NULL,
    event_time INT NOT NULL,
    details VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE,
    INDEX idx_veh_ev (vehicle_id, event_time)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 8. SIGNAL EVENTS TABLE
-- Audit log of traffic signal state transitions
-- ----------------------------------------------------------------------------
CREATE TABLE signal_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    junction_id INT NOT NULL,
    simulation_id INT NOT NULL,
    direction ENUM('NORTH', 'SOUTH', 'EAST', 'WEST') NOT NULL,
    old_state ENUM('RED', 'YELLOW', 'GREEN') NOT NULL,
    new_state ENUM('RED', 'YELLOW', 'GREEN') NOT NULL,
    duration INT NOT NULL DEFAULT 0,
    reason VARCHAR(100) NOT NULL DEFAULT 'Adaptive Scheduling',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (junction_id) REFERENCES junctions(id) ON DELETE CASCADE,
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 9. TRAFFIC INCIDENTS TABLE
-- Dynamic scenarios: accidents, closures, congestion, emergency corridors
-- ----------------------------------------------------------------------------
CREATE TABLE traffic_incidents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    simulation_id INT NOT NULL,
    junction_id INT NOT NULL,
    road_id INT NULL,
    incident_type ENUM('ACCIDENT', 'ROAD_CLOSURE', 'CONGESTION', 'EMERGENCY_CORRIDOR') NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'MEDIUM',
    description VARCHAR(255) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    reported_time INT NOT NULL DEFAULT 0,
    resolved_time INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE,
    FOREIGN KEY (junction_id) REFERENCES junctions(id) ON DELETE CASCADE,
    FOREIGN KEY (road_id) REFERENCES roads(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 10. SCHEDULING RESULTS TABLE
-- Stores detailed output from the C engine
-- ----------------------------------------------------------------------------
CREATE TABLE scheduling_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    simulation_id INT NOT NULL,
    algorithm ENUM('FCFS', 'PRIORITY', 'ROUND_ROBIN', 'ADAPTIVE') NOT NULL,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_order_json JSON NOT NULL,
    metrics_json JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 11. PERFORMANCE METRICS TABLE
-- Normalized metric entries for comparative analytics queries
-- ----------------------------------------------------------------------------
CREATE TABLE performance_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    simulation_id INT NOT NULL,
    algorithm ENUM('FCFS', 'PRIORITY', 'ROUND_ROBIN', 'ADAPTIVE') NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 4) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (simulation_id) REFERENCES simulations(id) ON DELETE CASCADE,
    INDEX idx_metric_lookup (simulation_id, algorithm, metric_name)
) ENGINE=InnoDB;
