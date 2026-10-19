from flask import Blueprint, jsonify, request
from backend.services.simulation_service import SimulationService
from backend.database import query_all, query_one, execute_commit

simulations_bp = Blueprint('simulations', __name__)

@simulations_bp.route('', methods=['GET'])
def get_simulations():
    sims = SimulationService.list_simulations()
    return jsonify({"status": "SUCCESS", "data": sims})

@simulations_bp.route('', methods=['POST'])
def create_simulation():
    data = request.get_json() or {}
    try:
        sim = SimulationService.create_simulation(data)
        return jsonify({"status": "SUCCESS", "data": sim}), 201
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@simulations_bp.route('/<int:sim_id>', methods=['GET'])
def get_simulation(sim_id):
    sim = SimulationService.get_simulation(sim_id)
    if not sim:
        return jsonify({"status": "ERROR", "message": f"Simulation {sim_id} not found"}), 404
    return jsonify({"status": "SUCCESS", "data": sim})

@simulations_bp.route('/<int:sim_id>/run', methods=['POST'])
@simulations_bp.route('/<int:sim_id>/start', methods=['POST'])
def start_simulation(sim_id):
    data = request.get_json() or {}
    algorithm = data.get('algorithm')
    quantum = data.get('quantum')
    scenario = data.get('scenario')

    # Optionally update algorithm/quantum/scenario before running
    if algorithm:
        execute_commit("UPDATE simulations SET algorithm = %s WHERE id = %s", (algorithm, sim_id))
    if quantum is not None:
        execute_commit("UPDATE simulations SET quantum = %s WHERE id = %s", (quantum, sim_id))
    if scenario:
        execute_commit("UPDATE simulations SET scenario = %s WHERE id = %s", (scenario, sim_id))
        SimulationService.seed_scenario_vehicles(sim_id, scenario)

    try:
        result = SimulationService.run_simulation(sim_id)
        return jsonify({"status": "SUCCESS", "data": result})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@simulations_bp.route('/<int:sim_id>/pause', methods=['POST'])
def pause_simulation(sim_id):
    try:
        sim = SimulationService.pause_simulation(sim_id)
        return jsonify({"status": "SUCCESS", "data": sim})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@simulations_bp.route('/<int:sim_id>/resume', methods=['POST'])
def resume_simulation(sim_id):
    try:
        sim = SimulationService.resume_simulation(sim_id)
        return jsonify({"status": "SUCCESS", "data": sim})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@simulations_bp.route('/<int:sim_id>/reset', methods=['POST'])
def reset_simulation(sim_id):
    try:
        sim = SimulationService.reset_simulation(sim_id)
        return jsonify({"status": "SUCCESS", "data": sim})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 400

@simulations_bp.route('/<int:sim_id>/state', methods=['GET'])
def get_simulation_state(sim_id):
    sim = SimulationService.get_simulation(sim_id)
    if not sim:
        return jsonify({"status": "ERROR", "message": f"Simulation {sim_id} not found"}), 404

    # Summary counts
    counts = query_one(
        """SELECT
             COUNT(*) AS total_vehicles,
             SUM(CASE WHEN status = 'RUNNING' THEN 1 ELSE 0 END) AS active_vehicles,
             SUM(CASE WHEN status = 'WAITING' THEN 1 ELSE 0 END) AS waiting_vehicles,
             SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_vehicles,
             SUM(CASE WHEN is_emergency = 1 AND status != 'COMPLETED' THEN 1 ELSE 0 END) AS emergency_vehicles
           FROM vehicles WHERE simulation_id = %s""",
        (sim_id,)
    )

    # Active incidents
    incidents = query_all("SELECT * FROM traffic_incidents WHERE simulation_id = %s AND is_active = 1", (sim_id,))

    # Junctions with signals and real-time waiting queues
    junctions = query_all("SELECT * FROM junctions ORDER BY id ASC")
    signals = query_all("SELECT * FROM traffic_signals ORDER BY junction_id, direction")
    queue_data = query_all(
        """SELECT junction_id, direction, COUNT(*) as cnt
           FROM vehicles WHERE simulation_id = %s AND status = 'WAITING'
           GROUP BY junction_id, direction""",
        (sim_id,)
    )

    # Map signals and queues to junctions
    j_map = {}
    for j in junctions:
        j_map[j['id']] = j
        j['signals'] = {}
        j['queues'] = {'NORTH': 0, 'SOUTH': 0, 'EAST': 0, 'WEST': 0}

    for s in signals:
        if s['junction_id'] in j_map:
            j_map[s['junction_id']]['signals'][s['direction']] = {
                'state': s['state'],
                'green_time': s['green_time']
            }

    for q in queue_data:
        if q['junction_id'] in j_map:
            j_map[q['junction_id']]['queues'][q['direction']] = q['cnt']

    # Recent events
    recent_events = query_all(
        """SELECT * FROM vehicle_events
           WHERE simulation_id = %s ORDER BY id DESC LIMIT 15""",
        (sim_id,)
    )

    state = {
        "simulation": sim,
        "summary": {
            "total_vehicles": counts['total_vehicles'] or 0,
            "active_vehicles": counts['active_vehicles'] or 0,
            "waiting_vehicles": counts['waiting_vehicles'] or 0,
            "completed_vehicles": counts['completed_vehicles'] or 0,
            "emergency_vehicles": counts['emergency_vehicles'] or 0,
            "junction_count": len(junctions),
            "active_incidents": len(incidents),
            "avg_waiting_time": float(sim['avg_waiting_time']),
            "avg_turnaround_time": float(sim['avg_turnaround_time']),
            "throughput": float(sim['throughput']),
            "current_tick": sim['current_tick']
        },
        "junctions": junctions,
        "incidents": incidents,
        "recent_events": recent_events
    }

    return jsonify({"status": "SUCCESS", "data": state})
