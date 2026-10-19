-- ============================================================================
-- SmartTraffic DBMS Stored Procedures, Functions, and Triggers
-- Graphic Era (Deemed to be University) - Academic Session 2025-26
-- Team ID: OSDBMS-V-2026-T217
-- ============================================================================

USE smarttraffic;

-- ============================================================================
-- 1. STORED FUNCTIONS (USER DEFINED FUNCTIONS)
-- ============================================================================

DROP FUNCTION IF EXISTS fn_calculate_traffic_density;
DELIMITER //
CREATE FUNCTION fn_calculate_traffic_density(p_junction_id INT)
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_capacity INT DEFAULT 50;
    DECLARE v_waiting INT DEFAULT 0;
    DECLARE v_density DECIMAL(5,2) DEFAULT 0.00;

    SELECT capacity INTO v_capacity FROM junctions WHERE id = p_junction_id;
    SELECT COUNT(*) INTO v_waiting FROM vehicles WHERE junction_id = p_junction_id AND status = 'WAITING';

    IF v_capacity > 0 THEN
        SET v_density = (v_waiting / v_capacity) * 100.0;
        IF v_density > 100.0 THEN
            SET v_density = 100.0;
        END IF;
    END IF;

    RETURN v_density;
END //
DELIMITER ;

DROP FUNCTION IF EXISTS fn_get_starvation_risk;
DELIMITER //
CREATE FUNCTION fn_get_starvation_risk(p_waiting_time INT, p_initial_priority INT)
RETURNS VARCHAR(10)
DETERMINISTIC
NO SQL
BEGIN
    IF p_waiting_time >= 15 AND p_initial_priority >= 3 THEN
        RETURN 'CRITICAL';
    ELSEIF p_waiting_time >= 8 AND p_initial_priority >= 3 THEN
        RETURN 'HIGH';
    ELSEIF p_waiting_time >= 4 THEN
        RETURN 'MEDIUM';
    ELSE
        RETURN 'LOW';
    END IF;
END //
DELIMITER ;

-- ============================================================================
-- 2. STORED PROCEDURES (ACID TRANSACTIONS)
-- ============================================================================

