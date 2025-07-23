import flet as ft
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, Set, Any, Optional, List
from dataclasses import dataclass
from db import EcoTracker, User

class AppConfig:
    def __init__(self):
        self.POINTS = {
            "Recycle": 10, "Bike": 20, "Walk": 15, "Public Transport": 15,
            "Plant Seed": 30, "Pick Up Trash": 5
        }
        self.WEEKLY_CAP = 1000
        self.ACHIEVEMENT_MILESTONES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        self.THEME_COLORS = {
            "primary": "#4CAF50", "secondary": "#2E7D32", "background": "#F1F8E9",
            "surface": "#FFFFFF", "accent": "#FF9800"
        }

class ChartGenerator:
    def __init__(self, config: AppConfig):
        self.config = config
    
    def generate_weekly_chart(self, data: List[tuple]) -> str:
        if not data:
            return ""

        days, points = zip(*data)
        
        plt.style.use('seaborn-v0_8')
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(days, points, color=self.config.THEME_COLORS["primary"], 
                     alpha=0.8, edgecolor=self.config.THEME_COLORS["secondary"], linewidth=1.2)
        
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{int(height)}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_title("Eco Points - Last 7 Days", fontsize=14, fontweight='bold', 
                    color=self.config.THEME_COLORS["secondary"])
        ax.set_ylabel("Points", fontweight='bold')
        ax.set_xlabel("Date", fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, fontsize=8)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches='tight')
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        plt.close()
        return f"data:image/png;base64,{encoded}"

class AchievementSystem:
    def __init__(self, config: AppConfig):
        self.config = config
        self.earned_achievements: Set[int] = set()
    
    def get_achievement_emoji(self, milestone: int) -> str:
        return "🥉" if milestone < 400 else "🥈" if milestone < 800 else "🥇"
    
    def check_new_achievements(self, old_points: int, new_points: int) -> List[int]:
        new_achievements = []
        for milestone in self.config.ACHIEVEMENT_MILESTONES:
            if old_points < milestone <= new_points and milestone not in self.earned_achievements:
                self.earned_achievements.add(milestone)
                new_achievements.append(milestone)
        return new_achievements
    
    def load_existing_achievements(self, total_points: int) -> None:
        for milestone in self.config.ACHIEVEMENT_MILESTONES:
            if total_points >= milestone:
                self.earned_achievements.add(milestone)
    
    def create_achievement_widget(self, milestone: int) -> ft.Container:
        emoji = self.get_achievement_emoji(milestone)
        return ft.Container(
            content=ft.Text(f"{emoji} {milestone} Points Achievement!", size=14, 
                          color=ft.Colors.WHITE, weight="bold"),
            bgcolor=ft.Colors.ORANGE, padding=10, border_radius=5,
            margin=ft.margin.only(bottom=5)
        )
    
    def reset_achievements(self) -> None:
        self.earned_achievements.clear()

