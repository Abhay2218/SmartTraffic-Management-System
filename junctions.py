from flask import Blueprint, jsonify, request
from backend.database import query_all, query_one, execute_commit

junctions_bp = Blueprint('junctions', __name__)

@junctions_bp.route('', methods=['GET'])
def get_junctions():
    junctions = query_all("SELECT * FROM junctions ORDER BY id ASC")
    signals = query_all("SELECT * FROM traffic_signals ORDER BY junction_id, direction")
    
    # Group signals by junction
    signal_map = {}
    for s in signals:
        j_id = s['junction_id']
        if j_id not in signal_map:
            signal_map[j_id] = {}
        signal_map[j_id][s['direction']] = {
            'state': s['state'],
            'green_time': s['green_time']
        }

    for j in junctions:
        j['signals'] = signal_map.get(j['id'], {
            'NORTH': {'state': 'RED', 'green_time': 15},
            'SOUTH': {'state': 'RED', 'green_time': 15},
            'EAST':  {'state': 'RED', 'green_time': 15},
            'WEST':  {'state': 'RED', 'green_time': 15},
        })

    return jsonify({"status": "SUCCESS", "data": junctions})

@junctions_bp.route('/<int:j_id>', methods=['GET'])
def get_junction(j_id):
    junction = query_one("SELECT * FROM junctions WHERE id = %s", (j_id,))
    if not junction:
        return jsonify({"status": "ERROR", "message": f"Junction {j_id} not found"}), 404

    signals = query_all("SELECT * FROM traffic_signals WHERE junction_id = %s", (j_id,))
    junction['signals'] = {s['direction']: {'state': s['state'], 'green_time': s['green_time']} for s in signals}

    # Get active vehicle counts per direction at this junction
    counts = query_all(
        """SELECT direction, COUNT(*) as cnt FROM vehicles
           WHERE junction_id = %s AND status = 'WAITING'
           GROUP BY direction""",
        (j_id,)
    )
    queues = {'NORTH': 0, 'SOUTH': 0, 'EAST': 0, 'WEST': 0}
    for c in counts:
        queues[c['direction']] = c['cnt']
    junction['queues'] = queues

    return jsonify({"status": "SUCCESS", "data": junction})

@junctions_bp.route('/<int:j_id>', methods=['PUT'])
def update_junction(j_id):
    data = request.get_json() or {}
    capacity = data.get('capacity')
    status = data.get('status')

    if capacity is not None:
        execute_commit("UPDATE junctions SET capacity = %s WHERE id = %s", (capacity, j_id))
    if status is not None:
        execute_commit("UPDATE junctions SET status = %s WHERE id = %s", (status, j_id))

    updated = query_one("SELECT * FROM junctions WHERE id = %s", (j_id,))
    return jsonify({"status": "SUCCESS", "data": updated})
