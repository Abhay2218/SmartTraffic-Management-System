import os
from flask import Blueprint, jsonify
from backend.services.c_engine_service import CEngineService
from backend.database import query_one
from backend.config import Config

system_bp = Blueprint('system', __name__)

@system_bp.route('/health', methods=['GET'])
def health_check():
    db_ok = False
    db_version = "Unknown"
    try:
        row = query_one("SELECT VERSION() as v")
        if row:
            db_ok = True
            db_version = row['v']
    except Exception as e:
        db_version = str(e)

    c_engine_ok = os.path.exists(Config.C_ENGINE_PATH)

    return jsonify({
        "status": "HEALTHY" if (db_ok and c_engine_ok) else "DEGRADED",
        "database": {
            "connected": db_ok,
            "version": db_version,
            "name": Config.DB_NAME
        },
        "c_engine": {
            "available": c_engine_ok,
            "path": Config.C_ENGINE_PATH
        }
    })

@system_bp.route('/sync-test', methods=['GET', 'POST'])
def test_synchronization():
    """
    Directly invokes the C OS Engine --test-sync mode to prove
    Mutex, Counting Semaphore, and Critical Section invariant enforcement.
    """
    try:
        res = CEngineService.run_sync_test()
        return jsonify({"status": "SUCCESS", "data": res})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500
