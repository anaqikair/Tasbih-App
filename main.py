import flet as ft
from datetime import datetime, date, timedelta
import json
import os
import threading
import time
import random
from plyer import notification
import winsound

DATA_FILE = "user_data.json"

# Emerald & Gold Theme
BG_COLOR = "#061a14" # Deep Emerald
PRIMARY_COLOR = "#d4af37" # Rich Gold
SECONDARY_COLOR = "#0a2b21" # Slightly lighter emerald for cards
TEXT_COLOR = "#f1f5f9"
TEXT_MUTED = "#94a3b8"

REMINDER_MESSAGES = [
    "Take a moment for Zikir.",
    "Time to remember Allah.",
    "A few minutes of Selawat brings immense blessings.",
    "Pause and remember your Creator.",
    "Refresh your heart with Istighfar."
]

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def play_bell():
    # Plays a pleasant Windows system sound
    try:
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
    except:
        pass

def main(page: ft.Page):
    page.title = "Tasbih - Remember Allah"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 400
    page.window.height = 800
    page.window.always_on_top = True
    page.bgcolor = BG_COLOR
    
    page.fonts = {"Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap"}
    page.theme = ft.Theme(font_family="Inter")

    today_str = date.today().isoformat()
    user_data = load_data()
    
    # Defaults
    if "today_date" not in user_data:
        user_data.update({
            "today_date": today_str,
            "today_count": 0,
            "today_time_seconds": 0,
            "total_count": 0,
            "streak_count": 0,
            "last_streak_date": "",
            "daily_goal_count": 100,
            "daily_goal_mins": 5,
            "enable_notifications": True,
            "notification_interval_mins": 60,
            "history": {}
        })
        save_data(user_data)
        
    # Handle new day logic
    if user_data.get("today_date") != today_str:
        old_date = user_data["today_date"]
        user_data["history"][old_date] = user_data.get("today_count", 0)
        user_data["today_count"] = 0
        user_data["today_time_seconds"] = 0
        user_data["today_date"] = today_str
        
        last_streak = user_data.get("last_streak_date")
        if last_streak:
            delta = date.today() - date.fromisoformat(last_streak)
            if delta.days > 1:
                user_data["streak_count"] = 0
        save_data(user_data)

    today_count = user_data.get("today_count", 0)
    today_time_seconds = user_data.get("today_time_seconds", 0)
    total_count = user_data.get("total_count", 0)
    streak_count = user_data.get("streak_count", 0)
    DAILY_GOAL_COUNT = user_data.get("daily_goal_count", 100)
    DAILY_GOAL_MINS = user_data.get("daily_goal_mins", 5)
    
    last_click_time = 0
    
    # ---------------- UI COMPONENTS (HOME) ----------------
    streak_text = ft.Text(f"🔥 {streak_count}", size=24, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR)
    total_text = ft.Text(f"Total: {total_count}", size=14, color=TEXT_MUTED)
    
    progress_ring = ft.ProgressRing(
        value=min(today_count / DAILY_GOAL_COUNT, 1.0) if DAILY_GOAL_COUNT > 0 else 1.0,
        stroke_width=15,
        width=250,
        height=250,
        color=PRIMARY_COLOR,
        bgcolor=SECONDARY_COLOR
    )
    
    count_display = ft.Text(str(today_count), size=64, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
    goal_display = ft.Text(f"Goal: {DAILY_GOAL_COUNT}", size=16, color=TEXT_MUTED, weight=ft.FontWeight.W_600)
    
    time_display = ft.Text(f"Time: {today_time_seconds // 60}m {today_time_seconds % 60}s / {DAILY_GOAL_MINS}m", size=14, color=PRIMARY_COLOR)

    def check_goals():
        nonlocal streak_count
        reached_count = (today_count == DAILY_GOAL_COUNT)
        
        if reached_count:
            play_bell()
            last_streak = user_data.get("last_streak_date")
            if last_streak != today_str: 
                streak_count += 1
                user_data["streak_count"] = streak_count
                user_data["last_streak_date"] = today_str
                streak_text.value = f"🔥 {streak_count}"
                
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("🎉 Daily Count Goal Reached! Streak +1", color=BG_COLOR, weight=ft.FontWeight.BOLD),
                    bgcolor=PRIMARY_COLOR, duration=4000
                )
                page.snack_bar.open = True
                
    def on_tap(e):
        nonlocal today_count, total_count, last_click_time
        today_count += 1
        total_count += 1
        last_click_time = time.time()
        
        user_data["history"][today_str] = today_count
        user_data["today_count"] = today_count
        user_data["total_count"] = total_count
        
        check_goals()
        update_home_ui()
        save_data(user_data)
        
    def reduce_count(e):
        nonlocal today_count, total_count
        if today_count > 0:
            today_count -= 1
            total_count -= 1
            user_data["today_count"] = today_count
            user_data["total_count"] = total_count
            update_home_ui()
            save_data(user_data)

    def reset_count(e):
        nonlocal today_count
        today_count = 0
        user_data["today_count"] = today_count
        update_home_ui()
        save_data(user_data)

    def update_home_ui():
        count_display.value = str(today_count)
        progress_ring.value = min(today_count / DAILY_GOAL_COUNT, 1.0) if DAILY_GOAL_COUNT > 0 else 1.0
        total_text.value = f"Total: {total_count}"
        time_display.value = f"Time: {today_time_seconds // 60}m {today_time_seconds % 60}s / {DAILY_GOAL_MINS}m"
        page.update()

    tap_button = ft.Container(
        content=ft.Stack(
            controls=[
                progress_ring,
                ft.Container(content=count_display, alignment=ft.Alignment.CENTER, width=250, height=250)
            ]
        ),
        on_click=on_tap,
        border_radius=125, 
        ink=True, 
    )

    action_row = ft.Row(
        controls=[
            ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color=TEXT_MUTED, icon_size=32, on_click=reduce_count, tooltip="Reduce Count (-1)"),
            ft.Container(width=40),
            ft.IconButton(icon=ft.Icons.REFRESH_ROUNDED, icon_color=TEXT_MUTED, icon_size=32, on_click=reset_count, tooltip="Reset Today (0)"),
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    home_view = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(height=20),
                tap_button,
                ft.Container(height=10),
                action_row,
                ft.Container(height=20),
                goal_display,
                time_display,
                ft.Container(height=5),
                total_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
    )

    # ---------------- UI COMPONENTS (GENERAL TIMER) ----------------
    general_timer_running = False
    general_timer_seconds = 300 # 5 mins default
    general_timer_left = 300
    
    timer_text = ft.Text("05:00", size=64, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR)
    
    def toggle_general_timer(e):
        nonlocal general_timer_running
        if general_timer_left <= 0:
            return
        general_timer_running = not general_timer_running
        timer_btn.text = "Pause" if general_timer_running else "Start"
        timer_btn.icon = ft.Icons.PAUSE if general_timer_running else ft.Icons.PLAY_ARROW
        page.update()

    def reset_general_timer(e):
        nonlocal general_timer_running, general_timer_left
        general_timer_running = False
        general_timer_left = general_timer_seconds
        timer_text.value = f"{general_timer_left // 60:02d}:{general_timer_left % 60:02d}"
        timer_btn.text = "Start"
        timer_btn.icon = ft.Icons.PLAY_ARROW
        page.update()
        
    def set_timer_duration(mins):
        nonlocal general_timer_seconds, general_timer_left, general_timer_running
        general_timer_running = False
        general_timer_seconds = mins * 60
        general_timer_left = general_timer_seconds
        timer_text.value = f"{general_timer_left // 60:02d}:{general_timer_left % 60:02d}"
        timer_btn.text = "Start"
        timer_btn.icon = ft.Icons.PLAY_ARROW
        page.update()

    timer_btn = ft.ElevatedButton("Start", icon=ft.Icons.PLAY_ARROW, on_click=toggle_general_timer, bgcolor=PRIMARY_COLOR, color=BG_COLOR)
    reset_timer_btn = ft.IconButton(icon=ft.Icons.REFRESH, on_click=reset_general_timer, icon_color=TEXT_MUTED)
    
    timer_view = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Dedicated Session", size=24, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Text("Set a timer and focus completely.", size=14, color=TEXT_MUTED),
                ft.Container(height=40),
                timer_text,
                ft.Container(height=20),
                ft.Row([timer_btn, reset_timer_btn], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=40),
                ft.Row(
                    controls=[
                        ft.ElevatedButton("3 Min", on_click=lambda e: set_timer_duration(3), bgcolor=SECONDARY_COLOR, color=TEXT_COLOR),
                        ft.ElevatedButton("5 Min", on_click=lambda e: set_timer_duration(5), bgcolor=SECONDARY_COLOR, color=TEXT_COLOR),
                        ft.ElevatedButton("10 Min", on_click=lambda e: set_timer_duration(10), bgcolor=SECONDARY_COLOR, color=TEXT_COLOR),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
        visible=False,
        expand=True,
    )

    # ---------------- UI COMPONENTS (STATS & SETTINGS) ----------------
    def generate_chart():
        bars = []
        history_vals = [user_data["history"].get((date.today() - timedelta(days=i)).isoformat(), 0) for i in range(7)]
        max_val = max(history_vals + [DAILY_GOAL_COUNT])
        if max_val == 0: max_val = 1
            
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            d_str = d.isoformat()
            val = user_data["history"].get(d_str, 0)
            if d_str == today_str: val = today_count
            
            bar_color = PRIMARY_COLOR if val >= DAILY_GOAL_COUNT else SECONDARY_COLOR
            bar_height = (val / max_val) * 120
            
            bars.append(ft.Column(
                controls=[
                    ft.Text(str(val), size=10, color=TEXT_MUTED),
                    ft.Container(width=25, height=max(4, bar_height), bgcolor=bar_color, border_radius=4),
                    ft.Text(d.strftime("%a")[0], size=12, color=TEXT_COLOR)
                ],
                alignment=ft.MainAxisAlignment.END,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ))
            
        return ft.Container(
            content=ft.Row(controls=bars, alignment=ft.MainAxisAlignment.SPACE_EVENLY, vertical_alignment=ft.CrossAxisAlignment.END, height=160),
            padding=ft.Padding.only(top=10, bottom=10)
        )

    chart_container = ft.Container(content=generate_chart(), height=180, padding=10)
    
    def on_settings_change(e):
        nonlocal DAILY_GOAL_COUNT, DAILY_GOAL_MINS
        try:
            user_data["daily_goal_count"] = int(goal_count_input.value)
            user_data["daily_goal_mins"] = int(goal_time_input.value)
            user_data["notification_interval_mins"] = int(notif_interval_input.value)
            user_data["enable_notifications"] = notif_switch.value
            
            DAILY_GOAL_COUNT = user_data["daily_goal_count"]
            DAILY_GOAL_MINS = user_data["daily_goal_mins"]
            
            save_data(user_data)
            goal_display.value = f"Goal: {DAILY_GOAL_COUNT}"
            update_home_ui()
            chart_container.content = generate_chart()
            
            page.snack_bar = ft.SnackBar(ft.Text("Settings Saved!", color=BG_COLOR), bgcolor=PRIMARY_COLOR, duration=2000)
            page.snack_bar.open = True
            page.update()
        except ValueError:
            pass

    goal_count_input = ft.TextField(label="Count Goal", value=str(DAILY_GOAL_COUNT), width=120)
    goal_time_input = ft.TextField(label="Time Goal (m)", value=str(DAILY_GOAL_MINS), width=120)
    notif_interval_input = ft.TextField(label="Notif Mins", value=str(user_data.get("notification_interval_mins", 60)), width=120)
    notif_switch = ft.Switch(label="Reminders", value=user_data.get("enable_notifications", True), active_color=PRIMARY_COLOR)

    settings_btn = ft.ElevatedButton("Save Settings", on_click=on_settings_change, bgcolor=PRIMARY_COLOR, color=BG_COLOR)

    stats_view = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Progress", size=20, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                chart_container,
                ft.Divider(color=ft.Colors.WHITE12, height=20),
                ft.Text("Settings", size=20, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                ft.Row([goal_count_input, goal_time_input], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([notif_interval_input, notif_switch], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                settings_btn
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        visible=False,
        expand=True,
    )

    # ---------------- NAVIGATION ----------------
    def on_nav_change(e):
        home_view.visible = e.control.selected_index == 0
        timer_view.visible = e.control.selected_index == 1
        stats_view.visible = e.control.selected_index == 2
        if stats_view.visible:
            chart_container.content = generate_chart()
        page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Tasbih"),
            ft.NavigationBarDestination(icon=ft.Icons.TIMER_OUTLINED, selected_icon=ft.Icons.TIMER, label="Timer"),
            ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART_OUTLINED, selected_icon=ft.Icons.BAR_CHART, label="Stats"),
        ],
        on_change=on_nav_change,
        bgcolor=SECONDARY_COLOR,
        selected_index=0
    )

    # ---------------- BACKGROUND LOOP (Timers & Notifications) ----------------
    def background_loop():
        nonlocal today_time_seconds, general_timer_left, general_timer_running
        last_notif_time = time.time()
        time_goal_reached_today = False
        
        while True:
            time.sleep(1)
            current_time = time.time()
            needs_update = False
            
            # 1. Background Tasbih Timer (Active if clicked in last 30s)
            if current_time - last_click_time <= 30 and last_click_time > 0:
                today_time_seconds += 1
                user_data["today_time_seconds"] = today_time_seconds
                
                # Check Time Goal
                if today_time_seconds == DAILY_GOAL_MINS * 60 and not time_goal_reached_today:
                    time_goal_reached_today = True
                    play_bell()
                    page.snack_bar = ft.SnackBar(ft.Text("🎉 Time Goal Reached!", color=BG_COLOR, weight=ft.FontWeight.BOLD), bgcolor=PRIMARY_COLOR)
                    page.snack_bar.open = True
                    needs_update = True
                    
                if home_view.visible:
                    time_display.value = f"Time: {today_time_seconds // 60}m {today_time_seconds % 60}s / {DAILY_GOAL_MINS}m"
                    needs_update = True
            
            # 2. General Session Timer
            if general_timer_running and general_timer_left > 0:
                general_timer_left -= 1
                if timer_view.visible:
                    timer_text.value = f"{general_timer_left // 60:02d}:{general_timer_left % 60:02d}"
                    needs_update = True
                
                if general_timer_left == 0:
                    general_timer_running = False
                    play_bell()
                    if timer_view.visible:
                        timer_btn.text = "Done"
                        timer_btn.icon = ft.Icons.CHECK
                        needs_update = True
                    page.snack_bar = ft.SnackBar(ft.Text("Session Complete!", color=BG_COLOR, weight=ft.FontWeight.BOLD), bgcolor=PRIMARY_COLOR)
                    page.snack_bar.open = True
                    needs_update = True

            # 3. Notifications
            if user_data.get("enable_notifications", True):
                notif_interval_sec = user_data.get("notification_interval_mins", 60) * 60
                if current_time - last_notif_time >= notif_interval_sec:
                    # Check if goals are reached (if so, stop bothering)
                    if today_count < DAILY_GOAL_COUNT and today_time_seconds < DAILY_GOAL_MINS * 60:
                        try:
                            notification.notify(
                                title="Tasbih",
                                message=random.choice(REMINDER_MESSAGES),
                                app_name="Tasbih",
                                timeout=5
                            )
                        except Exception as ex:
                            pass
                    last_notif_time = current_time

            if needs_update:
                try:
                    page.update()
                except:
                    pass

    # Start background thread
    threading.Thread(target=background_loop, daemon=True).start()

    # --- Main Layout Assembly ---
    page.add(
        ft.SafeArea(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text("Tasbih", size=28, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                                streak_text,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=ft.Padding.only(left=20, right=20, top=15, bottom=5)
                    ),
                    ft.Divider(color=ft.Colors.WHITE12, height=1),
                    home_view,
                    timer_view,
                    stats_view
                ],
            ),
            expand=True
        )
    )

ft.run(main)
