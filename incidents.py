from flask import Blueprint, jsonify, request
from backend.database import query_all, query_one, execute_commit, execute_transaction

incidents_bp = Blueprint('incidents', __name__)

@incidents_bp.route('', methods=['GET'])
def get_incidents():
    sim_id = request.args.get('simulation_id')
    sql = """
        SELECT i.*, j.name AS junction_name, r.name AS road_name
        FROM traffic_incidents i
        JOIN junctions j ON i.junction_id = j.id
        LEFT JOIN roads r ON i.road_id = r.id
    """
    params = []
    if sim_id:
        sql += " WHERE i.simulation_id = %s"
        params.append(sim_id)
    sql += " ORDER BY i.is_active DESC, i.id DESC"

    incidents = query_all(sql, params)
    return jsonify({"status": "SUCCESS", "data": incidents})

@incidents_bp.route('', methods=['POST'])
def create_incident():
    data = request.get_json() or {}
    sim_id = data.get('simulation_id', 1)
    junction_id = data.get('junction_id')
    road_id = data.get('road_id')
    inc_type = data.get('incident_type', 'ACCIDENT').upper()
    severity = data.get('severity', 'HIGH').upper()
    description = data.get('description', f'{inc_type} reported at junction')

    if not junction_id:
        return jsonify({"status": "ERROR", "message": "junction_id is required"}), 400

    if inc_type not in ['ACCIDENT', 'ROAD_CLOSURE', 'CONGESTION', 'EMERGENCY_CORRIDOR']:
        return jsonify({"status": "ERROR", "message": "Invalid incident_type"}), 400

    ops = [
        ("""INSERT INTO traffic_incidents
            (simulation_id, junction_id, road_id, incident_type, severity, description, is_active, reported_time)
            VALUES (%s, %s, %s, %s, %s, %s, 1, 0)""",
         (sim_id, junction_id, road_id, inc_type, severity, description))
    ]

    # Dynamically affect simulation behaviour
    if inc_type in ['ACCIDENT', 'ROAD_CLOSURE']:
        if road_id:
            ops.append(("UPDATE roads SET is_closed = 1 WHERE id = %s", (road_id,)))
        ops.append(("UPDATE junctions SET status = 'BLOCKED' WHERE id = %s", (junction_id,)))
    elif inc_type == 'CONGESTION':
        ops.append(("UPDATE junctions SET status = 'CONGESTED' WHERE id = %s", (junction_id,)))

    res = execute_transaction(ops)
    new_id = res[0]['lastrowid']

    created = query_one("SELECT * FROM traffic_incidents WHERE id = %s", (new_id,))
    return jsonify({"status": "SUCCESS", "data": created}), 201

@incidents_bp.route('/<int:inc_id>', methods=['GET'])
def get_incident(inc_id):
    inc = query_one("SELECT * FROM traffic_incidents WHERE id = %s", (inc_id,))
    if not inc:
        return jsonify({"status": "ERROR", "message": f"Incident {inc_id} not found"}), 404
    return jsonify({"status": "SUCCESS", "data": inc})

@incidents_bp.route('/<int:inc_id>', methods=['PUT'])
def update_incident(inc_id):
    inc = query_one("SELECT * FROM traffic_incidents WHERE id = %s", (inc_id,))
    if not inc:
        return jsonify({"status": "ERROR", "message": f"Incident {inc_id} not found"}), 404
    data = request.get_json() or {}
    severity = data.get('severity', inc['severity'])
    description = data.get('description', inc['description'])
    execute_commit(
        "UPDATE traffic_incidents SET severity = %s, description = %s WHERE id = %s",
        (severity, description, inc_id)
    )
    updated = query_one("SELECT * FROM traffic_incidents WHERE id = %s", (inc_id,))
    return jsonify({"status": "SUCCESS", "data": updated})

@incidents_bp.route('/<int:inc_id>', methods=['DELETE'])
def delete_incident(inc_id):
    inc = query_one("SELECT * FROM traffic_incidents WHERE id = %s", (inc_id,))
    if not inc:
        return jsonify({"status": "ERROR", "message": f"Incident {inc_id} not found"}), 404
    execute_commit("DELETE FROM traffic_incidents WHERE id = %s", (inc_id,))
    return jsonify({"status": "SUCCESS", "message": f"Incident {inc_id} deleted"})

@incidents_bp.route('/<int:inc_id>/resolve', methods=['PUT', 'POST'])
def resolve_incident(inc_id):
    inc = query_one("SELECT * FROM traffic_incidents WHERE id = %s", (inc_id,))
    if not inc:
        return jsonify({"status": "ERROR", "message": f"Incident {inc_id} not found"}), 404

    ops = [
        ("UPDATE traffic_incidents SET is_active = 0, resolved_time = 100 WHERE id = %s", (inc_id,))
    ]

    # Reopen road and set junction back to ACTIVE
    if inc.get('road_id'):
        ops.append(("UPDATE roads SET is_closed = 0 WHERE id = %s", (inc['road_id'],)))
    ops.append(("UPDATE junctions SET status = 'ACTIVE' WHERE id = %s", (inc['junction_id'],)))

    execute_transaction(ops)

    updated = query_one("SELECT * FROM traffic_incidents WHERE id = %s", (inc_id,))
    return jsonify({"status": "SUCCESS", "message": "Incident resolved successfully", "data": updated})
