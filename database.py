import pymysql
from pymysql.cursors import DictCursor
from backend.config import Config

def get_connection():
    """Returns a new MySQL connection with DictCursor."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )

def query_all(sql, params=None):
    """Executes a SELECT query and returns all matching rows as dictionaries."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()

def query_one(sql, params=None):
    """Executes a SELECT query and returns a single row dictionary or None."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
    finally:
        conn.close()

def execute_commit(sql, params=None):
    """Executes an INSERT/UPDATE/DELETE query and commits. Returns lastrowid or affected rows."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            conn.commit()
            return last_id if last_id else affected
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute_transaction(operations):
    """
    Executes multiple SQL operations inside an ACID MySQL transaction.
    operations: list of tuples (sql, params)
    Rolls back completely if any operation fails.
    """
    conn = get_connection()
    results = []
    try:
        with conn.cursor() as cursor:
            for sql, params in operations:
                cursor.execute(sql, params or ())
                results.append({
                    'lastrowid': cursor.lastrowid,
                    'rowcount': cursor.rowcount
                })
            conn.commit()
            return results
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