-- Procedure 1: Atomically register vehicle arrival and audit event
DROP PROCEDURE IF EXISTS sp_register_vehicle_arrival;
DELIMITER //
CREATE PROCEDURE sp_register_vehicle_arrival(
    IN p_sim_id INT,
    IN p_plate VARCHAR(20),
    IN p_type VARCHAR(20),
    IN p_junction_id INT,
    IN p_direction VARCHAR(10),
    IN p_arrival INT,
    IN p_burst INT,
    IN p_priority INT,
    IN p_is_emergency TINYINT,
    OUT p_vehicle_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
        INSERT INTO vehicles (
            simulation_id, plate_number, vehicle_type, junction_id,
            direction, arrival_time, burst_time, remaining_time,
            initial_priority, priority, is_emergency, status
        ) VALUES (
            p_sim_id, p_plate, p_type, p_junction_id,
            p_direction, p_arrival, p_burst, p_burst,
            p_priority, p_priority, p_is_emergency, 'WAITING'
        );
        SET p_vehicle_id = LAST_INSERT_ID();

        INSERT INTO vehicle_events (
            vehicle_id, simulation_id, event_type, event_time, details
        ) VALUES (
            p_vehicle_id, p_sim_id, 'ARRIVED', p_arrival,
            CONCAT('Vehicle arrived at junction ', p_junction_id, ' approach ', p_direction)
        );
    COMMIT;
END //
DELIMITER ;

-- Procedure 2: Complete vehicle transit and compute turnaround metrics
DROP PROCEDURE IF EXISTS sp_transit_vehicle_complete;
DELIMITER //
CREATE PROCEDURE sp_transit_vehicle_complete(
    IN p_vehicle_id INT,
    IN p_completion_time INT
)
BEGIN
    DECLARE v_arrival INT;
    DECLARE v_burst INT;
    DECLARE v_sim_id INT;
    DECLARE v_tat INT;
    DECLARE v_wt INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
        SELECT simulation_id, arrival_time, burst_time
        INTO v_sim_id, v_arrival, v_burst
        FROM vehicles WHERE id = p_vehicle_id FOR UPDATE;

        SET v_tat = p_completion_time - v_arrival;
        SET v_wt = v_tat - v_burst;
        IF v_wt < 0 THEN
            SET v_wt = 0;
        END IF;

        UPDATE vehicles
        SET status = 'COMPLETED',
            completion_time = p_completion_time,
            turnaround_time = v_tat,
            waiting_time = v_wt,
            remaining_time = 0
        WHERE id = p_vehicle_id;

        INSERT INTO vehicle_events (
            vehicle_id, simulation_id, event_type, event_time, details
        ) VALUES (
            p_vehicle_id, v_sim_id, 'COMPLETED', p_completion_time,
            CONCAT('Vehicle cleared intersection. TAT=', v_tat, 's, Wait=', v_wt, 's')
        );

        UPDATE simulations
        SET completed_vehicles = completed_vehicles + 1
        WHERE id = v_sim_id;
    COMMIT;
END //
DELIMITER ;

-- Procedure 3: Report incident and automatically flag roads/junctions
DROP PROCEDURE IF EXISTS sp_report_traffic_incident;
DELIMITER //
CREATE PROCEDURE sp_report_traffic_incident(
    IN p_sim_id INT,
    IN p_junction_id INT,
    IN p_road_id INT,
    IN p_type VARCHAR(30),
    IN p_severity VARCHAR(20),
    IN p_desc VARCHAR(255),
    IN p_time INT,
    OUT p_incident_id INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
        INSERT INTO traffic_incidents (
            simulation_id, junction_id, road_id, incident_type,
            severity, description, is_active, reported_time
        ) VALUES (
            p_sim_id, p_junction_id, p_road_id, p_type,
            p_severity, p_desc, 1, p_time
        );
        SET p_incident_id = LAST_INSERT_ID();

        IF p_severity IN ('HIGH', 'CRITICAL') THEN
            UPDATE junctions SET status = 'BLOCKED' WHERE id = p_junction_id;
            IF p_road_id IS NOT NULL THEN
                UPDATE roads SET is_closed = 1 WHERE id = p_road_id;
            END IF;
        ELSE
            UPDATE junctions SET status = 'CONGESTED' WHERE id = p_junction_id;
        END IF;
    COMMIT;
END //
DELIMITER ;

-- Procedure 4: Resolve traffic incident and restore active status
DROP PROCEDURE IF EXISTS sp_resolve_traffic_incident;
DELIMITER //
CREATE PROCEDURE sp_resolve_traffic_incident(
    IN p_incident_id INT,
    IN p_resolve_time INT
)
BEGIN
    DECLARE v_junc_id INT;
    DECLARE v_road_id INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
        SELECT junction_id, road_id INTO v_junc_id, v_road_id
        FROM traffic_incidents WHERE id = p_incident_id FOR UPDATE;

        UPDATE traffic_incidents
        SET is_active = 0, resolved_time = p_resolve_time
        WHERE id = p_incident_id;

        UPDATE junctions SET status = 'ACTIVE' WHERE id = v_junc_id;
        IF v_road_id IS NOT NULL THEN
            UPDATE roads SET is_closed = 0 WHERE id = v_road_id;
        END IF;
    COMMIT;
END //
DELIMITER ;

-- Procedure 5: Record standardized performance metric
DROP PROCEDURE IF EXISTS sp_record_scheduling_metric;
DELIMITER //
CREATE PROCEDURE sp_record_scheduling_metric(
    IN p_sim_id INT,
    IN p_algorithm VARCHAR(20),
    IN p_name VARCHAR(50),
    IN p_val DECIMAL(10,4)
)
BEGIN
    INSERT INTO performance_metrics (simulation_id, algorithm, metric_name, metric_value)
    VALUES (p_sim_id, p_algorithm, p_name, p_val);
END //
DELIMITER ;

-- ============================================================================
-- 3. TRIGGERS (AUDIT LOGGING & STATE SYNCHRONIZATION)
-- ============================================================================

DROP TRIGGER IF EXISTS trg_after_vehicle_insert;
DELIMITER //
CREATE TRIGGER trg_after_vehicle_insert
AFTER INSERT ON vehicles
FOR EACH ROW
BEGIN
    INSERT INTO vehicle_events (vehicle_id, simulation_id, event_type, event_time, details)
    VALUES (NEW.id, NEW.simulation_id, 'ARRIVED', NEW.arrival_time, 
            CONCAT('Arrived at junction ', NEW.junction_id, ' from ', NEW.direction));
END //
DELIMITER ;

DROP TRIGGER IF EXISTS trg_after_vehicle_update;
DELIMITER //
CREATE TRIGGER trg_after_vehicle_update
AFTER UPDATE ON vehicles
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO vehicle_events (vehicle_id, simulation_id, event_type, event_time, details)
        VALUES (NEW.id, NEW.simulation_id, 
                CASE 
                    WHEN NEW.status = 'RUNNING' THEN 'STARTED'
                    WHEN NEW.status = 'COMPLETED' THEN 'COMPLETED'
                    WHEN NEW.status = 'BLOCKED' THEN 'BLOCKED'
                    ELSE 'QUEUED'
                END, 
                IFNULL(NEW.completion_time, NEW.arrival_time),
                CONCAT('Status updated: ', OLD.status, ' -> ', NEW.status));
    END IF;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS trg_after_incident_insert;
DELIMITER //
CREATE TRIGGER trg_after_incident_insert
AFTER INSERT ON traffic_incidents
FOR EACH ROW
BEGIN
    IF NEW.is_active = 1 THEN
        IF NEW.severity IN ('HIGH', 'CRITICAL') THEN
            UPDATE junctions SET status = 'BLOCKED' WHERE id = NEW.junction_id;
            IF NEW.road_id IS NOT NULL THEN
                UPDATE roads SET is_closed = 1 WHERE id = NEW.road_id;
            END IF;
        ELSE
            UPDATE junctions SET status = 'CONGESTED' WHERE id = NEW.junction_id;
        END IF;
    END IF;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS trg_after_incident_update;
DELIMITER //
CREATE TRIGGER trg_after_incident_update
AFTER UPDATE ON traffic_incidents
FOR EACH ROW
BEGIN
    IF OLD.is_active = 1 AND NEW.is_active = 0 THEN
        UPDATE junctions SET status = 'ACTIVE' WHERE id = NEW.junction_id;
        IF NEW.road_id IS NOT NULL THEN
            UPDATE roads SET is_closed = 0 WHERE id = NEW.road_id;
        END IF;
    END IF;
END //
DELIMITER ;