class UIComponentFactory:
    def __init__(self, config: AppConfig):
        self.config = config
    
    def create_action_dropdown(self) -> ft.Dropdown:
        return ft.Dropdown(
            label="🌍 Choose Your Eco-Action",
            hint_text="Select an eco-friendly action...",
            options=[ft.dropdown.Option(key=name, text=f"{name} (+{points} pts)") 
                    for name, points in self.config.POINTS.items()],
            width=350, bgcolor=ft.Colors.WHITE, border_color=ft.Colors.GREEN,
            focused_border_color=ft.Colors.GREEN_800
        )
    
    def create_streak_card(self) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon("local_fire_department", color=ft.Colors.ORANGE, size=30),
                        ft.Text("Streak System", size=18, weight="bold", color=ft.Colors.ORANGE)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Text("Current: 0 days", size=14, text_align=ft.TextAlign.CENTER),
                    ft.Text("Best: 0 days", size=12, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER)
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15
            ), elevation=3, color="#FFF3E0"
        )
    
    def create_history_table(self) -> ft.DataTable:
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("🎯 Action", weight="bold")),
                ft.DataColumn(ft.Text("⭐ Points", weight="bold")),
                ft.DataColumn(ft.Text("📅 Date", weight="bold")),
            ], rows=[], bgcolor=ft.Colors.WHITE, border_radius=10,
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300)
        )
    
    def create_log_button(self, on_click_handler) -> ft.ElevatedButton:
        return ft.ElevatedButton(
            "🚀 Log Action", on_click=on_click_handler, bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE, height=50, width=200,
            style=ft.ButtonStyle(text_style=ft.TextStyle(size=16, weight="bold"))
        )
    
    def create_reset_button(self, on_click_handler) -> ft.OutlinedButton:
        return ft.OutlinedButton(
            "🔄 Reset All Data", on_click=on_click_handler, icon="restart_alt", height=40
        )
    
    def create_impact_card(self) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Environmental Impact", size=18, weight="bold", color=ft.Colors.GREEN)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Text("This Week:", size=14, weight="bold", color=ft.Colors.GREY_800),
                    ft.Text("🌍 CO2 Saved: 0.0 kg", size=12, text_align=ft.TextAlign.CENTER),
                    ft.Text("⛽ Gas Saved: 0.0 gallons", size=12, text_align=ft.TextAlign.CENTER),
                    ft.Text("🌳 Trees Equivalent: 0", size=12, text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=1),
                    ft.Text("All Time:", size=12, weight="bold", color=ft.Colors.BLUE_GREY_700),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=15
            ), elevation=3, color="#F1F1F1"
        )

class UIDataManager:
    def __init__(self, tracker: EcoTracker, config: AppConfig):
        self.tracker = tracker
        self.config = config
        self.emoji_map = {
            "Recycle": "♻️", "Bike": "🚲", "Walk": "🚶", 
            "Public Transport": "🚌", "Plant Seed": "🌱", "Pick Up Trash": "🗑️"
        }
    
    def get_action_emoji(self, action: str) -> str:
        return self.emoji_map.get(action, "🌍")
    
    def create_history_row(self, action: str, points: int, timestamp: str) -> ft.DataRow:
        action_emoji = self.get_action_emoji(action)
        return ft.DataRow(cells=[
            ft.DataCell(ft.Text(f"{action_emoji} {action}")),
            ft.DataCell(ft.Text(f"+{points}", color=ft.Colors.GREEN, weight="bold")),
            ft.DataCell(ft.Text(timestamp.split()[0], size=12)),
        ])
    
    def create_challenge_card(self, name: str, description: str, current: int, 
                            target: int, completed: bool) -> ft.Card:
        progress = min(current / target, 1.0) if target > 0 else 0
        card_color = "#E8F5E8" if completed else "#FFFFFF"
        progress_color = ft.Colors.GREEN if completed else ft.Colors.BLUE
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon("emoji_events" if completed else "flag", 
                               color=ft.Colors.GREEN if completed else ft.Colors.BLUE, size=20),
                        ft.Text(name, size=14, weight="bold", 
                               color=ft.Colors.GREEN if completed else ft.Colors.BLACK)
                    ]),
                    ft.Text(description, size=12, color=ft.Colors.GREY_700),
                    ft.ProgressBar(value=progress, color=progress_color, height=8),
                    ft.Text(f"{current}/{target} {'✅ Complete!' if completed else 'actions'}", 
                           size=11, color=ft.Colors.GREEN if completed else ft.Colors.GREY_600)
                ], spacing=5), padding=10
            ), elevation=2, color=card_color
        )

