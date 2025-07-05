import flet as ft

def main(page: ft.Page):
    page.title = "Round-2-Eco"
    page.vertical_alignment = ft.MainAxisAlignment.START

    def log_action(e):
        page.dialog = ft.AlertDialog(title=ft.Text(f"Logged action: {action_input.value}"))
        page.dialog.open = True
        page.update()

    action_input = ft.TextField(label="Enter eco-action (e.g., recycled, biked)")
    log_button = ft.ElevatedButton("Log Action", on_click=log_action)

    page.add(action_input, log_button)

ft.app(target=main, view=ft.AppView.WEB_BROWSER)