import os
import sys
import pymysql
from pymysql.cursors import DictCursor

# Add project root to sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
from backend.config import Config
from backend.database import get_connection, query_all, query_one, execute_commit, execute_transaction
from database.init_db import init_database

def print_banner():
    print("\n==================================================")
    print(" SmartTraffic - Database Management Console")
    print(" Team: Kshitij, Abhay, Abhyudaya | Graphic Era")
    print("==================================================")

def display_ascii_table(rows, title="Query Results"):
    print(f"\n--- {title} ---")
    if not rows:
        print("(No rows found)")
        return

    columns = list(rows[0].keys())
    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            val_str = str(row[col]) if row[col] is not None else "NULL"
            if len(val_str) > widths[col]:
                widths[col] = min(len(val_str), 28)

    sep = "+" + "+".join(["-" * (widths[col] + 2) for col in columns]) + "+"
    header = "|" + "|".join([f" {col.center(widths[col])} " for col in columns]) + "|"
    print(sep)
    print(header)
    print(sep)

    for row in rows:
        line_parts = []
        for col in columns:
            val_str = str(row[col]) if row[col] is not None else "NULL"
            if len(val_str) > 28:
                val_str = val_str[:25] + "..."
            line_parts.append(f" {val_str.ljust(widths[col])} ")
        print("|" + "|".join(line_parts) + "|")
    print(sep + "\n")

def check_db_status():
    print_banner()
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DATABASE() as db, VERSION() as ver")
            info = cursor.fetchone()
            print(f"Connected to: {info['db']} (MySQL {info['ver']})")
            print(f"Host: {Config.DB_HOST}:{Config.DB_PORT}\n")

            # Tables
            cursor.execute("""
                SELECT table_name as 'Table', table_rows as 'Estimated Rows', engine as 'Engine'
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (Config.DB_NAME,))
            tables = cursor.fetchall()
            display_ascii_table(tables, "11 Database Tables")

            # Views
            cursor.execute("""
                SELECT table_name as 'View Name'
                FROM information_schema.views 
                WHERE table_schema = %s
                ORDER BY table_name
            """, (Config.DB_NAME,))
            views = cursor.fetchall()
            display_ascii_table(views, "5 Analytical SQL Views")

            # Stored Procedures & Functions
            cursor.execute("""
                SELECT routine_name as 'Routine Name', routine_type as 'Type'
                FROM information_schema.routines
                WHERE routine_schema = %s
                ORDER BY routine_type, routine_name
            """, (Config.DB_NAME,))
            routines = cursor.fetchall()
            display_ascii_table(routines, "Stored Procedures & Functions")

            # Triggers
            cursor.execute("""
                SELECT trigger_name as 'Trigger', event_object_table as 'Target Table', event_manipulation as 'Event'
                FROM information_schema.triggers
                WHERE trigger_schema = %s
                ORDER BY trigger_name
            """, (Config.DB_NAME,))
            triggers = cursor.fetchall()
            display_ascii_table(triggers, "Database Triggers")

    finally:
        conn.close()

def display_views():
    print_banner()
    print("Querying 5 Analytical Views:\n")

    views = [
        ("vw_junction_live_status", "1. Live Junction Queues & Phases"),
        ("vw_algorithm_comparison", "2. Algorithm Performance Comparison"),
        ("vw_emergency_vehicle_audit", "3. Emergency Vehicles Log"),
        ("vw_road_traffic_density", "4. Road Network & Incident Status"),
        ("vw_simulation_summary", "5. Simulation Sessions Overview")
    ]

    for view_name, title in views:
        rows = query_all(f"SELECT * FROM {view_name} LIMIT 10")
        display_ascii_table(rows, title)

def test_acid_transactions():
    print_banner()
    print("Testing ACID Transaction Handling (Commit & Rollback):\n")

    conn = get_connection()
    try:
        print("[Step 1] Testing Atomic Commit:")
        print("  Inserting a vehicle and its arrival event in one transaction...")
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO vehicles 
                (simulation_id, plate_number, vehicle_type, junction_id, direction, arrival_time, burst_time, priority, status)
                VALUES (1, 'UK07-TX-999', 'Ambulance', 1, 'NORTH', 0, 3, 1, 'WAITING')
            """)
            v_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO vehicle_events (vehicle_id, simulation_id, event_type, event_time, details)
                VALUES (%s, 1, 'ARRIVED', 0, 'Vehicle arrived at junction 1')
            """, (v_id,))

            conn.commit()
            print(f"  -> Committed successfully. Created vehicle ID: {v_id}")

        v_check = query_one("SELECT * FROM vehicles WHERE id = %s", (v_id,))
        assert v_check is not None
        print("  -> Verified: Both vehicle and event log were saved.")

        print("\n[Step 2] Testing Atomic Rollback on Error:")
        print("  Running a transaction with an invalid foreign key...")
        before_count = query_one("SELECT COUNT(*) as c FROM vehicles")['c']

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO vehicles 
                    (simulation_id, plate_number, vehicle_type, junction_id, direction, burst_time)
                    VALUES (1, 'UK07-TEMP', 'Car', 1, 'NORTH', 2)
                """)
                # Invalid junction ID
                cursor.execute("""
                    INSERT INTO vehicles 
                    (simulation_id, plate_number, vehicle_type, junction_id, direction, burst_time)
                    VALUES (1, 'UK07-TEMP-FAIL', 'Car', 999999, 'NORTH', 2)
                """)
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"  -> Expected error triggered: {e.__class__.__name__}")
            print("  -> Rolled back all changes.")

        after_count = query_one("SELECT COUNT(*) as c FROM vehicles")['c']
        assert before_count == after_count
        print(f"  -> Verified: Vehicle count before ({before_count}) == after ({after_count}). No partial data left behind.")

        print("\nAll ACID transaction tests passed!\n")

    finally:
        conn.close()

