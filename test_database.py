import unittest
import pymysql
from backend.database import get_connection, query_all, query_one, execute_commit, execute_transaction

class TestDatabase(unittest.TestCase):
    def test_01_database_connection(self):
        conn = get_connection()
        self.assertIsNotNone(conn)
        conn.close()

    def test_02_all_eleven_tables_exist(self):
        expected_tables = {
            'users', 'junctions', 'roads', 'traffic_signals', 'simulations',
            'vehicles', 'vehicle_events', 'signal_events', 'traffic_incidents',
            'scheduling_results', 'performance_metrics'
        }
        tables_res = query_all("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        actual_tables = {list(r.values())[0] for r in tables_res}
        for t in expected_tables:
            self.assertIn(t, actual_tables, f"Table '{t}' must exist in schema")

    def test_03_foreign_key_cascade(self):
        # Create dummy simulation
        sim_id = execute_commit(
            "INSERT INTO simulations (name, algorithm, status) VALUES ('FK Test Sim', 'FCFS', 'CREATED')"
        )
        # Create vehicle under this simulation
        v_id = execute_commit(
            """INSERT INTO vehicles
               (simulation_id, plate_number, vehicle_type, junction_id, direction, burst_time)
               VALUES (%s, 'UK07-FK-0001', 'Car', 1, 'NORTH', 2)""",
            (sim_id,)
        )
        # Verify vehicle exists
        v = query_one("SELECT * FROM vehicles WHERE id = %s", (v_id,))
        self.assertIsNotNone(v)

        # Delete simulation -> vehicle must be CASCADE deleted
        execute_commit("DELETE FROM simulations WHERE id = %s", (sim_id,))
        v_after = query_one("SELECT * FROM vehicles WHERE id = %s", (v_id,))
        self.assertIsNone(v_after, "Vehicle should be cascade-deleted when simulation is deleted")

    def test_04_transaction_rollback_on_failure(self):
        cnt_before = query_one("SELECT COUNT(*) as c FROM vehicles")['c']

        ops = [
            ("""INSERT INTO vehicles
                (simulation_id, plate_number, vehicle_type, junction_id, direction, burst_time)
                VALUES (1, 'UK07-ROLLBACK-1', 'Car', 1, 'NORTH', 2)""", ()),
            ("""INSERT INTO vehicles
                (simulation_id, plate_number, vehicle_type, junction_id, direction, burst_time)
                VALUES (999999, 'UK07-FAIL', 'Car', 999999, 'NORTH', 2)""", ()) # Invalid FK
        ]

        with self.assertRaises(Exception):
            execute_transaction(ops)

        cnt_after = query_one("SELECT COUNT(*) as c FROM vehicles")['c']
        self.assertEqual(cnt_before, cnt_after, "Transaction must rollback all changes on error")

    def test_05_check_and_unique_constraints(self):
        juncs = query_all("SELECT * FROM junctions")
        self.assertGreaterEqual(len(juncs), 4)

        roads = query_all("SELECT * FROM roads")
        self.assertGreaterEqual(len(roads), 8)

        # Verify signals unique constraint (junction_id, direction)
        signals = query_all("SELECT junction_id, direction, COUNT(*) as cnt FROM traffic_signals GROUP BY junction_id, direction HAVING cnt > 1")
        self.assertEqual(len(signals), 0, "No duplicate direction signals per junction")

    def test_06_analytical_views(self):
        # 1. vw_junction_live_status
        j_view = query_all("SELECT * FROM vw_junction_live_status")
        self.assertGreaterEqual(len(j_view), 4)
        self.assertIn('junction_name', j_view[0])
        self.assertIn('waiting_vehicles', j_view[0])

        # 2. vw_algorithm_comparison
        alg_view = query_all("SELECT * FROM vw_algorithm_comparison")
        self.assertGreaterEqual(len(alg_view), 1)
        self.assertIn('overall_avg_wait_time', alg_view[0])

        # 3. vw_emergency_vehicle_audit
        emerg_view = query_all("SELECT * FROM vw_emergency_vehicle_audit")
        self.assertGreaterEqual(len(emerg_view), 1)
        for ev in emerg_view:
            self.assertEqual(ev['is_emergency'], 1)

        # 4. vw_road_traffic_density
        road_view = query_all("SELECT * FROM vw_road_traffic_density")
        self.assertGreaterEqual(len(road_view), 8)

        # 5. vw_simulation_summary
        sim_view = query_all("SELECT * FROM vw_simulation_summary")
        self.assertGreaterEqual(len(sim_view), 1)

    def test_07_stored_procedures(self):
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                # Test sp_register_vehicle_arrival
                cursor.execute("SET @v_id = 0;")
                cursor.execute("CALL sp_register_vehicle_arrival(1, 'UK07-TEST-PROC', 'Car', 1, 'SOUTH', 0, 3, 3, 0, @v_id);")
                cursor.execute("SELECT @v_id as created_id;")
                created_id = cursor.fetchone()['created_id']
                self.assertGreater(created_id, 0)

                # Test sp_transit_vehicle_complete
                cursor.execute(f"CALL sp_transit_vehicle_complete({created_id}, 6);")
                v = query_one("SELECT * FROM vehicles WHERE id = %s", (created_id,))
                self.assertEqual(v['status'], 'COMPLETED')
                self.assertEqual(v['completion_time'], 6)
                self.assertEqual(v['turnaround_time'], 6)
                self.assertEqual(v['waiting_time'], 3)

                # Test sp_report_traffic_incident
                cursor.execute("SET @inc_id = 0;")
                cursor.execute("CALL sp_report_traffic_incident(1, 3, 6, 'CONGESTION', 'LOW', 'Test Congestion', 1, @inc_id);")
                cursor.execute("SELECT @inc_id as inc_id;")
                inc_id = cursor.fetchone()['inc_id']
                self.assertGreater(inc_id, 0)

                # Test sp_resolve_traffic_incident
                cursor.execute(f"CALL sp_resolve_traffic_incident({inc_id}, 10);")
                inc = query_one("SELECT * FROM traffic_incidents WHERE id = %s", (inc_id,))
                self.assertEqual(inc['is_active'], 0)
                self.assertEqual(inc['resolved_time'], 10)
        finally:
            conn.close()

    def test_08_stored_functions(self):
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT fn_calculate_traffic_density(1) as density;")
                density = float(cursor.fetchone()['density'])
                self.assertGreaterEqual(density, 0.0)
                self.assertLessEqual(density, 100.0)

                cursor.execute("SELECT fn_get_starvation_risk(20, 4) as risk;")
                risk = cursor.fetchone()['risk']
                self.assertEqual(risk, 'CRITICAL')

                cursor.execute("SELECT fn_get_starvation_risk(1, 1) as risk;")
                low_risk = cursor.fetchone()['risk']
                self.assertEqual(low_risk, 'LOW')
        finally:
            conn.close()

    def test_09_database_triggers(self):
        # Insert vehicle directly to verify trg_after_vehicle_insert
        v_id = execute_commit("""
            INSERT INTO vehicles (simulation_id, plate_number, vehicle_type, junction_id, direction, arrival_time, burst_time)
            VALUES (1, 'UK07-TRG-01', 'Car', 1, 'NORTH', 2, 3)
        """)
        # Trigger should have inserted ARRIVED event
        ev = query_one("SELECT * FROM vehicle_events WHERE vehicle_id = %s AND event_type = 'ARRIVED'", (v_id,))
        self.assertIsNotNone(ev, "Trigger trg_after_vehicle_insert must auto-record ARRIVED event")

        # Update vehicle status to RUNNING to verify trg_after_vehicle_update
        execute_commit("UPDATE vehicles SET status = 'RUNNING' WHERE id = %s", (v_id,))
        ev_run = query_one("SELECT * FROM vehicle_events WHERE vehicle_id = %s AND event_type = 'STARTED'", (v_id,))
        self.assertIsNotNone(ev_run, "Trigger trg_after_vehicle_update must auto-record STARTED event")

if __name__ == '__main__':
    unittest.main()
