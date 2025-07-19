import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple
from contextlib import contextmanager

class EcoDatabase:
    def __init__(self, db_name: str = "eco_tracker.db"):
        self.db_name = db_name

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    target_count INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    completed INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def insert_action(self, action: str, points: int) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO actions (action, points, timestamp) VALUES (?, ?, ?)",
                    (action, points, timestamp)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error inserting action: {e}")
            return False

    def get_total_points(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(points) FROM actions")
            result = cursor.fetchone()[0]
            return result if result is not None else 0

    def get_weekly_points(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT SUM(points) FROM actions WHERE timestamp >= ?", (one_week_ago,))
            result = cursor.fetchone()[0]
            return result if result is not None else 0

    def get_action_history(self) -> List[Tuple[str, int, str]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT action, points, timestamp FROM actions ORDER BY timestamp DESC")
            return cursor.fetchall()

    def get_points_per_day_last_week(self) -> List[Tuple[str, int]]:
        with self.get_connection() as conn:
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
            daily_points = {
                (seven_days_ago + timedelta(days=i)).strftime("%Y-%m-%d"): 0
                for i in range(7)
            }
            for day, points in rows:
                if points is not None:
                    daily_points[day] = points
            return list(daily_points.items())

    def reset_all_data(self) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM actions")
            cursor.execute("DELETE FROM challenges")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='actions'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='challenges'")
            conn.commit()
            return True

    def insert_challenge(self, description: str, target_count: int, start_date: str, end_date: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO challenges (description, target_count, start_date, end_date) VALUES (?, ?, ?, ?)",
                (description, target_count, start_date, end_date)
            )
            conn.commit()

    def update_challenge_completion(self) -> List[Tuple[int, str, int, str, str, int, int]]:
        today = datetime.now().strftime("%Y-%m-%d")
        updated_challenges = []

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, description, target_count, start_date, end_date, completed
                FROM challenges 
                WHERE start_date <= ? AND end_date >= ? AND completed = 0
            ''', (today, today))
            challenges = cursor.fetchall()

            for cid, desc, target, start, end, completed in challenges:
                start_datetime = f"{start} 00:00:00"
                end_datetime = f"{end} 23:59:59"

                cursor.execute('''
                    SELECT COUNT(*) FROM actions
                    WHERE timestamp BETWEEN ? AND ?
                ''', (start_datetime, end_datetime))
                progress = cursor.fetchone()[0] or 0

                if progress >= target and completed == 0:
                    cursor.execute("UPDATE challenges SET completed = 1 WHERE id = ?", (cid,))
                    completed = 1

                updated_challenges.append((cid, desc, target, start, end, completed, progress))

            conn.commit()

        return updated_challenges

    def get_active_challenges(self) -> List[Tuple[int, str, int, str, str, int, int]]:
        today = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM challenges 
                WHERE start_date <= ? AND end_date >= ? AND completed = 0
            ''', (today, today))
            challenges = cursor.fetchall()

        enriched = []
        for cid, desc, target, start, end, completed in challenges:
            actions_done = self.get_actions_count_in_date_range(start, end)
            enriched.append((cid, desc, target, start, end, completed, actions_done))
        return enriched

    def get_actions_count_in_date_range(self, start_date: str, end_date: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            start_datetime = f"{start_date} 00:00:00"
            end_datetime = f"{end_date} 23:59:59"
            cursor.execute("""
                SELECT COUNT(*) 
                FROM actions 
                WHERE timestamp >= ? AND timestamp <= ?
            """, (start_datetime, end_datetime))
            result = cursor.fetchone()[0]
            return result if result is not None else 0
