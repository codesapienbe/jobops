from __future__ import annotations

import os
from pathlib import Path
from typing import List

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout

import threading
import pystray
from PIL import Image
import json
import tkinter as tk
from tkinter import filedialog, messagebox

from .theme import apply_jobops_theme
from .repository import Repository
from .i18n import I18N
from .screens.sections import SECTION_SPECS, build_section_screen
from .screens.settings import SettingsScreen


APP_TITLE = "JobOps App"


class JobOpsRoot(Screen):
    title = StringProperty(APP_TITLE)


class JobOpsApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config_dir = Path(os.path.expanduser("~/.jobops"))
        config_dir.mkdir(parents=True, exist_ok=True)
        self.store = JsonStore(str(config_dir / "jobops_app_settings.json"))
        self.repo = Repository(db_path=str(config_dir / "jobops_app.db"))
        self.i18n = I18N(self.store)
        self.current_job_id: str | None = None
        self._tray_icon: pystray.Icon | None = None
        self._tray_thread: threading.Thread | None = None
        self._is_hidden: bool = False
        self._loader_anim_event = None
        # Use clipper icon for window/app icon if available
        icon_path = Path(__file__).resolve().parents[2] / "jobops_clipper" / "src" / "icon.png"
        if icon_path.exists():
            try:
                self.icon = str(icon_path)
            except Exception:
                pass

    def build(self):
        try:
            Window.size = (1920, 800)
            # Center the window if possible
            try:
                # Preferred: compute center using system size
                sys_w, sys_h = Window.system_size  # type: ignore[attr-defined]
                Window.position = 'custom'
                Window.left = int((sys_w - Window.size[0]) / 2)
                Window.top = int((sys_h - Window.size[1]) / 2)
            except Exception:
                try:
                    # Some providers expose a private getter
                    sys_w, sys_h = Window._get_system_size()  # type: ignore[attr-defined]
                    Window.position = 'custom'
                    Window.left = int((sys_w - Window.size[0]) / 2)
                    Window.top = int((sys_h - Window.size[1]) / 2)
                except Exception:
                    # Fallback: ask provider to center
                    try:
                        Window.position = 'center'  # may be ignored on some platforms
                    except Exception:
                        pass
        except Exception:
            pass
        apply_jobops_theme()
        root = Builder.load_string(KV)
        # Start tray icon asynchronously
        Clock.schedule_once(lambda dt: self._start_tray(), 0)
        # Intercept window close to minimize to tray
        try:
            Window.bind(on_request_close=self._on_request_close)
        except Exception:
            pass
        return root

    def on_start(self):
        self._populate_navigation()
        self._create_section_screens()
        # Recenter after window is shown
        Clock.schedule_once(lambda dt: self._center_window(), 0)

    def on_stop(self):
        # Ensure tray is stopped
        try:
            if self._tray_icon:
                self._tray_icon.visible = False
                self._tray_icon.stop()
        except Exception:
            pass

    def _center_window(self):
        try:
            sys_w, sys_h = Window.system_size  # type: ignore[attr-defined]
        except Exception:
            try:
                sys_w, sys_h = Window._get_system_size()  # type: ignore[attr-defined]
            except Exception:
                return
        try:
            Window.position = 'custom'
            Window.left = int((sys_w - Window.size[0]) / 2)
            Window.top = int((sys_h - Window.size[1]) / 2)
        except Exception:
            try:
                Window.position = 'center'
            except Exception:
                pass

    def _populate_navigation(self):
        menu_box = self.root.ids.top_menu_box
        menu_box.clear_widgets()
        from kivy.uix.button import Button
        for spec in SECTION_SPECS:
            btn = Button(text=self.i18n.t(spec["title_key"]), size_hint_y=None, height=48, size_hint_x=None)
            btn.background_normal = ''
            btn.background_color = (0, 0, 0, 0)
            btn.color = (1, 1, 1, 0.92)
            # Give buttons a fixed width for aesthetics
            btn.width = max(140, int(0.08 * Window.width))
            btn.bind(on_release=lambda _b, s=spec: self.switch_to_section(s["name"]))
            menu_box.add_widget(btn)
        settings_btn = Button(text=self.i18n.t("settings.title"), size_hint_y=None, height=48, size_hint_x=None)
        settings_btn.background_normal = ''
        settings_btn.background_color = (0, 0, 0, 0)
        settings_btn.color = (1, 1, 1, 0.92)
        settings_btn.width = max(140, int(0.08 * Window.width))
        settings_btn.bind(on_release=lambda *_: self.open_settings_screen())
        menu_box.add_widget(settings_btn)

    def _create_section_screens(self):
        sm: ScreenManager = self.root.ids.screen_manager
        sm.clear_widgets()
        for spec in SECTION_SPECS:
            screen = build_section_screen(spec, self.repo, self.i18n)
            sm.add_widget(screen)

    def switch_to_section(self, name: str):
        self.root.ids.screen_manager.current = name
        self.root.title = next((self.i18n.t(s["title_key"]) for s in SECTION_SPECS if s["name"] == name), APP_TITLE)

    def open_settings_screen(self):
        sm: ScreenManager = self.root.ids.screen_manager
        screen_name = "settings"
        if not sm.has_screen(screen_name):
            sm.add_widget(SettingsScreen(name=screen_name, store=self.store, i18n=self.i18n))
        self.root.title = self.i18n.t("settings.title")
        sm.current = screen_name

    def generate_report(self):
        self.start_loading(self.i18n.t("app.title") + ' - Generating')
        def _do(_dt):
            job_id = self.current_job_id or self.repo.get_latest_job_id()
            if not job_id:
                self.root.title = "No job yet"
                self.stop_loading()
                return
            sections = self.repo.list_sections_for_job(job_id)
            parts = [f"# Application Summary\n"]
            order = [s["name"] for s in SECTION_SPECS if s["name"] != "application_summary"]
            for name in order:
                data = sections.get(name) or {}
                if not data:
                    continue
                pretty_name = next((self.i18n.t(s["title_key"]) for s in SECTION_SPECS if s["name"] == name), name)
                parts.append(f"\n## {pretty_name}\n")
                for k, v in data.items():
                    vtxt = v if isinstance(v, str) else str(v)
                    if vtxt.strip():
                        parts.append(f"- **{k}**: {vtxt}")
            summary = "\n".join(parts)
            self.repo.save_application_summary(job_id, summary)
            self.root.title = "Report generated"
            self.stop_loading()
        # schedule to let overlay render first frame
        Clock.schedule_once(_do, 0.05)

    def export_to_linear(self):
        self.root.title = "Exporting to Linear (stub)"

    # Tray integration
    def _toggle_visibility(self, _icon, _item=None):
        try:
            if self._is_hidden:
                Window.show()
                self._is_hidden = False
            else:
                Window.hide()
                self._is_hidden = True
        except Exception:
            pass

    def _on_request_close(self, *args, **kwargs):
        # Minimize to tray instead of exiting
        try:
            Window.hide()
            self._is_hidden = True
        except Exception:
            pass
        return True

    def _tray_tooltip(self) -> str:
        if self.current_job_id:
            return f"processing: {self.current_job_id}"
        return "running..."

    def _exit_from_tray(self, _icon, _item=None):
        try:
            if self._tray_icon:
                self._tray_icon.visible = False
                self._tray_icon.stop()
        except Exception:
            pass
        # Stop Kivy app
        try:
            self.stop()
        except Exception:
            pass

    def _start_tray(self):
        try:
            if self._tray_icon:
                return
            # Create a simple icon from the clipper asset or a placeholder
            icon_path = Path(__file__).resolve().parents[2] / "jobops_clipper" / "src" / "icon.png"
            if icon_path.exists():
                image = Image.open(str(icon_path))
            else:
                image = Image.new('RGBA', (64, 64), (20, 20, 28, 220))
            menu = pystray.Menu(
                pystray.MenuItem('Show/Hide', self._toggle_visibility, default=True),
                pystray.MenuItem('Exit', self._exit_from_tray),
            )
            self._tray_icon = pystray.Icon("jobops")
            self._tray_icon.icon = image
            self._tray_icon.title = "JobOps"
            self._tray_icon.menu = menu
            self._tray_icon.visible = True

            def run_tray():
                try:
                    def setup(icon):
                        icon.visible = True
                    self._tray_icon.run(setup=setup)
                except Exception:
                    pass

            self._tray_thread = threading.Thread(target=run_tray, daemon=True)
            self._tray_thread.start()
            # Update tooltip periodically
            Clock.schedule_interval(lambda dt: self._update_tray_tooltip(), 1.0)
        except Exception:
            pass

    def _update_tray_tooltip(self):
        try:
            if self._tray_icon:
                self._tray_icon.title = self._tray_tooltip()
        except Exception:
            pass

    # Preloader overlay controls
    def start_loading(self, message: str = "Loading…"):
        try:
            overlay = self.root.ids.preloader
            label = self.root.ids.preloader_label
            label.text = message
            overlay.disabled = False
            overlay.opacity = 1
            # Animated dots
            def animate(_dt):
                base = message.rstrip('. ')
                current = label.text
                dots = (current.count('.') % 3) + 1 if current.startswith(base) else 1
                label.text = base + ('.' * dots)
            self._loader_anim_event = Clock.schedule_interval(animate, 0.5)
        except Exception:
            pass

    def stop_loading(self):
        try:
            if self._loader_anim_event:
                self._loader_anim_event.cancel()
                self._loader_anim_event = None
            overlay = self.root.ids.preloader
            overlay.opacity = 0
            overlay.disabled = True
        except Exception:
            pass

    # Import JSON and populate forms
    def import_json(self):
        # Open a file dialog restricted to JSON
        try:
            self.start_loading('Importing')
            root_tk = tk.Tk()
            root_tk.withdraw()
            file_path = filedialog.askopenfilename(
                title='Select job data JSON',
                filetypes=[('JSON files', '*.json')]
            )
            root_tk.destroy()
            if not file_path:
                self.stop_loading()
                return
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stop_loading()
            try:
                messagebox.showerror('Import Error', f'Failed to import JSON: {e}')
            except Exception:
                pass
            return
        # Validate basic structure
        if not isinstance(data, dict):
            self.stop_loading()
            try:
                messagebox.showerror('Import Error', 'Invalid JSON structure: expected an object at top level.')
            except Exception:
                pass
            return
        # Create or select a job id
        url = data.get('url') or data.get('job_posting_url') or 'http://example.com/placeholder'
        job_id = self.repo.get_or_create_job(url, data.get('job_title'), data.get('company_name'))
        self.current_job_id = job_id
        # Mapping: for each section, if keys exist in JSON, populate matching fields and save
        sm: ScreenManager = self.root.ids.screen_manager
        for spec in SECTION_SPECS:
            name = spec['name']
            screen = sm.get_screen(name) if sm.has_screen(name) else None
            section_payload = data.get(name) or {}
            if not isinstance(section_payload, dict):
                continue
            # Fill fields
            if screen and hasattr(screen, '_fields_widgets'):
                widgets = getattr(screen, '_fields_widgets')
                for field_id, widget in widgets.items():
                    if field_id in section_payload and isinstance(section_payload[field_id], (str, int, float)):
                        widget.text = str(section_payload[field_id])
            # Save to DB
            try:
                self.repo.upsert_section(job_id, name, section_payload)
            except Exception:
                pass
        self.stop_loading()
        self.root.title = 'Import completed'


