import flet as ft
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
from typing import Set, Dict, List, Tuple
from dataclasses import dataclass
from db import EcoDatabase
from datetime import datetime

@dataclass
class EcoAction:
    name: str
    points: int

class EcoConfig:
    ACTIONS = {
        "Recycle": EcoAction("Recycle", 10),
        "Bike": EcoAction("Bike", 20),
        "Walk": EcoAction("Walk", 15),
        "Public Transport": EcoAction("Public Transport", 15),
        "Plant Seed": EcoAction("Plant Seed", 30),
        "Pick Up Trash": EcoAction("Pick Up Trash", 5)
    }
    WEEKLY_CAP = 1000
    ACHIEVEMENT_MILESTONES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

class ChartGenerator:
    @staticmethod
    def generate_weekly_chart(data: List[Tuple[str, int]]) -> str:
        if not data:
            return ""
        days, points = zip(*data)
        fig, ax = plt.subplots()
        ax.bar(days, points, color='green')
        ax.set_title("Eco Points (Last 7 Days)")
        ax.set_ylabel("Points")
        ax.set_xlabel("Date")
        plt.xticks(rotation=45)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        plt.close()
        return f"data:image/png;base64,{encoded}"

class AchievementManager:
    def __init__(self, milestones: List[int]):
        self.milestones = milestones
        self.earned_achievements: Set[int] = set()
        self.achievements_display = ft.Column([])

    def check_new_achievements(self, previous_total: int, current_total: int) -> bool:
        new_achievement = False
        for milestone in self.milestones:
            if previous_total < milestone <= current_total and milestone not in self.earned_achievements:
                self.earned_achievements.add(milestone)
                self._display_achievement(milestone)
                new_achievement = True
                break
        return new_achievement

    def load_existing_achievements(self, total_points: int) -> None:
        for milestone in self.milestones:
            if total_points >= milestone:
                self.earned_achievements.add(milestone)
                self._display_achievement(milestone)

    def _display_achievement(self, milestone: int) -> None:
        emoji = self._get_achievement_emoji(milestone)
        achievement_text = ft.Text(f"{emoji} {milestone} Points Achievement", size=16, color=ft.Colors.ORANGE)
        self.achievements_display.controls.append(achievement_text)

    def _get_achievement_emoji(self, milestone: int) -> str:
        if milestone < 400:
            return "🥉"
        elif milestone < 800:
            return "🥈"
        else:
            return "🥇"

    def reset_achievements(self) -> None:
        self.earned_achievements.clear()
        self.achievements_display.controls.clear()

