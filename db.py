import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_PATH

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_columns():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(schedules)")
    columns = [col[1] for col in cursor.fetchall()]
    if "created_at" not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN created_at TEXT")
    if "updated_at" not in columns:
        cursor.execute("ALTER TABLE schedules ADD COLUMN updated_at TEXT")
    conn.commit()
    conn.close()

def load_schedules():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM schedules", conn)
    conn.close()
    return df

def update_schedule(schedule_id: int, updates: dict):
    updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "UPDATE schedules SET " + ", ".join(f"{k}=?" for k in updates) + " WHERE id=?"
    values = list(updates.values()) + [schedule_id]
    cursor.execute(query, values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def insert_schedule(data: dict):
    data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    keys = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = list(data.values())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO schedules ({keys}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()

def delete_schedule(schedule_id):
    schedule_id = int(schedule_id)  # numpy 타입 방지
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE id=?", (schedule_id,))
    conn.commit()
    conn.close()
