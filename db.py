import csv
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class EcoAction:
    action: str
    points: int
    timestamp: str
    user_id: int
    id: Optional[int] = None

@dataclass
class Challenge:
    name: str
    description: str
    target_count: int
    user_id: int
    current_count: int = 0
    completed: bool = False
    created_date: str = ""
    completed_date: Optional[str] = None
    id: Optional[int] = None

@dataclass
class StreakData:
    user_id: int
    current_streak: int = 0
    longest_streak: int = 0
    last_action_date: Optional[str] = None
    id: Optional[int] = None

@dataclass
class ImpactData:
    co2_saved_kg: float = 0.0
    gas_saved_gallons: float = 0.0
    trees_equivalent: int = 0
    id: Optional[int] = None

@dataclass
class User:
    username: str
    password_hash: str
    id: Optional[int] = None

class CSVDatabase:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.csv")
        self.actions_file = os.path.join(data_dir, "actions.csv")
        self.challenges_file = os.path.join(data_dir, "challenges.csv")
        self.streak_file = os.path.join(data_dir, "streak_data.csv")
        
        self._ensure_data_directory()
        self._initialize_csv_files()

    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _initialize_csv_files(self):
        """Initialize CSV files with headers if they don't exist"""
        
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'username', 'password_hash'])

        if not os.path.exists(self.actions_file):
            with open(self.actions_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'user_id', 'action', 'points', 'timestamp'])

        if not os.path.exists(self.challenges_file):
            with open(self.challenges_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'user_id', 'name', 'description', 'target_count', 
                               'current_count', 'completed', 'created_date', 'completed_date'])

        if not os.path.exists(self.streak_file):
            with open(self.streak_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'user_id', 'current_streak', 'longest_streak', 'last_action_date'])

    def _get_next_id(self, csv_file: str) -> int:
        """Get the next available ID for a CSV file"""
        try:
            data = self.read_csv_safe(csv_file)
            if not data:
                return 1
            ids = [int(row['id']) for row in data if row.get('id') and str(row['id']).isdigit()]
            return max(ids) + 1 if ids else 1
        except (FileNotFoundError, ValueError, KeyError):
            return 1

    def read_csv_safe(self, file_path: str) -> List[Dict]:
        """Safely read CSV file and return list of dictionaries"""
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = []
                for row in reader:
                    for key, value in row.items():
                        if key in ['id', 'user_id', 'points', 'target_count', 'current_count', 'current_streak', 'longest_streak']:
                            try:
                                row[key] = int(value) if value else 0
                            except ValueError:
                                row[key] = 0
                        elif key == 'completed':
                            row[key] = value.lower() in ['true', '1', 'yes'] if value else False
                    data.append(row)
                return data
        except (FileNotFoundError, csv.Error):
            return []

    def write_csv_safe(self, file_path: str, data: List[Dict], fieldnames: List[str]):
        """Safely write data to CSV file"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

class UserManager:
    def __init__(self, db: CSVDatabase):
        self.db = db

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username: str, password: str) -> Optional[User]:
        password_hash = self._hash_password(password)
        
        users = self.db.read_csv_safe(self.db.users_file)
        if any(user['username'] == username for user in users):
            print(f"User '{username}' already exists.")
            return None

        try:
            user_id = self.db._get_next_id(self.db.users_file)
            
            users.append({
                'id': user_id,
                'username': username,
                'password_hash': password_hash
            })
            
            self.db.write_csv_safe(self.db.users_file, users, ['id', 'username', 'password_hash'])

            streak_data = self.db.read_csv_safe(self.db.streak_file)
            streak_data.append({
                'id': self.db._get_next_id(self.db.streak_file),
                'user_id': user_id,
                'current_streak': 0,
                'longest_streak': 0,
                'last_action_date': ''
            })
            self.db.write_csv_safe(self.db.streak_file, streak_data, 
                                 ['id', 'user_id', 'current_streak', 'longest_streak', 'last_action_date'])

            challenges = self.db.read_csv_safe(self.db.challenges_file)
            default_challenges = [
                ("Eco Beginner", "Complete 10 eco-actions", 10),
                ("Green Warrior", "Complete 20 eco-actions in a month", 20),
                ("Eco Champion", "Complete 50 eco-actions", 50),
                ("Planet Protector", "Complete 100 eco-actions", 100),
                ("Recycling Master", "Recycle 15 times", 15),
                ("Transport Hero", "Use eco-transport 25 times", 25)
            ]
            
            challenge_id = self.db._get_next_id(self.db.challenges_file)
            for name, desc, target in default_challenges:
                challenges.append({
                    'id': challenge_id,
                    'user_id': user_id,
                    'name': name,
                    'description': desc,
                    'target_count': target,
                    'current_count': 0,
                    'completed': False,
                    'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'completed_date': ''
                })
                challenge_id += 1
            
            self.db.write_csv_safe(self.db.challenges_file, challenges,
                                 ['id', 'user_id', 'name', 'description', 'target_count', 
                                  'current_count', 'completed', 'created_date', 'completed_date'])

            return User(id=user_id, username=username, password_hash=password_hash)
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        password_hash = self._hash_password(password)
        
        try:
            users = self.db.read_csv_safe(self.db.users_file)
            for user in users:
                if user['username'] == username and user['password_hash'] == password_hash:
                    return User(id=user['id'], username=user['username'], password_hash=user['password_hash'])
            return None
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        try:
            users = self.db.read_csv_safe(self.db.users_file)
            for user in users:
                if user['id'] == user_id:
                    return User(id=user['id'], username=user['username'], password_hash=user['password_hash'])
            return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

class ActionManager:
    def __init__(self, db: CSVDatabase):
        self.db = db

    def add_action(self, user_id: int, action: str, points: int) -> bool:
        try:
            actions = self.db.read_csv_safe(self.db.actions_file)
            action_id = self.db._get_next_id(self.db.actions_file)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            actions.append({
                'id': action_id,
                'user_id': user_id,
                'action': action,
                'points': points,
                'timestamp': timestamp
            })
            
            self.db.write_csv_safe(self.db.actions_file, actions, 
                                 ['id', 'user_id', 'action', 'points', 'timestamp'])

            streak_manager = StreakManager(self.db)
            challenge_manager = ChallengeManager(self.db)
            
            streak_manager.update_streak(user_id)
            challenge_manager.update_challenges(user_id, action)
            
            return True
        except Exception as e:
            print(f"❌ Error adding action: {e}")
            return False

    def get_action_history(self, user_id: int) -> List[Tuple[str, int, str]]:
        try:
            actions = self.db.read_csv_safe(self.db.actions_file)
            user_actions = [action for action in actions if action['user_id'] == user_id]
            
            user_actions.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return [(action['action'], action['points'], action['timestamp']) for action in user_actions]
        except Exception as e:
            print(f"Error getting action history: {e}")
            return []

    def get_total_action_count(self, user_id: int) -> int:
        try:
            actions = self.db.read_csv_safe(self.db.actions_file)
            return len([action for action in actions if action['user_id'] == user_id])
        except Exception as e:
            print(f"Error getting total action count: {e}")
            return 0

class PointsManager:
    def __init__(self, db: CSVDatabase):
        self.db = db

    def get_total_points(self, user_id: int) -> int:
        try:
            actions = self.db.read_csv_safe(self.db.actions_file)
            user_actions = [action for action in actions if action['user_id'] == user_id]
            return sum(action['points'] for action in user_actions)
        except Exception as e:
            print(f"Error getting total points: {e}")
            return 0

    def get_weekly_points(self, user_id: int) -> int:
        try:
            actions = self.db.read_csv_safe(self.db.actions_file)
            one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            
            user_actions = [
                action for action in actions 
                if action['user_id'] == user_id and action['timestamp'] >= one_week_ago
            ]
            return sum(action['points'] for action in user_actions)
        except Exception as e:
            print(f"Error getting weekly points: {e}")
            return 0

    def get_points_per_day_last_week(self, user_id: int) -> List[Tuple[str, int]]:
        try:
            actions = self.db.read_csv_safe(self.db.actions_file)
            today = datetime.now().date()
            seven_days_ago = today - timedelta(days=6)
            
            daily_points = {(seven_days_ago + timedelta(days=i)).strftime("%Y-%m-%d"): 0 
                          for i in range(7)}
            
            for action in actions:
                if action['user_id'] == user_id:
                    try:
                        action_date = datetime.strptime(action['timestamp'], "%Y-%m-%d %H:%M:%S").date()
                        date_str = action_date.strftime("%Y-%m-%d")
                        if date_str in daily_points:
                            daily_points[date_str] += action['points']
                    except ValueError:
                        continue
            
            return list(daily_points.items())
        except Exception as e:
            print(f"Error getting daily points: {e}")
            return []

class StreakManager:
    def __init__(self, db: CSVDatabase):
        self.db = db

    def update_streak(self, user_id: int) -> None:
        try:
            streak_data = self.db.read_csv_safe(self.db.streak_file)
            today = datetime.now().date()
            
            user_streak = None
            user_index = -1
            for i, streak in enumerate(streak_data):
                if streak['user_id'] == user_id:
                    user_streak = streak
                    user_index = i
                    break
            
            if user_streak:
                current_streak = user_streak['current_streak']
                longest_streak = user_streak['longest_streak']
                last_action_date = user_streak['last_action_date']
                
                if last_action_date:
                    try:
                        last_date = datetime.strptime(last_action_date.split()[0], "%Y-%m-%d").date()
                        
                        if last_date == today:
                            return
                        elif last_date == today - timedelta(days=1):
                            current_streak += 1
                        else:
                            current_streak = 1
                    except ValueError:
                        current_streak = 1
                else:
                    current_streak = 1
                
                longest_streak = max(longest_streak, current_streak)
                
                streak_data[user_index].update({
                    'current_streak': current_streak,
                    'longest_streak': longest_streak,
                    'last_action_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                streak_data.append({
                    'id': self.db._get_next_id(self.db.streak_file),
                    'user_id': user_id,
                    'current_streak': 1,
                    'longest_streak': 1,
                    'last_action_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            self.db.write_csv_safe(self.db.streak_file, streak_data,
                                 ['id', 'user_id', 'current_streak', 'longest_streak', 'last_action_date'])
                                 
        except Exception as e:
            print(f"Error updating streak: {e}")

    def get_streak_data(self, user_id: int) -> Tuple[int, int]:
        try:
            streak_data = self.db.read_csv_safe(self.db.streak_file)
            for streak in streak_data:
                if streak['user_id'] == user_id:
                    return (streak['current_streak'], streak['longest_streak'])
            return (0, 0)
        except Exception as e:
            print(f"Error getting streak data: {e}")
            return (0, 0)

class ChallengeManager:
    def __init__(self, db: CSVDatabase):
        self.db = db

    def update_challenges(self, user_id: int, action: str) -> None:
        try:
            challenges = self.db.read_csv_safe(self.db.challenges_file)
            action_manager = ActionManager(self.db)
            total_actions = action_manager.get_total_action_count(user_id)
            
            for i, challenge in enumerate(challenges):
                if challenge['user_id'] == user_id:
                    if challenge['name'] in ['Eco Beginner', 'Green Warrior', 'Eco Champion', 'Planet Protector']:
                        challenges[i]['current_count'] = total_actions
                    
                    elif challenge['name'] == 'Recycling Master' and action == 'Recycle':
                        actions = self.db.read_csv_safe(self.db.actions_file)
                        recycle_count = len([a for a in actions if a['user_id'] == user_id and a['action'] == 'Recycle'])
                        challenges[i]['current_count'] = recycle_count
                    
                    elif challenge['name'] == 'Transport Hero' and action in ['Bike', 'Walk', 'Public Transport']:
                        actions = self.db.read_csv_safe(self.db.actions_file)
                        transport_count = len([a for a in actions if a['user_id'] == user_id and 
                                             a['action'] in ['Bike', 'Walk', 'Public Transport']])
                        challenges[i]['current_count'] = transport_count
                    
                    if (challenges[i]['current_count'] >= challenges[i]['target_count'] and 
                        not challenges[i]['completed']):
                        challenges[i]['completed'] = True
                        challenges[i]['completed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.db.write_csv_safe(self.db.challenges_file, challenges,
                                 ['id', 'user_id', 'name', 'description', 'target_count', 
                                  'current_count', 'completed', 'created_date', 'completed_date'])
                                  
        except Exception as e:
            print(f"Error updating challenges: {e}")

    def get_challenges(self, user_id: int) -> List[Tuple]:
        try:
            challenges = self.db.read_csv_safe(self.db.challenges_file)
            user_challenges = [c for c in challenges if c['user_id'] == user_id]
            
            user_challenges.sort(key=lambda x: (x['completed'], x['id']))
            
            return [(c['name'], c['description'], c['current_count'], 
                    c['target_count'], c['completed']) for c in user_challenges]
        except Exception as e:
            print(f"Error getting challenges: {e}")
            return []

class EnvironmentalImpactManager:
    def __init__(self, db: CSVDatabase):
        self.db = db
        self.impact_values = {
            "Recycle": {"co2": 0.5, "gas": 0.0},
            "Bike": {"co2": 2.3, "gas": 0.8},
            "Walk": {"co2": 2.3, "gas": 0.8},
            "Public Transport": {"co2": 1.2, "gas": 0.4},
            "Plant Seed": {"co2": 22.0, "gas": 0.0},
            "Pick Up Trash": {"co2": 0.2, "gas": 0.0}
        }

    def calculate_total_impact(self, user_id: int) -> ImpactData:
        try:
            actions = self.db.read_csv_safe(self.db.actions_file)
            user_actions = [action for action in actions if action['user_id'] == user_id]
            
            action_counts = {}
            for action in user_actions:
                action_type = action['action']
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            total_co2 = 0.0
            total_gas = 0.0
            
            for action_type, count in action_counts.items():
                if action_type in self.impact_values:
                    total_co2 += self.impact_values[action_type]["co2"] * count
                    total_gas += self.impact_values[action_type]["gas"] * count
            
            trees_equivalent = int(total_co2 / 22)
            
            return ImpactData(
                co2_saved_kg=total_co2,
                gas_saved_gallons=total_gas,
                trees_equivalent=trees_equivalent
            )
        except Exception as e:
            print(f"Error calculating total impact: {e}")
            return ImpactData()

    def get_weekly_impact(self, user_id: int) -> ImpactData:
        try:
            actions = self.db.read_csv_safe(self.db.actions_file)
            one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            
            user_actions = [
                action for action in actions 
                if action['user_id'] == user_id and action['timestamp'] >= one_week_ago
            ]
            
            action_counts = {}
            for action in user_actions:
                action_type = action['action']
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            total_co2 = 0.0
            total_gas = 0.0
            
            for action_type, count in action_counts.items():
                if action_type in self.impact_values:
                    total_co2 += self.impact_values[action_type]["co2"] * count
                    total_gas += self.impact_values[action_type]["gas"] * count
            
            trees_equivalent = int(total_co2 / 22)
            
            return ImpactData(
                co2_saved_kg=total_co2,
                gas_saved_gallons=total_gas,
                trees_equivalent=trees_equivalent
            )
        except Exception as e:
            print(f"Error calculating weekly impact: {e}")
            return ImpactData()

class EcoTracker:
    def __init__(self, data_dir: str = "data"):
        self.db = CSVDatabase(data_dir)
        self.user_manager = UserManager(self.db)
        self.action_manager = ActionManager(self.db)
        self.points_manager = PointsManager(self.db)
        self.streak_manager = StreakManager(self.db)
        self.challenge_manager = ChallengeManager(self.db)
        self.impact_manager = EnvironmentalImpactManager(self.db)
        self.current_user_id: Optional[int] = None

    def set_current_user(self, user_id: int):
        self.current_user_id = user_id

    def log_action(self, action: str, points: int) -> bool:
        if self.current_user_id is None:
            print("Error: No user logged in.")
            return False
        return self.action_manager.add_action(self.current_user_id, action, points)

    def get_stats(self) -> dict:
        if self.current_user_id is None:
            return {}
        return {
            'total_points': self.points_manager.get_total_points(self.current_user_id),
            'weekly_points': self.points_manager.get_weekly_points(self.current_user_id),
            'total_actions': self.action_manager.get_total_action_count(self.current_user_id),
            'streak_data': self.streak_manager.get_streak_data(self.current_user_id),
            'challenges': self.challenge_manager.get_challenges(self.current_user_id),
            'action_history': self.action_manager.get_action_history(self.current_user_id),
            'daily_points_last_week': self.points_manager.get_points_per_day_last_week(self.current_user_id),
            'total_impact': self.impact_manager.calculate_total_impact(self.current_user_id),
            'weekly_impact': self.impact_manager.get_weekly_impact(self.current_user_id)
        }

    def reset_all_data(self) -> bool:
        if self.current_user_id is None:
            print("Error: No user logged in to reset data.")
            return False
        try:
            actions = self.db.read_csv_safe(self.db.actions_file)
            actions = [action for action in actions if action['user_id'] != self.current_user_id]
            self.db.write_csv_safe(self.db.actions_file, actions, 
                                 ['id', 'user_id', 'action', 'points', 'timestamp'])
            
            challenges = self.db.read_csv_safe(self.db.challenges_file)
            for i, challenge in enumerate(challenges):
                if challenge['user_id'] == self.current_user_id:
                    challenges[i]['current_count'] = 0
                    challenges[i]['completed'] = False
                    challenges[i]['completed_date'] = ''
            
            self.db.write_csv_safe(self.db.challenges_file, challenges,
                                 ['id', 'user_id', 'name', 'description', 'target_count', 
                                  'current_count', 'completed', 'created_date', 'completed_date'])
            
            streak_data = self.db.read_csv_safe(self.db.streak_file)
            for i, streak in enumerate(streak_data):
                if streak['user_id'] == self.current_user_id:
                    streak_data[i]['current_streak'] = 0
                    streak_data[i]['last_action_date'] = ''
            
            self.db.write_csv_safe(self.db.streak_file, streak_data,
                                 ['id', 'user_id', 'current_streak', 'longest_streak', 'last_action_date'])
            
            return True
        except Exception as ex:
            print(f"❌ CSV error: {ex}")
            return False

def init_db():
    tracker = EcoTracker()
    return tracker

def insert_action(user_id, action, points):
    tracker = EcoTracker()
    tracker.set_current_user(user_id)
    tracker.log_action(action, points)

def get_total_points(user_id):
    tracker = EcoTracker()
    tracker.set_current_user(user_id)
    return tracker.points_manager.get_total_points(user_id)

def get_weekly_points(user_id):
    tracker = EcoTracker()
    tracker.set_current_user(user_id)
    return tracker.points_manager.get_weekly_points(user_id)

def get_challenges(user_id):
    tracker = EcoTracker()
    tracker.set_current_user(user_id)
    return tracker.challenge_manager.get_challenges(user_id)

def get_streak_data(user_id):
    tracker = EcoTracker()
    tracker.set_current_user(user_id)
    return tracker.streak_manager.get_streak_data(user_id)

def get_action_history(user_id):
    tracker = EcoTracker()
    tracker.set_current_user(user_id)
    return tracker.action_manager.get_action_history(user_id)

def reset_all_data(user_id):
    tracker = EcoTracker()
    tracker.set_current_user(user_id)
    return tracker.reset_all_data()

def get_points_per_day_last_week(user_id):
    tracker = EcoTracker()
    tracker.set_current_user(user_id)
    return tracker.points_manager.get_points_per_day_last_week(user_id)

if __name__ == "__main__":
    tracker = EcoTracker()
    
    user = tracker.user_manager.create_user("testuser", "password123")
    if user:
        tracker.set_current_user(user.id)
        tracker.log_action("Recycle", 10)
        tracker.log_action("Bike", 15)
        
        stats = tracker.get_stats()
        print("📊 Your Eco Stats:")
        print(f"Total Points: {stats['total_points']}")
        print(f"Current Streak: {stats['streak_data'][0]} days")
        print(f"Total Actions: {stats['total_actions']}")
    else:
        print("Failed to create or authenticate user.")