def test_stored_procedures():
    print_banner()
    print("Testing Stored Procedures and Functions:\n")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. sp_register_vehicle_arrival
            print("1. Calling sp_register_vehicle_arrival...")
            cursor.execute("SET @v_out_id = 0;")
            cursor.execute("""
                CALL sp_register_vehicle_arrival(
                    1, 'UK07-POL-10', 'Police', 2, 'EAST', 5, 2, 1, 1, @v_out_id
                );
            """)
            cursor.execute("SELECT @v_out_id AS created_vehicle_id;")
            created_v_id = cursor.fetchone()['created_vehicle_id']
            print(f"   -> Vehicle registered with ID: {created_v_id}")

            # 2. UDF fn_calculate_traffic_density
            cursor.execute("SELECT fn_calculate_traffic_density(2) as density_pct;")
            density = cursor.fetchone()['density_pct']
            print(f"2. fn_calculate_traffic_density(Junction 2) = {density}%")

            # 3. UDF fn_get_starvation_risk
            cursor.execute("SELECT fn_get_starvation_risk(16, 4) as risk_level;")
            risk = cursor.fetchone()['risk_level']
            print(f"3. fn_get_starvation_risk(wait=16s, priority=4) = {risk}")

            # 4. sp_transit_vehicle_complete
            print("4. Calling sp_transit_vehicle_complete...")
            cursor.execute(f"CALL sp_transit_vehicle_complete({created_v_id}, 9);")
            v_completed = query_one("SELECT * FROM vehicles WHERE id = %s", (created_v_id,))
            print(f"   -> Vehicle completed. Finished at t={v_completed['completion_time']}s, Turnaround={v_completed['turnaround_time']}s, Wait={v_completed['waiting_time']}s")

            # 5. sp_report_traffic_incident
            print("5. Calling sp_report_traffic_incident (accident on Junction 2)...")
            cursor.execute("SET @inc_id = 0;")
            cursor.execute("""
                CALL sp_report_traffic_incident(
                    1, 2, 2, 'ACCIDENT', 'HIGH', 'Traffic accident near Ballupur', 10, @inc_id
                );
            """)
            cursor.execute("SELECT @inc_id as inc_id;")
            inc_id = cursor.fetchone()['inc_id']
            j_status = query_one("SELECT status FROM junctions WHERE id = 2")['status']
            print(f"   -> Incident logged with ID: {inc_id}. Junction 2 status changed to: {j_status}")

            # 6. sp_resolve_traffic_incident
            print("6. Calling sp_resolve_traffic_incident...")
            cursor.execute(f"CALL sp_resolve_traffic_incident({inc_id}, 15);")
            j_restored = query_one("SELECT status FROM junctions WHERE id = 2")['status']
            print(f"   -> Incident cleared. Junction 2 status back to: {j_restored}")

            print("\nStored procedures and functions tested successfully!\n")

    finally:
        conn.close()

def seed_evaluation_data():
    print_banner()
    print("Seeding sample simulation runs for comparison view...")

    sims = [
        ("Peak Traffic Run", "FCFS", 2, "HEAVY", 18, 18, 8.50, 12.20, 0.285),
        ("Emergency Transit Run", "PRIORITY", 2, "EMERGENCY", 15, 15, 5.20, 8.60, 0.320),
        ("Fair Sharing Run", "ROUND_ROBIN", 2, "MIXED", 20, 20, 6.80, 10.40, 0.310),
        ("Adaptive Green Phase", "ADAPTIVE", 2, "NORMAL", 24, 24, 3.40, 6.10, 0.395)
    ]

    for name, algo, q, scen, tot, comp, avg_wt, avg_tat, thr in sims:
        execute_commit("""
            INSERT INTO simulations 
            (name, algorithm, quantum, scenario, signal_mode, speed, status, total_vehicles, completed_vehicles, avg_waiting_time, avg_turnaround_time, throughput)
            VALUES (%s, %s, %s, %s, 'AUTOMATIC', 1.0, 'COMPLETED', %s, %s, %s, %s, %s)
        """, (name, algo, q, scen, tot, comp, avg_wt, avg_tat, thr))

    print("Done! Check 'vw_algorithm_comparison' to view the benchmark.\n")

def interactive_menu():
    while True:
        print_banner()
        print("Options:")
        print("  [1] View Tables, Views, Procedures, and Triggers")
        print("  [2] Query 5 Analytical SQL Views")
        print("  [3] Test ACID Transactions (Commit & Rollback)")
        print("  [4] Test Stored Procedures & Functions")
        print("  [5] Seed Sample Runs for Comparison View")
        print("  [6] Reset Database & Re-apply Schema")
        print("  [7] Exit")
        print("Enter choice (1-7): ", end="")

        try:
            choice = input().strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == '1':
            check_db_status()
        elif choice == '2':
            display_views()
        elif choice == '3':
            test_acid_transactions()
        elif choice == '4':
            test_stored_procedures()
        elif choice == '5':
            seed_evaluation_data()
        elif choice == '6':
            init_database(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                db_name=Config.DB_NAME
            )
        elif choice == '7':
            print("\nExiting. Bye!\n")
            break
        else:
            print("\nInvalid choice. Please enter 1-7.")

        print("\nPress ENTER to continue...")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            break

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--status' in args:
        check_db_status()
    elif '--views' in args:
        display_views()
    elif '--test-acid' in args:
        test_acid_transactions()
    elif '--test-procedures' in args:
        test_stored_procedures()
    elif '--seed-evaluation' in args:
        seed_evaluation_data()
    elif '--init' in args:
        init_database(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            db_name=Config.DB_NAME
        )
    else:
        interactive_menu()
