from flask import Blueprint, jsonify, request
from backend.database import query_one, execute_transaction

signals_bp = Blueprint('signals', __name__)

@signals_bp.route('/manual', methods=['POST'])
def manual_signal_control():
    data = request.get_json() or {}
    junction_id = data.get('junction_id')
    direction = (data.get('direction') or '').upper()
    green_time = int(data.get('green_time', 20))
    simulation_id = int(data.get('simulation_id', 1))

    if not junction_id:
        return jsonify({"status": "ERROR", "message": "junction_id is required"}), 400

    if direction not in ['NORTH', 'SOUTH', 'EAST', 'WEST']:
        return jsonify({"status": "ERROR", "message": "direction must be NORTH, SOUTH, EAST, or WEST"}), 400

    junction = query_one("SELECT * FROM junctions WHERE id = %s", (junction_id,))
    if not junction:
        return jsonify({"status": "ERROR", "message": f"Junction {junction_id} not found"}), 404

    # Enforce MUTUAL EXCLUSION: Selected direction is GREEN, all conflicting orthogonal directions are RED!
    ops = [
        # Set all directions to RED first
        ("UPDATE traffic_signals SET state = 'RED' WHERE junction_id = %s", (junction_id,)),
        # Set the selected direction to GREEN with requested green time
        ("""UPDATE traffic_signals SET state = 'GREEN', green_time = %s
            WHERE junction_id = %s AND direction = %s""", (green_time, junction_id, direction)),
        # Update junction active direction
        ("""UPDATE junctions SET active_direction = %s, current_phase = %s
            WHERE id = %s""", (direction, f"MANUAL_{direction}_GREEN", junction_id)),
        # Record signal event for audit log
        ("""INSERT INTO signal_events
            (junction_id, simulation_id, direction, old_state, new_state, duration, reason)
            VALUES (%s, %s, %s, 'RED', 'GREEN', %s, 'Manual Operator Override')""",
         (junction_id, simulation_id, direction, green_time))
    ]

    execute_transaction(ops)

    # Return current signal states for all directions so callers can verify mutual exclusion
    from backend.database import query_all
    current_signals = query_all(
        "SELECT direction, state, green_time FROM traffic_signals WHERE junction_id = %s ORDER BY direction",
        (junction_id,)
    )

    return jsonify({
        "status": "SUCCESS",
        "message": f"Manual signal override applied at Junction {junction_id}: {direction} is GREEN (Conflicting directions set to RED)",
        "junction_id": junction_id,
        "active_direction": direction,
        "green_time": green_time,
        "data": {
            "junction_id": junction_id,
            "active_direction": direction,
            "green_time": green_time,
            "signals": current_signals
        }
    })

@signals_bp.route('/automatic', methods=['POST'])
def automatic_signal_mode():
    data = request.get_json() or {}
    junction_id = data.get('junction_id')
    simulation_id = int(data.get('simulation_id', 1))

    if not junction_id:
        return jsonify({"status": "ERROR", "message": "junction_id is required"}), 400

    ops = [
        ("UPDATE junctions SET current_phase = 'AUTOMATIC_ADAPTIVE' WHERE id = %s", (junction_id,)),
        ("""INSERT INTO signal_events
            (junction_id, simulation_id, direction, old_state, new_state, duration, reason)
            VALUES (%s, %s, 'NORTH', 'RED', 'RED', 0, 'Restored Automatic Control')""",
         (junction_id, simulation_id))
    ]
    execute_transaction(ops)

    return jsonify({
        "status": "SUCCESS",
        "message": f"Junction {junction_id} returned to automatic adaptive mode",
        "junction_id": junction_id
    })
