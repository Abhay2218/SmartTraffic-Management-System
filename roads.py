from flask import Blueprint, jsonify, request
from backend.database import query_all, query_one, execute_commit

roads_bp = Blueprint('roads', __name__)

@roads_bp.route('', methods=['GET'])
def get_roads():
    sql = """
        SELECT r.*,
               sj.name AS source_name,
               dj.name AS dest_name
        FROM roads r
        JOIN junctions sj ON r.source_junction_id = sj.id
        JOIN junctions dj ON r.dest_junction_id = dj.id
        ORDER BY r.id ASC
    """
    roads = query_all(sql)
    return jsonify({"status": "SUCCESS", "data": roads})

@roads_bp.route('/<int:road_id>/toggle-closure', methods=['POST'])
def toggle_road_closure(road_id):
    road = query_one("SELECT * FROM roads WHERE id = %s", (road_id,))
    if not road:
        return jsonify({"status": "ERROR", "message": f"Road {road_id} not found"}), 404

    new_state = 0 if road['is_closed'] else 1
    execute_commit("UPDATE roads SET is_closed = %s WHERE id = %s", (new_state, road_id))
    
    updated = query_one("SELECT * FROM roads WHERE id = %s", (road_id,))
    return jsonify({"status": "SUCCESS", "data": updated})
