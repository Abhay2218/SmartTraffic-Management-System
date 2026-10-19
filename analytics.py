from flask import Blueprint, jsonify, request
from backend.database import query_all, query_one
from backend.services.c_engine_service import CEngineService
from backend.services.simulation_service import SimulationService

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('', methods=['GET'])
def get_analytics_summary():
    """
    Returns aggregated metrics grouped by scheduling algorithm from historical runs.
    """
    sql = """
        SELECT
            algorithm,
            COUNT(*) as runs_count,
            ROUND(AVG(avg_waiting_time), 2) as avg_waiting_time,
            ROUND(AVG(avg_turnaround_time), 2) as avg_turnaround_time,
            ROUND(AVG(throughput), 3) as avg_throughput
        FROM simulations
        WHERE status IN ('RUNNING', 'COMPLETED')
        GROUP BY algorithm
    """
    summary = query_all(sql)
    return jsonify({"status": "SUCCESS", "data": summary})

@analytics_bp.route('/<int:sim_id>', methods=['GET'])
def get_simulation_analytics(sim_id):
    sim = SimulationService.get_simulation(sim_id)
    if not sim:
        return jsonify({"status": "ERROR", "message": f"Simulation {sim_id} not found"}), 404

    # Performance metrics
    metrics = query_all("SELECT * FROM performance_metrics WHERE simulation_id = %s", (sim_id,))
    
    # Vehicle turnaround and waiting times
    vehicles = query_all(
        """SELECT id, plate_number, vehicle_type, junction_id, direction,
                  arrival_time, burst_time, waiting_time, turnaround_time,
                  completion_time, is_emergency, status
           FROM vehicles WHERE simulation_id = %s
           ORDER BY completion_time ASC, id ASC""",
        (sim_id,)
    )

    # Emergency vehicles stats
    emerg_stats = query_one(
        """SELECT
             COUNT(*) as count,
             ROUND(AVG(waiting_time), 2) as avg_wait,
             ROUND(AVG(turnaround_time), 2) as avg_tat
           FROM vehicles
           WHERE simulation_id = %s AND is_emergency = 1""",
        (sim_id,)
    )

    return jsonify({
        "status": "SUCCESS",
        "simulation": sim,
        "metrics": metrics,
        "vehicles": vehicles,
        "emergency_stats": emerg_stats
    })

@analytics_bp.route('/compare', methods=['GET', 'POST'])
def run_comparison_benchmark():
    """
    Executes identical vehicle workload through FCFS, Priority, Round Robin, and Adaptive
    via the C OS Scheduling Engine, returning exact metrics for charts and comparative analysis.
    """
    sim_id = request.args.get('simulation_id', 1)
    quantum = int(request.args.get('quantum', 2))

    junctions = query_all("SELECT id, name FROM junctions ORDER BY id ASC")
    vehicles = query_all(
        """SELECT id, junction_id, vehicle_type AS type, direction,
                  arrival_time, burst_time, initial_priority AS priority, is_emergency
           FROM vehicles WHERE simulation_id = %s
           ORDER BY arrival_time ASC, id ASC""",
        (sim_id,)
    )

    if not vehicles:
        # Fallback to simulation 1 if requested simulation has no vehicles
        vehicles = query_all(
            """SELECT id, junction_id, vehicle_type AS type, direction,
                      arrival_time, burst_time, initial_priority AS priority, is_emergency
               FROM vehicles WHERE simulation_id = 1
               ORDER BY arrival_time ASC, id ASC"""
        )

    algorithms = ['FCFS', 'PRIORITY', 'ROUND_ROBIN', 'ADAPTIVE']
    results = {}

    for alg in algorithms:
        payload = {
            "algorithm": alg,
            "quantum": quantum,
            "aging_threshold": 4,
            "junctions": [{"id": j['id'], "name": j['name']} for j in junctions],
            "vehicles": vehicles
        }
        res = CEngineService.run_scheduling(payload)
        m = res.get('metrics', {})
        results[alg] = {
            "avg_waiting_time": m.get('avg_waiting_time', 0.0),
            "avg_turnaround_time": m.get('avg_turnaround_time', 0.0),
            "throughput": m.get('throughput', 0.0),
            "total_time": m.get('total_time', 0),
            "completed_vehicles": m.get('completed_vehicles', 0),
            "emergency_vehicles": m.get('emergency_vehicles', 0),
            "avg_emergency_wait": m.get('avg_emergency_wait', 0.0),
            "execution_order": res.get('execution_order', [])
        }

    return jsonify({
        "status": "SUCCESS",
        "benchmark_workload": {
            "simulation_id": sim_id,
            "total_vehicles": len(vehicles),
            "quantum": quantum
        },
        "comparison": results
    })