class EcoTrackerUI:
    def __init__(self):
        self.db = EcoDatabase()
        self.config = EcoConfig()
        self.chart_generator = ChartGenerator()
        self.achievement_manager = AchievementManager(self.config.ACHIEVEMENT_MILESTONES)
        self.reset_confirmation = {"confirming": False}
        self.total_points_text = None
        self.action_dropdown = None
        self.history_table = None
        self.chart_image = None
        self.log_button = None
        self.reset_button = None
        self.challenge_display = ft.Column([])
        self.page = None

    def create_components(self) -> None:
        self.total_points_text = ft.Text(f"Total Points: {self.db.get_total_points()}", size=18, weight="bold", color="green")
        self.action_dropdown = ft.Dropdown(
            label="Choose Eco-Action",
            hint_text="-- Select Eco-Action --",
            options=[ft.dropdown.Option(name) for name in self.config.ACTIONS.keys()],
            width=300
        )
        self.history_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Action")),
                ft.DataColumn(ft.Text("Points")),
                ft.DataColumn(ft.Text("Date Logged")),
            ],
            rows=[]
        )
        chart_src = self.chart_generator.generate_weekly_chart(self.db.get_points_per_day_last_week())
        self.chart_image = ft.Image(src_base64=chart_src.split(",")[1] if chart_src else "", width=500, height=300)
        self.log_button = ft.ElevatedButton("Log Action", on_click=self.log_action)
        self.reset_button = ft.OutlinedButton("🔄 Reset Points", on_click=self.reset_points, icon="restart_alt")
        self._update_challenges()

    def log_action(self, e) -> None:
        selected_action = self.action_dropdown.value
        if not selected_action:
            self._show_snackbar("⚠️ Please select an action before logging.")
            return

        eco_action = self.config.ACTIONS[selected_action]
        weekly_total = self.db.get_weekly_points()

        if weekly_total + eco_action.points > self.config.WEEKLY_CAP:
            self._show_snackbar("🚫 Weekly point cap (1000 pts) reached!")
            return

        previous_total = self.db.get_total_points()
        success = self.db.insert_action(eco_action.name, eco_action.points)
        if not success:
            self._show_snackbar("❌ Failed to log action.")
            return

        current_total = self.db.get_total_points()
        self.refresh_history()
        self._show_snackbar(f"✅ Logged '{eco_action.name}' for {eco_action.points} points!")

        if self.achievement_manager.check_new_achievements(previous_total, current_total):
            self.page.update()

        updated_challenges = self.db.update_challenge_completion()
        self._update_challenges(challenges=updated_challenges)
        self.page.update()  

        self._update_chart()

    def refresh_history(self) -> None:
        self.history_table.rows.clear()
        for action, points, timestamp in self.db.get_action_history():
            self.history_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(action)),
                    ft.DataCell(ft.Text(str(points))),
                    ft.DataCell(ft.Text(timestamp)),
                ])
            )
        self.total_points_text.value = f"Total Points: {self.db.get_total_points()}"
        self.page.update()

    def reset_points(self, e) -> None:
        if not self.reset_confirmation["confirming"]:
            self.reset_button.text = "❗ Click again to confirm reset"
            self.reset_confirmation["confirming"] = True
            self.page.update()
            return
        success = self.db.reset_all_data()
        if success:
            self.history_table.rows.clear()
            self.total_points_text.value = f"Total Points: {self.db.get_total_points()}"
            self.achievement_manager.reset_achievements()
            self._show_snackbar("✅ All points have been reset to 0.")
        else:
            self._show_snackbar("❌ Error resetting points.")
        self.reset_button.text = "🔄 Reset Points"
        self.reset_confirmation["confirming"] = False
        self._update_chart()
        self._update_challenges()
        self.page.update()

    def _update_chart(self) -> None:
        new_src = self.chart_generator.generate_weekly_chart(self.db.get_points_per_day_last_week())
        if new_src:
            self.chart_image.src_base64 = new_src.split(",")[1]

    def _update_challenges(self, challenges=None):
        self.challenge_display.controls.clear()
        if challenges is None:
            challenges = self.db.get_active_challenges()

        for cid, desc, target, start, end, completed, progress in challenges:
            progress_percentage = min(100, (progress / target) * 100) if target > 0 else 0
            progress_bar = ft.ProgressBar(
                width=300,
                color=ft.Colors.GREEN if progress >= target else ft.Colors.BLUE,
                bgcolor=ft.Colors.GREY_200,
                value=progress_percentage / 100
            )
            status_emoji = "✅" if progress >= target else "🔄"
            challenge_text = ft.Text(
                f"{status_emoji} {desc}\n📅 {start} to {end}\n🎯 Progress: {progress}/{target} actions ({progress_percentage:.1f}%)",
                size=14,
                color=ft.Colors.BLACK
            )
            challenge_container = ft.Container(
                content=ft.Column([challenge_text, progress_bar], spacing=5),
                padding=10,
                margin=5,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                bgcolor=ft.Colors.GREEN_50 if progress >= target else ft.Colors.BLUE_50
            )
            self.challenge_display.controls.append(challenge_container)

        if not challenges:
            self.challenge_display.controls.append(
                ft.Text("No active challenges", size=14, color=ft.Colors.BLACK)
            )

    def _show_snackbar(self, message: str) -> None:
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def create_layout(self) -> ft.Row:
        left_column = ft.Container(
            content=ft.Column([
                ft.Text("🌱 Round-2-Eco Tracker", size=24, weight="bold"),
                self.action_dropdown,
                self.log_button,
                self.total_points_text,
                ft.Divider(),
                ft.Text("📝 Action History", size=20, weight="bold"),
                self.history_table,
                ft.Divider(),
                self.reset_button
            ], spacing=10, scroll=ft.ScrollMode.ALWAYS),
            height=600,
            expand=True,
            padding=10
        )
        right_column = ft.Column([
            ft.Text("🏆 Achievements", size=18, weight="bold"),
            self.achievement_manager.achievements_display,
            ft.Divider(),
            ft.Text("📊 Weekly Stats", size=18, weight="bold"),
            self.chart_image,
            ft.Divider(),
            ft.Text("🎯 Monthly Challenges", size=18, weight="bold"),
            self.challenge_display
        ], spacing=10)
        return ft.Row([left_column, ft.VerticalDivider(width=1), right_column])

    def initialize_on_load(self) -> None:
        self.refresh_history()
        total_points = self.db.get_total_points()
        self.achievement_manager.load_existing_achievements(total_points)
        self._update_chart()
        self._update_challenges()
        self.page.update()

class EcoTrackerApp:
    def __init__(self):
        self.ui = EcoTrackerUI()

    def main(self, page: ft.Page) -> None:
        page.title = "Round-2-Eco – Sprint 3"
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.scroll = ft.ScrollMode.AUTO
        self.ui.page = page
        self.ui.create_components()
        page.add(self.ui.create_layout())

        def on_load(_):
            self.ui.initialize_on_load()
        page.on_load = on_load

def main():
    db = EcoDatabase()
    db.init_db()

    today = datetime.now().strftime("%Y-%m-%d")
    month_end = "2025-07-31"

    existing_challenges = db.get_active_challenges()
    if not any("Complete 20 eco actions" in challenge[1] for challenge in existing_challenges):
        db.insert_challenge("Complete 20 eco actions", 20, today, month_end)

    app = EcoTrackerApp()
    ft.app(target=app.main, view=ft.AppView.FLET_APP)

if __name__ == "__main__":
    main()
