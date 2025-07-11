import flet as ft
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

from db import (
    init_db,
    insert_action,
    get_total_points,
    get_weekly_points,
    get_action_history,
    reset_all_data,
    get_points_per_day_last_week
)

POINTS = {
    "Recycle": 10,
    "Bike": 20,
    "Walk": 15,
    "Public Transport": 15,
    "Plant Seed": 30,
    "Pick Up Trash": 5
}

WEEKLY_CAP = 1000
ACHIEVEMENT_MILESTONES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

def generate_weekly_chart():
    data = get_points_per_day_last_week()
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

def main(page: ft.Page):
    page.title = "Round-2-Eco – Sprint 2"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = ft.ScrollMode.AUTO

    achievements_earned = set()
    reset_stage = {"confirming": False}

    achievements_texts = ft.Column([]) 

    total_points_text = ft.Text(f"Total Points: {get_total_points()}", size=18, weight="bold", color="green")

    action_dropdown = ft.Dropdown(
        label="Choose Eco-Action",
        hint_text="-- Select Eco-Action --",
        options=[ft.dropdown.Option(name) for name in POINTS.keys()],
        width=300
    )

    history_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Action")),
            ft.DataColumn(ft.Text("Points")),
            ft.DataColumn(ft.Text("Date Logged")),
        ],
        rows=[]
    )

    def refresh_history():
        history_table.rows.clear()
        for action, points, timestamp in get_action_history():
            history_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(action)),
                    ft.DataCell(ft.Text(str(points))),
                    ft.DataCell(ft.Text(timestamp)),
                ])
            )
        total_points_text.value = f"Total Points: {get_total_points()}"
        page.update()

    chart_src = generate_weekly_chart()
    chart_image = ft.Image(
        src_base64=chart_src.split(",")[1] if chart_src else "",
        width=500,
        height=300
    )

    def log_action(e):
        selected = action_dropdown.value
        if not selected:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Please select an action before logging."))
            page.snack_bar.open = True
            page.update()
            return

        points = POINTS[selected]
        weekly_total = get_weekly_points()

        if weekly_total + points > WEEKLY_CAP:
            page.snack_bar = ft.SnackBar(ft.Text("🚫 Weekly point cap (1000 pts) reached!"))
            page.snack_bar.open = True
            page.update()
            return

        insert_action(selected, points)
        new_total = get_total_points()
        refresh_history()

        page.snack_bar = ft.SnackBar(ft.Text(f"✅ Logged '{selected}' for {points} points!"))
        page.snack_bar.open = True
        page.update()

        for milestone in ACHIEVEMENT_MILESTONES:
            if new_total - points < milestone <= new_total and milestone not in achievements_earned:
                achievements_earned.add(milestone)

                if milestone < 400:
                    emoji = "🥉"
                elif milestone < 800:
                    emoji = "🥈"
                else:
                    emoji = "🥇"

                achievements_texts.controls.append(
                    ft.Text(f"{emoji} {milestone} Points Achievement", size=16, color=ft.Colors.ORANGE)
                )
                page.update()
                break

    
        new_src = generate_weekly_chart()
        if new_src:
            chart_image.src_base64 = new_src.split(",")[1]
            page.update()

    def reset_points(e):
        if not reset_stage["confirming"]:
            reset_button.text = "❗ Click again to confirm reset"
            reset_stage["confirming"] = True
            page.update()
            return

        if reset_all_data():
            history_table.rows.clear()
            total_points_text.value = f"Total Points: {get_total_points()}"
            achievements_earned.clear()
            achievements_texts.controls.clear()
            page.snack_bar = ft.SnackBar(ft.Text("✅ All points have been reset to 0."))
        else:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Error resetting points."))

        reset_button.text = "🔄 Reset Points"
        reset_stage["confirming"] = False
        page.snack_bar.open = True

        new_src = generate_weekly_chart()
        if new_src:
            chart_image.src_base64 = new_src.split(",")[1]
        page.update()

    log_button = ft.ElevatedButton("Log Action", on_click=log_action)
    global reset_button
    reset_button = ft.OutlinedButton("🔄 Reset Points", on_click=reset_points, icon="restart_alt")

    left_scrollable_column = ft.Container(
        content=ft.Column([
            ft.Text("🌱 Round-2-Eco Tracker", size=24, weight="bold"),
            action_dropdown,
            log_button,
            total_points_text,
            ft.Divider(),
            ft.Text("📝 Action History", size=20, weight="bold"),
            history_table,
            ft.Divider(),
            reset_button
        ], spacing=10, scroll=ft.ScrollMode.ALWAYS),
        height=600,
        expand=True,
        padding=10
    )


    achievements_column = ft.Column([
        ft.Text("🏆 Achievements", size=18, weight="bold"),
        achievements_texts,
        ft.Divider(),
        ft.Text("📊 Weekly Stats", size=18, weight="bold"),
        chart_image
    ], spacing=10)

    page.add(
        ft.Row([
            left_scrollable_column,
            ft.VerticalDivider(width=1),
            achievements_column
        ])
    )

    def on_load(_):
        refresh_history()

        total_now = get_total_points()
        for milestone in ACHIEVEMENT_MILESTONES:
            if total_now >= milestone:
                achievements_earned.add(milestone)
                if milestone < 400:
                    emoji = "🥉"
                elif milestone < 800:
                    emoji = "🥈"
                else:
                    emoji = "🥇"
                achievements_texts.controls.append(
                    ft.Text(f"{emoji} {milestone} Points Achievement", size=16, color=ft.Colors.ORANGE)
                )

        new_src = generate_weekly_chart()
        if new_src:
            chart_image.src_base64 = new_src.split(",")[1]
        page.update()

    page.on_load = on_load

if __name__ == "__main__":
    init_db()
    ft.app(target=main, view=ft.AppView.FLET_APP)