class EcoTrackerApp:
    def __init__(self):
        self.config = AppConfig()
        self.tracker = EcoTracker()
        self.chart_generator = ChartGenerator(self.config)
        self.achievement_system = AchievementSystem(self.config)
        self.ui_factory = UIComponentFactory(self.config)
        self.data_manager = UIDataManager(self.tracker, self.config)
        
        self.reset_stage = {"confirming": False}
        self.current_user: Optional[User] = None 
        self.page = None

        self.action_dropdown = None
        self.streak_card = None
        self.history_table = None
        self.log_button = None
        self.reset_button = None
        self.impact_card = None
        self.total_points_text = None
        self.achievements_column = None
        self.challenges_column = None
        self.chart_image = None

        self.username_field = ft.TextField(label="Username", width=300)
        self.password_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
        self.login_button = ft.ElevatedButton("Login", on_click=self._login, width=300)
        self.register_button = ft.OutlinedButton("Register", on_click=self._register, width=300)
        self.main_content_container = ft.Container(expand=True)

    def _init_main_app_ui_components(self):
        self.action_dropdown = self.ui_factory.create_action_dropdown()
        self.streak_card = self.ui_factory.create_streak_card()
        self.history_table = self.ui_factory.create_history_table()
        self.log_button = self.ui_factory.create_log_button(self._log_action)
        self.reset_button = self.ui_factory.create_reset_button(self._reset_points)
        self.impact_card = self.ui_factory.create_impact_card()
        self.total_points_text = ft.Text("Total Points: 0", size=20, weight="bold", color=ft.Colors.GREEN)
        self.achievements_column = ft.Column([])
        self.challenges_column = ft.Column([], spacing=10)
        self.chart_image = ft.Image(src_base64="", width=500, height=300, border_radius=10)

    def _update_streak_display(self):
        if not self.current_user: return
        current_streak, longest_streak = self.tracker.streak_manager.get_streak_data(self.current_user.id)
        self.streak_card.content.content.controls[1].value = f"Current: {current_streak} days"
        self.streak_card.content.content.controls[2].value = f"Best: {longest_streak} days"

    def _update_challenges_display(self):
        if not self.current_user: return
        self.challenges_column.controls.clear()
        challenges = self.tracker.challenge_manager.get_challenges(self.current_user.id)
        
        for name, description, current, target, completed in challenges:
            card = self.data_manager.create_challenge_card(name, description, current, target, completed)
            self.challenges_column.controls.append(card)

    def _update_history_display(self):
        if not self.current_user: return
        self.history_table.rows.clear()
        history = self.tracker.action_manager.get_action_history(self.current_user.id)
        
        for action, points, timestamp in history[:10]:
            row = self.data_manager.create_history_row(action, points, timestamp)
            self.history_table.rows.append(row)

    def _update_impact_display(self):
        if not self.current_user: return
        stats = self.tracker.get_stats()
        weekly_impact = stats['weekly_impact']
        total_impact = stats['total_impact']
        
        impact_controls = self.impact_card.content.content.controls
        impact_controls[2].value = f"🌍 CO2 Saved: {weekly_impact.co2_saved_kg:.1f} kg"
        impact_controls[3].value = f"⛽ Gas Saved: {weekly_impact.gas_saved_gallons:.1f} gallons"
        impact_controls[4].value = f"🌳 Trees Equivalent: {weekly_impact.trees_equivalent}"
        impact_controls[6].value = f"Total Impact: {total_impact.co2_saved_kg:.1f} kg CO2"

    def _refresh_all_displays(self):
        if not self.current_user: return
        if not self.action_dropdown: 
            self._init_main_app_ui_components()

        self._update_history_display()
        self.total_points_text.value = f"Total Points: {self.tracker.points_manager.get_total_points(self.current_user.id)}"
        self._update_streak_display()
        self._update_challenges_display()
        self._update_impact_display()
        
        chart_data = self.tracker.points_manager.get_points_per_day_last_week(self.current_user.id)
        new_chart_src = self.chart_generator.generate_weekly_chart(chart_data)
        if new_chart_src:
            self.chart_image.src_base64 = new_chart_src.split(",")[1]
        
        self.main_content_container.content.update() 
        self.page.update() 

    def _show_snackbar(self, message: str, color: str):
        self.page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()

    def _log_action(self, e):
        if not self.current_user:
            self._show_snackbar("Please log in to log actions.", ft.Colors.RED_300)
            return

        selected = self.action_dropdown.value
        if not selected:
            self._show_snackbar("⚠️ Please select an action before logging.", ft.Colors.ORANGE_300)
            return

        points = self.config.POINTS[selected]
        weekly_points = self.tracker.points_manager.get_weekly_points(self.current_user.id)
        
        if weekly_points + points > self.config.WEEKLY_CAP:
            self._show_snackbar("🚫 Weekly point cap (1000 pts) reached!", ft.Colors.RED_300)
            return

        old_points = self.tracker.points_manager.get_total_points(self.current_user.id)
        
        success = self.tracker.action_manager.add_action(self.current_user.id, selected, points)
        if not success:
            self._show_snackbar("❌ Failed to log action. Please try again.", ft.Colors.RED_300)
            return

        self._refresh_all_displays()

        new_points = self.tracker.points_manager.get_total_points(self.current_user.id)
        new_achievements = self.achievement_system.check_new_achievements(old_points, new_points)
        for milestone in new_achievements:
            achievement_widget = self.achievement_system.create_achievement_widget(milestone)
            self.achievements_column.controls.append(achievement_widget)

        current_streak, _ = self.tracker.streak_manager.get_streak_data(self.current_user.id)
        streak_msg = f" 🔥 {current_streak} day streak!" if current_streak > 1 else ""
        
        self._show_snackbar(f"✅ Logged '{selected}' for {points} points!{streak_msg}", ft.Colors.GREEN_300)

    def _reset_points(self, e):
        if not self.current_user:
            self._show_snackbar("Please log in to reset data.", ft.Colors.RED_300)
            return

        if not self.reset_stage["confirming"]:
            self.reset_button.text = "❗ Click again to confirm reset"
            self.reset_stage["confirming"] = True
            self.page.update()
            return

        success = self.tracker.reset_all_data()
        if not success:
            self._show_snackbar("❌ Failed to reset data. Please try again.", ft.Colors.RED_300)
            return
        
        self.achievement_system.reset_achievements()
        self.achievements_column.controls.clear()
        self._refresh_all_displays()
            
        self._show_snackbar("✅ All data has been reset.", ft.Colors.BLUE_300)

        self.reset_button.text = "🔄 Reset All Data"
        self.reset_stage["confirming"] = False
        self.page.update()
    
    def _create_main_app_layout_content(self) -> ft.Container:
        actions_tab = ft.Tab(
            text="🎯 Actions",
            content=ft.Container(
                content=ft.Column([
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                self.action_dropdown, self.log_button, self.total_points_text, self.streak_card
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                            padding=20
                        ), elevation=5, color=ft.Colors.WHITE
                    ),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("📝 Recent Actions", size=18, weight="bold", color=ft.Colors.GREEN),
                                ft.Card(content=ft.Container(content=self.history_table, padding=10), elevation=3)
                            ], spacing=10), expand=True
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("🌍 Your Impact", size=18, weight="bold", color=ft.Colors.GREEN),
                                self.impact_card
                            ], spacing=10), width=300
                        )
                    ], spacing=20),
                    self.reset_button
                ], spacing=20), padding=20
            )
        )
        
        challenges_tab = ft.Tab(
            text="🏆 Challenges",
            content=ft.Container(
                content=ft.Column([
                    ft.Text("🎯 Active Challenges", size=20, weight="bold", color=ft.Colors.BLUE),
                    ft.Text("Complete challenges to earn special recognition!", size=14, color=ft.Colors.GREY_700),
                    self.challenges_column
                ], spacing=15), padding=20
            )
        )
        
        stats_tab = ft.Tab(
            text="📊 Stats",
            content=ft.Container(
                content=ft.Column([
                    ft.Text("🏆 Achievements gained this Session", size=18, weight="bold", color=ft.Colors.ORANGE),
                    self.achievements_column, ft.Divider(),
                    ft.Text("📊 Weekly Progress", size=18, weight="bold", color=ft.Colors.BLUE),
                    ft.Card(content=ft.Container(content=self.chart_image, padding=15), elevation=3)
                ], spacing=15), padding=20
            )
        )
        
        tab_content = ft.Tabs(
            selected_index=0, animation_duration=300,
            tabs=[actions_tab, challenges_tab, stats_tab]
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon("eco", color=ft.Colors.GREEN, size=40),
                        ft.Text("Round-2-Eco", size=28, weight="bold", color=ft.Colors.GREEN),
                        ft.Container(expand=True),
                        ft.ElevatedButton("Logout", on_click=self._logout, icon=ft.Icons.LOGOUT) 
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=ft.Colors.WHITE, padding=20, border_radius=10,
                    margin=ft.margin.only(bottom=20)
                ),
                tab_content
            ], expand=True), padding=20 
        )

    def _load_initial_data(self):
        if not self.current_user: return 
        self.tracker.set_current_user(self.current_user.id) 
        self._refresh_all_displays()
        
        total_points = self.tracker.points_manager.get_total_points(self.current_user.id)
        self.achievement_system.load_existing_achievements(total_points)
        
        self.achievements_column.controls.clear() 
        for milestone in self.achievement_system.earned_achievements:
            achievement_widget = self.achievement_system.create_achievement_widget(milestone)
            self.achievements_column.controls.append(achievement_widget)
        
        self.page.update()
    
    def run(self, page: ft.Page):
        self.page = page
        
        page.title = "Round-2-Eco"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.scroll = ft.ScrollMode.AUTO
        page.padding = 20
        page.bgcolor = self.config.THEME_COLORS["background"]
        
        self.page.add(self.main_content_container)
        
        self.main_content_container.content = ft.Container(
            content=self._create_login_view(),
            alignment=ft.alignment.center, 
            expand=True 
        )
        self.page.update()
    
    def _create_login_view(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text("Welcome to Round-2-Eco!", size=30, weight="bold", color=self.config.THEME_COLORS["primary"]),
                ft.Text("Login or Register to continue", size=16, color=ft.Colors.GREY_700),
                ft.Divider(),
                self.username_field, self.password_field,
                ft.Column([self.login_button, self.register_button], 
                         horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            alignment=ft.alignment.center, padding=30, border_radius=15,
            bgcolor=self.config.THEME_COLORS["surface"], width=400, height=480 
        )

    def _login(self, e):
        username = self.username_field.value
        password = self.password_field.value

        if not username or not password:
            self._show_snackbar("Please enter both username and password.", ft.Colors.ORANGE_300)
            return

        user = self.tracker.user_manager.authenticate_user(username, password)
        if user:
            self.current_user = user
            self._show_snackbar(f"Welcome, {self.current_user.username}!", ft.Colors.GREEN_300)
            self._show_main_app_view()
        else:
            self._show_snackbar("Invalid username or password.", ft.Colors.RED_300)

    def _register(self, e):
        username = self.username_field.value
        password = self.password_field.value
        
        if not username or not password:
            self._show_snackbar("Please enter both username and password.", ft.Colors.ORANGE_300)
            return

        user = self.tracker.user_manager.create_user(username, password)
        if user:
            self._show_snackbar("Registration successful! Please log in.", ft.Colors.BLUE_300)
            self.username_field.value = ""
            self.password_field.value = ""
            self.page.update()
        else:
            self._show_snackbar("Username already exists. Please choose another.", ft.Colors.RED_300)

    def _show_main_app_view(self):
        try:
            self._init_main_app_ui_components()
            new_content = self._create_main_app_layout_content()
            self.main_content_container.content = new_content
            self._load_initial_data() 
        except Exception as e:
            print(f"ERROR: _show_main_app_view failed: {e}")
            self._show_snackbar(f"Error loading main view: {e}", ft.Colors.RED_500)

    def _logout(self, e):
        self.current_user = None
        self.tracker.set_current_user(None) 
        self.main_content_container.content = ft.Container(
            content=self._create_login_view(),
            alignment=ft.alignment.center, expand=True 
        )
        
        self.username_field.value = "" 
        self.password_field.value = ""
        self._show_snackbar("Logged out successfully.", ft.Colors.BLUE_300)
        self.page.update()

def main(page: ft.Page):
    app = EcoTrackerApp()
    app.run(page)

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