def run():
    JobOpsApp().run()


KV = """
<RoundedTextInput@TextInput>:
    background_normal: ''
    background_active: ''
    foreground_color: 1, 1, 1, 0.96         # primary text
    hint_text_color: 0.78, 0.78, 0.82, 0.9  # muted hint
    selection_color: 0.290, 1.000, 0.471, 0.35  # selection highlight
    cursor_color: 0.290, 1.000, 0.471, 1    # #4ade80
    padding: [16, 12]
    canvas.before:
        Color:
            rgba: 0.094, 0.094, 0.125, 0.85   # input background (dark theme)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]
        Color:
            rgba: (0.290, 1.000, 0.471, 0.45) if self.focus else (0.290, 1.000, 0.471, 0.18)
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 10)
            width: 1.5

<PillButton@Button>:
    background_normal: ''
    background_color: 0.290, 1.000, 0.471, 1
    color: 0, 0, 0, 1
    size_hint_y: None
    height: 44
    canvas.before:
        Color:
            rgba: self.background_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [22,]
        Color:
            rgba: 1, 1, 1, 0.08
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 22)
            width: 1

<GlassCard@BoxLayout>:
    orientation: 'vertical'
    padding: 16, 16
    spacing: 12
    canvas.before:
        Color:
            rgba: 0.12, 0.12, 0.18, 0.55
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [16,]
        Color:
            rgba: 1, 1, 1, 0.10
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 16)
            width: 1

<JobOpsRoot>:
    title: 'JobOps App'
    BoxLayout:
        orientation: 'vertical'
        # Top menu row (glass)
        BoxLayout:
            size_hint_y: None
            height: 56
            padding: 8, 8
            spacing: 8
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.18, 0.6
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [12,]
                Color:
                    rgba: 1, 1, 1, 0.08
                Line:
                    rounded_rectangle: (self.x, self.y, self.width, self.height, 12)
                    width: 1
            ScrollView:
                do_scroll_x: True
                do_scroll_y: False
                bar_width: 2
                scroll_type: ['bars', 'content']
                BoxLayout:
                    id: top_menu_box
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: 40
                    size_hint_x: None
                    width: self.minimum_width
                    spacing: 8
        # Title + actions bar (glass)
        BoxLayout:
            size_hint_y: None
            height: 48
            padding: 8, 8
            spacing: 8
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.18, 0.6
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [12,]
                Color:
                    rgba: 1, 1, 1, 0.08
                Line:
                    rounded_rectangle: (self.x, self.y, self.width, self.height, 12)
                    width: 1
            Label:
                id: title_label
                text: root.title
                color: 1, 1, 1, 1
                halign: 'left'
            PillButton:
                text: 'Import JSON'
                background_color: 0.26, 0.74, 0.96, 1  # info blue
                size_hint_x: None
                width: 140
                on_release: app.import_json()
            PillButton:
                text: 'Generate'
                background_color: 0.290, 1.000, 0.471, 1  # #4ade80
                size_hint_x: None
                width: 140
                on_release: app.generate_report()
            PillButton:
                text: 'Export'
                background_color: 0.133, 0.773, 0.369, 1  # #22c55e
                size_hint_x: None
                width: 140
                on_release: app.export_to_linear()
        # Content area (glass background)
        BoxLayout:
            orientation: 'vertical'
            padding: 0, 8
            canvas.before:
                Color:
                    rgba: 0.06, 0.06, 0.09, 0.5
                Rectangle:
                    pos: self.pos
                    size: self.size
            ScreenManager:
                id: screen_manager

        # Preloader overlay
        FloatLayout:
            id: preloader
            size_hint: 1, 1
            opacity: 0
            disabled: True
            canvas.before:
                Color:
                    rgba: 0, 0, 0, 0.35
                Rectangle:
                    pos: self.pos
                    size: self.size
            AnchorLayout:
                anchor_x: 'center'
                anchor_y: 'center'
                size_hint: 1, 1
                BoxLayout:
                    orientation: 'vertical'
                    size_hint: None, None
                    width: min(root.width * 0.6, 520)
                    height: 160
                    padding: 16, 16
                    spacing: 8
                    canvas.before:
                        Color:
                            rgba: 0.12, 0.12, 0.18, 0.7
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [16,]
                        Color:
                            rgba: 1, 1, 1, 0.10
                        Line:
                            rounded_rectangle: (self.x, self.y, self.width, self.height, 16)
                            width: 1
                    Label:
                        id: preloader_label
                        text: 'Loading…'
                        color: 1,1,1,1
                        size_hint_y: None
                        height: 48
                        font_size: '20sp'
                    ProgressBar:
                        max: 100
                        value: 50
                        size_hint_y: None
                        height: 8

JobOpsRoot:
"""
