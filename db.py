import sqlite3
from datetime import datetime, timedelta

DB_NAME = "eco_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(actions)")
    columns = cursor.fetchall()

    if not columns or not any(col[1] == 'points' for col in columns):
        print("Recreating database with correct schema...")
        cursor.execute("DROP TABLE IF EXISTS actions")
        cursor.execute('''
            CREATE TABLE actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                points INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')

    conn.commit()
    conn.close()

def insert_action(action, points):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO actions (action, points, timestamp) VALUES (?, ?, ?)",
                   (action, points, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_total_points():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SUM(points) FROM actions")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else 0
    except sqlite3.OperationalError:
        conn.close()
        return 0

def get_weekly_points():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT SUM(points) FROM actions WHERE timestamp >= ?", (one_week_ago,))
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else 0
    except sqlite3.OperationalError:
        conn.close()
        return 0

def get_action_history():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT action, points, timestamp FROM actions ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.OperationalError:
        conn.close()
        return []

def reset_all_data():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM actions")
        print("🧪 Before reset:", cursor.fetchone()[0])

        cursor.execute("DELETE FROM actions")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='actions'")

        cursor.execute("SELECT COUNT(*) FROM actions")
        print("🧪 After reset:", cursor.fetchone()[0])

        conn.commit()
        conn.close()
        return True
    except Exception as ex:
        print(f"❌ Database error: {ex}")
        return False

def get_points_per_day_last_week():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=6)

    cursor.execute("""
        SELECT DATE(timestamp) as day, SUM(points)
        FROM actions
        WHERE DATE(timestamp) BETWEEN ? AND ?
        GROUP BY day
        ORDER BY day ASC
    """, (seven_days_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")))

    rows = cursor.fetchall()
    conn.close()

    daily_points = { (seven_days_ago + timedelta(days=i)).strftime("%Y-%m-%d"): 0 for i in range(7) }
    for day, points in rows:
        daily_points[day] = points if points else 0

    return list(daily_points.items())
