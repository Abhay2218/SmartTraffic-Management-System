import json
from backend.database import query_all, query_one, execute_commit, execute_transaction
from backend.services.c_engine_service import CEngineService

class SimulationService:
    @staticmethod
    def get_simulation(sim_id):
        return query_one("SELECT * FROM simulations WHERE id = %s", (sim_id,))

    @staticmethod
    def list_simulations():
        return query_all("SELECT * FROM simulations ORDER BY id DESC")

    @classmethod
    def create_simulation(cls, data):
        name = data.get('name', 'Traffic Simulation')
        algorithm = data.get('algorithm', 'ADAPTIVE')
        quantum = int(data.get('quantum', 2))
        scenario = data.get('scenario', 'NORMAL')
        signal_mode = data.get('signal_mode', 'AUTOMATIC')
        speed = float(data.get('speed', 1.0))

        sim_id = execute_commit(
            """INSERT INTO simulations
               (name, algorithm, quantum, scenario, signal_mode, speed, status, current_tick, total_vehicles, completed_vehicles)
               VALUES (%s, %s, %s, %s, %s, %s, 'CREATED', 0, 0, 0)""",
            (name, algorithm, quantum, scenario, signal_mode, speed)
        )

        # Clone default vehicles from simulation 1 if requested or seed standard vehicles
        seed_vehicles = data.get('seed_vehicles', True)
        if seed_vehicles:
            cls.seed_scenario_vehicles(sim_id, scenario)

        return cls.get_simulation(sim_id)

    @classmethod
    def seed_scenario_vehicles(cls, sim_id, scenario='NORMAL'):
        vehicles = []
        if scenario == 'EMERGENCY':
            vehicles = [
                ('UK07-EM-911', 'Ambulance', 1, 'Doon Hospital', 'Max Hospital', 'NORTH', 0, 2, 1, 1),
                ('UK07-FT-101', 'Fire Truck', 1, 'Fire Station', 'Premnagar', 'EAST', 1, 3, 1, 1),
                ('UK07-PV-100', 'Police', 2, 'City Police', 'ISBT', 'SOUTH', 0, 2, 1, 1),
                ('UK07-CR-112', 'Car', 1, 'Paltan Bazaar', 'Rajpur Road', 'NORTH', 0, 3, 3, 0),
                ('UK07-CR-113', 'Car', 2, 'Ballupur', 'GMS Road', 'WEST', 2, 3, 4, 0),
            ]
        elif scenario == 'HEAVY':
            # 16 vehicles across all junctions
            for i in range(16):
                j_id = (i % 4) + 1
                dirs = ['NORTH', 'SOUTH', 'EAST', 'WEST']
                dir_val = dirs[i % 4]
                v_type = 'Bus' if i % 3 == 0 else 'Car'
                prio = 2 if v_type == 'Bus' else 3
                vehicles.append((f'UK07-HV-{1000+i}', v_type, j_id, 'Source', 'Dest', dir_val, i // 2, 3, prio, 0))
        elif scenario == 'ACCIDENT':
            vehicles = [
                ('UK07-CR-201', 'Car', 1, 'Source', 'Dest', 'NORTH', 0, 3, 3, 0),
                ('UK07-CR-202', 'Car', 1, 'Source', 'Dest', 'NORTH', 1, 3, 3, 0),
                ('UK07-EM-999', 'Ambulance', 1, 'Hospital', 'Accident Site', 'EAST', 2, 2, 1, 1),
                ('UK07-CR-203', 'Car', 2, 'Source', 'Dest', 'SOUTH', 0, 4, 3, 0),
            ]
        elif scenario == 'ROAD_CLOSURE':
            vehicles = [
                ('UK07-BS-401', 'Bus', 1, 'Haridwar', 'Dehradun', 'SOUTH', 0, 5, 2, 0),
                ('UK07-CR-402', 'Car', 2, 'Ballupur', 'Chakrata', 'WEST', 1, 3, 3, 0),
                ('UK07-CR-403', 'Car', 3, 'ISBT', 'Prince Chowk', 'NORTH', 2, 3, 3, 0),
            ]
        elif scenario == 'BUS_PRIORITY':
            vehicles = [
                ('UK07-PB-701', 'Bus', 1, 'Intercity Term', 'City Center', 'NORTH', 0, 4, 2, 0),
                ('UK07-PB-702', 'Bus', 1, 'ISBT Express', 'Clock Tower', 'NORTH', 1, 4, 2, 0),
                ('UK07-CR-703', 'Car', 1, 'Local', 'Market', 'EAST', 0, 2, 4, 0),
                ('UK07-CR-704', 'Car', 2, 'Local', 'Market', 'WEST', 1, 3, 4, 0),
            ]
        else: # NORMAL / MIXED
            vehicles = [
                ('UK07-AX-1011', 'Car', 1, 'Paltan Bazaar', 'Rajpur Road', 'NORTH', 0, 3, 3, 0),
                ('UK07-EM-9999', 'Ambulance', 1, 'Doon Hospital', 'Max Hospital', 'NORTH', 1, 2, 1, 1),
                ('UK07-PA-4022', 'Bus', 1, 'Rispana Pull', 'Clock Tower', 'SOUTH', 1, 5, 2, 0),
                ('UK07-BX-3044', 'Car', 1, 'Subhash Road', 'Chakrata Rd', 'EAST', 2, 3, 4, 0),
                ('UK07-TX-8801', 'Truck', 2, 'Premnagar', 'Ballupur', 'WEST', 0, 4, 4, 0),
                ('UK07-FT-1010', 'Fire Truck', 2, 'Fire Station', 'IMA BloodBank', 'EAST', 1, 3, 1, 1),
                ('UK07-CX-7722', 'Car', 2, 'Vasant Vihar', 'Kaulagarh', 'NORTH', 2, 2, 3, 0),
                ('UK07-PB-5501', 'Bus', 3, 'Haridwar By', 'ISBT Terminal', 'SOUTH', 0, 6, 2, 0),
                ('UK07-PV-0012', 'Police', 3, 'Patel Nagar', 'Cantonment', 'NORTH', 1, 2, 1, 1),
                ('UK07-DX-6633', 'Car', 3, 'Kargi Chowk', 'ISBT Flyover', 'WEST', 3, 3, 3, 0),
                ('UK07-EX-2211', 'Motorcycle', 4, 'Railway Stn', 'Gandhi Road', 'EAST', 0, 2, 4, 0),
                ('UK07-FX-4499', 'Car', 4, 'Saharanpur Rd', 'Prince Chowk', 'WEST', 1, 3, 3, 0),
            ]

        for plate, v_type, j_id, src, dst, direction, arr, burst, prio, is_emerg in vehicles:
            execute_commit(
                """INSERT INTO vehicles
                   (simulation_id, plate_number, vehicle_type, junction_id, source, destination,
                    direction, arrival_time, burst_time, remaining_time, initial_priority, priority,
                    is_emergency, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'WAITING')""",
                (sim_id, plate, v_type, j_id, src, dst, direction, arr, burst, burst, prio, 1 if is_emerg else prio, is_emerg)
            )

        execute_commit(
            "UPDATE simulations SET total_vehicles = (SELECT COUNT(*) FROM vehicles WHERE simulation_id = %s) WHERE id = %s",
            (sim_id, sim_id)
        )

    @classmethod
    def run_simulation(cls, sim_id):
        sim = cls.get_simulation(sim_id)
        if not sim:
            raise ValueError(f"Simulation {sim_id} not found.")

        # Load active junctions
        junctions = query_all("SELECT * FROM junctions ORDER BY id ASC")
        
        # Load active incidents affecting junctions
        incidents = query_all("SELECT * FROM traffic_incidents WHERE simulation_id = %s AND is_active = 1", (sim_id,))
        blocked_junction_directions = {}
        for inc in incidents:
            if inc['incident_type'] in ['ACCIDENT', 'ROAD_CLOSURE']:
                blocked_junction_directions[inc['junction_id']] = True

        # Load vehicles for this simulation
        db_vehicles = query_all("SELECT * FROM vehicles WHERE simulation_id = %s ORDER BY arrival_time ASC, id ASC", (sim_id,))

        if not db_vehicles:
            # Nothing to schedule
            execute_commit("UPDATE simulations SET status = 'COMPLETED' WHERE id = %s", (sim_id,))
            return {"status": "SUCCESS", "message": "Zero vehicles to schedule", "sim_id": sim_id}

        # Prepare payload for C Engine
        payload_junctions = []
        for j in junctions:
            is_blocked = blocked_junction_directions.get(j['id'], False)
            payload_junctions.append({
                "id": j['id'],
                "name": j['name'],
                "blocked_north": 1 if is_blocked else 0,
                "blocked_south": 0,
                "blocked_east": 0,
                "blocked_west": 0
            })

        payload_vehicles = []
        for v in db_vehicles:
            payload_vehicles.append({
                "id": v['id'],
                "junction_id": v['junction_id'],
                "type": v['vehicle_type'],
                "direction": v['direction'],
                "arrival_time": v['arrival_time'],
                "burst_time": v['burst_time'],
                "priority": v['initial_priority'],
                "is_emergency": v['is_emergency']
            })

        payload = {
            "algorithm": sim['algorithm'],
            "quantum": sim['quantum'],
            "aging_threshold": 4,
            "junctions": payload_junctions,
            "vehicles": payload_vehicles
        }

        # Execute C OS Engine!
        c_result = CEngineService.run_scheduling(payload)

        # Apply C Engine results back to MySQL in an ACID transaction
        metrics = c_result.get('metrics', {})
        scheduled_vehicles = c_result.get('vehicles', [])
        junction_states = c_result.get('junctions', [])
        events = c_result.get('events', [])
        exec_order = c_result.get('execution_order', [])

        ops = []

        # 1. Update simulation record
        ops.append((
            """UPDATE simulations SET
               status = 'RUNNING',
               completed_vehicles = %s,
               avg_waiting_time = %s,
               avg_turnaround_time = %s,
               throughput = %s,
               current_tick = %s
               WHERE id = %s""",
            (
                metrics.get('completed_vehicles', 0),
                metrics.get('avg_waiting_time', 0.0),
                metrics.get('avg_turnaround_time', 0.0),
                metrics.get('throughput', 0.0),
                metrics.get('total_time', 0),
                sim_id
            )
        ))

        # 2. Update each vehicle
        for sv in scheduled_vehicles:
            ops.append((
                """UPDATE vehicles SET
                   status = %s,
                   priority = %s,
                   waiting_time = %s,
                   turnaround_time = %s,
                   completion_time = %s,
                   remaining_time = 0
                   WHERE id = %s AND simulation_id = %s""",
                (
                    sv.get('status', 'COMPLETED'),
                    sv.get('effective_priority', 1),
                    sv.get('waiting_time', 0),
                    sv.get('turnaround_time', 0),
                    sv.get('completion_time', 0),
                    sv['id'],
                    sim_id
                )
            ))

        # 3. Store schedule events
        for ev in events:
            ops.append((
                """INSERT INTO vehicle_events
                   (vehicle_id, simulation_id, event_type, event_time, details)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    ev.get('vehicle_id', 1) if ev.get('vehicle_id', 0) > 0 else (db_vehicles[0]['id'] if db_vehicles else 1),
                    sim_id,
                    ev.get('action', 'QUEUED') if ev.get('action') in ['ARRIVED', 'QUEUED', 'AGING_APPLIED', 'STARTED', 'PREEMPTED', 'COMPLETED', 'BLOCKED'] else 'QUEUED',
                    ev.get('time', 0),
                    ev.get('details', '')
                )
            ))

        # 4. Update junction signal states in database
        for js in junction_states:
            j_id = js['id']
            signals = js.get('signals', {})
            green_times = js.get('green_times', {})
            for direction_name, state in signals.items():
                g_time = green_times.get(direction_name, 15)
                ops.append((
                    """UPDATE traffic_signals SET
                       state = %s,
                       green_time = %s
                       WHERE junction_id = %s AND direction = %s""",
                    (state, g_time, j_id, direction_name)
                ))
            ops.append((
                """UPDATE junctions SET
                   active_direction = %s,
                   current_phase = %s
                   WHERE id = %s""",
                (js.get('active_direction', 'NORTH'), f"PHASE_{js.get('active_direction', 'NORTH')}_GREEN", j_id)
            ))

        # 5. Save raw scheduling results
        ops.append((
            """INSERT INTO scheduling_results
               (simulation_id, algorithm, execution_order_json, metrics_json)
               VALUES (%s, %s, %s, %s)""",
            (
                sim_id,
                sim['algorithm'],
                json.dumps(exec_order),
                json.dumps(metrics)
            )
        ))

        # 6. Save normalized performance metrics for comparative analytics
        for m_name, m_val in metrics.items():
            if isinstance(m_val, (int, float)):
                ops.append((
                    """INSERT INTO performance_metrics
                       (simulation_id, algorithm, metric_name, metric_value)
                       VALUES (%s, %s, %s, %s)""",
                    (sim_id, sim['algorithm'], m_name, m_val)
                ))

        # Execute transaction
        execute_transaction(ops)

        return {
            "status": "SUCCESS",
            "sim_id": sim_id,
            "algorithm": sim['algorithm'],
            "metrics": metrics,
            "execution_order": exec_order,
            "junctions": junction_states,
            "scheduled_count": len(scheduled_vehicles)
        }

    @classmethod
    def pause_simulation(cls, sim_id):
        execute_commit("UPDATE simulations SET status = 'PAUSED' WHERE id = %s", (sim_id,))
        return cls.get_simulation(sim_id)

    @classmethod
    def resume_simulation(cls, sim_id):
        execute_commit("UPDATE simulations SET status = 'RUNNING' WHERE id = %s", (sim_id,))
        return cls.get_simulation(sim_id)

    @classmethod
    def reset_simulation(cls, sim_id):
        sim = cls.get_simulation(sim_id)
        if not sim:
            raise ValueError(f"Simulation {sim_id} not found.")

        ops = [
            ("DELETE FROM vehicle_events WHERE simulation_id = %s", (sim_id,)),
            ("DELETE FROM scheduling_results WHERE simulation_id = %s", (sim_id,)),
            ("DELETE FROM performance_metrics WHERE simulation_id = %s", (sim_id,)),
            ("""UPDATE vehicles SET
                status = 'WAITING',
                priority = initial_priority,
                waiting_time = 0,
                turnaround_time = 0,
                completion_time = 0,
                remaining_time = burst_time
                WHERE simulation_id = %s""", (sim_id,)),
            ("""UPDATE simulations SET
                status = 'CREATED',
                completed_vehicles = 0,
                avg_waiting_time = 0.0,
                avg_turnaround_time = 0.0,
                throughput = 0.0,
                current_tick = 0
                WHERE id = %s""", (sim_id,)),
        ]
        execute_transaction(ops)
        return cls.get_simulation(sim_id)
