from __future__ import annotations

import os
from pathlib import Path
import time
import subprocess, sys

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation

import threading
import pystray
from PIL import Image
import json
# import tkinter as tk
# from tkinter import filedialog, messagebox

from zipfile import ZipFile
from io import BytesIO

from .theme import apply_jobops_theme
from .repository import Repository
from .i18n import I18N
from .screens.sections import SECTION_SPECS, build_section_screen
from .screens.settings import SettingsScreen
from kivy.utils import platform
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
import re, webbrowser
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView


APP_TITLE = "JobOps App"

# Tab color palette (blue / gray / orange)
TAB_COLOR_BLUE_400 = (0.376, 0.647, 0.980, 1)  # #60a5fa
TAB_COLOR_BLUE_500 = (0.231, 0.510, 0.965, 1)  # #3b82f6
TAB_COLOR_BLUE_600 = (0.149, 0.388, 0.922, 1)  # #2563eb
TAB_COLOR_BLUE_700 = (0.114, 0.306, 0.847, 1)  # #1d4ed8
TAB_COLOR_BLUE_800 = (0.118, 0.251, 0.686, 1)  # #1e40af
TAB_COLOR_BLUE_900 = (0.118, 0.227, 0.541, 1)  # #1e3a8a

TAB_COLOR_ORANGE_500 = (0.976, 0.451, 0.086, 1)  # #f97316
TAB_COLOR_ORANGE_600 = (0.918, 0.345, 0.047, 1)  # #ea580c
TAB_COLOR_ORANGE_700 = (0.761, 0.255, 0.047, 1)  # #c2410c
TAB_COLOR_ORANGE_800 = (0.706, 0.325, 0.035, 1)  # #b45309

TAB_COLOR_GRAY_500 = (0.392, 0.455, 0.545, 1)  # #64748B
TAB_COLOR_GRAY_600 = (0.278, 0.333, 0.408, 1)  # #475569
TAB_COLOR_GRAY_700 = (0.200, 0.255, 0.333, 1)  # #334155
TAB_COLOR_GRAY_800 = (0.122, 0.161, 0.216, 1)  # #1f2937
TAB_COLOR_GRAY_900 = (0.067, 0.094, 0.141, 1)  # #111827

TAB_COLORS = {
    "position_details": TAB_COLOR_BLUE_500,
    "job_requirements": TAB_COLOR_BLUE_400,
    "company_information": TAB_COLOR_ORANGE_500,
    "skills_matrix": TAB_COLOR_BLUE_600,
    "application_materials": TAB_COLOR_BLUE_700,
    "interview_schedule": TAB_COLOR_BLUE_800,
    "interview_preparation": TAB_COLOR_ORANGE_600,
    "communication_log": TAB_COLOR_GRAY_500,
    "key_contacts": TAB_COLOR_BLUE_900,
    "interview_feedback": TAB_COLOR_BLUE_400,
    "offer_details": TAB_COLOR_ORANGE_700,
    "rejection_analysis": TAB_COLOR_GRAY_600,
    "privacy_policy": TAB_COLOR_GRAY_700,
    "lessons_learned": TAB_COLOR_GRAY_800,
    "performance_metrics": TAB_COLOR_GRAY_900,
    "advisor_review": TAB_COLOR_ORANGE_800,
    "application_summary": TAB_COLOR_BLUE_500,
    "settings": TAB_COLOR_GRAY_600,
}


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
        self._is_hidden: bool = False
        self._loader_anim_event = None
        # swipe handling
        self._touch_start_x: float | None = None
        self._tray_icon: pystray.Icon | None = None
        self._tray_thread: threading.Thread | None = None
        self._menu_buttons: dict[str, Button] = {}
        self._nav_history: list[str] = []
        # Use clipper icon for window/app icon if available
        icon_path = Path(__file__).resolve().parents[2] / "jobops_clipper" / "src" / "icon.png"
        if icon_path.exists():
            try:
                self.icon = str(icon_path)
            except Exception:
                pass
        self._exports_dir = Path(os.path.expanduser('~/.jobops/exports'))
        self._exports_dir.mkdir(parents=True, exist_ok=True)
        self._explorer_filter: str = ''
        self._thumb_cards: dict[str, object] = {}
        self._selected_thumb: str | None = None
        self._last_click_path: str | None = None
        self._last_click_ts: float = 0.0
        self._thumb_base_height: int = 200

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
        if platform in ('win', 'linux', 'macosx'):
            Clock.schedule_once(lambda dt: self._start_tray(), 0)
        # Intercept window close to minimize to tray
        try:
            if platform in ('win', 'linux', 'macosx'):
                Window.bind(on_request_close=self._on_request_close)
        except Exception:
            pass
        # Responsive nav
        try:
            Window.bind(size=lambda *_: self._toggle_nav_mode())
        except Exception:
            pass
        # Drag & drop (zip)
        try:
            Window.bind(on_dropfile=self._on_drop_file)  # deprecated but widely available
        except Exception:
            pass
        try:
            Window.bind(on_drop_file=self._on_drop_file)  # newer api on some builds
        except Exception:
            pass
        return root

    def on_start(self):
        # Initialize gallery message
        try:
            self._set_gallery_hint('Drag & drop a zip exported by JobOps into this window to browse files.')
        except Exception:
            pass
        try:
            self.root.ids.screen_manager.current = 'gallery'
        except Exception:
            pass
        Clock.schedule_once(lambda dt: self._center_window(), 0)

    def on_touch_down(self, touch):  # type: ignore[override]
        self._touch_start_x = touch.x
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):  # type: ignore[override]
        try:
            if self._touch_start_x is not None:
                dx = touch.x - self._touch_start_x
                if abs(dx) > 60:
                    sm = self.root.ids.screen_manager
                    sm.current = 'code' if dx < 0 else 'preview'
        finally:
            self._touch_start_x = None
        return super().on_touch_up(touch)

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

    def _create_preview(self) -> None:
        try:
            job_id = self.current_job_id or self.repo.get_latest_job_id()
            md = self._generate_markdown(job_id) if job_id else "# No job loaded\n\nImport JSON to begin."
            # Update code view
            try:
                self.root.ids.md_code.text = md
            except Exception:
                pass
            # Render pretty preview
            try:
                self._render_markdown_to_preview(md)
            except Exception:
                # fallback to plain text if rendering fails
                self.root.ids.md_preview_fallback.text = md
            self.root.title = "Markdown Preview"
        except Exception:
            pass

    def _render_markdown_to_preview(self, md: str) -> None:
        container: BoxLayout = self.root.ids.md_render
        container.clear_widgets()
        from kivy.uix.label import Label
        pad = 12
        
        link_color = '60a5fa'
        
        def to_markup(text: str) -> str:
            # links [text](url)
            def repl_link(m):
                t, u = m.group(1), m.group(2)
                safe_u = u.replace(']', '%5D').replace('[', '%5B')
                return f"[ref={safe_u}][color=#{link_color}]{t}[/color][/ref]"
            text2 = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl_link, text)
            # bold ** **
            text2 = re.sub(r"\*\*(.*?)\*\*", r"[b]\1[/b]", text2)
            # italic * * (non-greedy)
            text2 = re.sub(r"\*(.*?)\*", r"[i]\1[/i]", text2)
            # inline code ` `
            text2 = re.sub(r"`([^`]+)`", r"[font=Courier]\1[/font]", text2)
            return text2
        
        def fit_width(lbl: Label) -> None:
            try:
                lbl.text_size = (container.width - pad*2, None)
                container.bind(width=lambda *_: setattr(lbl, 'text_size', (container.width - pad*2, None)))
            except Exception:
                pass
        
        # simple parser
        lines = md.splitlines()
        in_code = False
        code_lines: list[str] = []
        paragraph: list[str] = []
        
        def flush_paragraph():
            nonlocal paragraph
            if not paragraph:
                return
            text = " ".join(paragraph).strip()
            if text:
                pretty = to_markup(text)
                lbl = Label(text=pretty, markup=True, color=(1,1,1,1), size_hint_y=None, halign='left', valign='top')
                fit_width(lbl)
                lbl.bind(texture_size=lambda _i,_v: setattr(lbl, 'height', lbl.texture_size[1]))
                lbl.bind(on_ref_press=lambda _i, ref: webbrowser.open(ref))
                container.add_widget(lbl)
            paragraph = []
        
        def flush_codeblock():
            nonlocal code_lines
            if not code_lines:
                return
            code = "\n".join(code_lines)
            holder = BoxLayout(orientation='vertical', padding=(10,8), size_hint_y=None)
            def draw_bg(widget):
                widget.canvas.before.clear()
                with widget.canvas.before:
                    Color(0.10,0.10,0.14,1)
                    rr = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[8,])
                def upd(*_):
                    rr.pos = widget.pos; rr.size = widget.size
                widget.bind(pos=upd, size=upd)
            draw_bg(holder)
            lbl = Label(text=code, font_name='Courier', color=(0.95,0.95,0.95,1), size_hint_y=None, halign='left', valign='top')
            try:
                lbl.text_size = (container.width - pad*2 - 20, None)
                container.bind(width=lambda *_: setattr(lbl, 'text_size', (container.width - pad*2 - 20, None)))
            except Exception:
                pass
            lbl.bind(texture_size=lambda _i,_v: setattr(lbl, 'height', lbl.texture_size[1]))
            holder.add_widget(lbl)
            holder.bind(minimum_height=holder.setter('height'))
            container.add_widget(holder)
            code_lines = []
        
        def try_parse_table(start_idx: int):
            # Detect GitHub-style table: header line with '|' then separator like |---|---|
            if '|' not in lines[start_idx]:
                return None
            header = lines[start_idx].strip()
            if not header.startswith('|') or not header.endswith('|'):
                return None
            if start_idx + 1 >= len(lines):
                return None
            sep = lines[start_idx+1].strip()
            if not (sep.startswith('|') and sep.endswith('|') and set(sep.replace('|','').replace('-','').replace(':','').strip()) == set()):
                return None
            # collect rows
            row_idx = start_idx + 2
            rows: list[list[str]] = []
            def split_row(s: str) -> list[str]:
                parts = [c.strip() for c in s.strip().strip('|').split('|')]
                return parts
            headers = split_row(header)
            while row_idx < len(lines) and lines[row_idx].strip().startswith('|') and lines[row_idx].strip().endswith('|'):
                rows.append(split_row(lines[row_idx]))
                row_idx += 1
            cols = max(len(headers), max((len(r) for r in rows), default=0))
            if cols == 0:
                return None
            grid = GridLayout(cols=cols, size_hint_y=None, spacing=6, padding=(4,4))
            def add_cell(text: str, is_header: bool = False):
                mk = to_markup(text)
                lbl = Label(text=mk, markup=True, color=(1,1,1,1), size_hint_y=None, halign='left', valign='top')
                lbl.bold = True if is_header else False
                try:
                    lbl.text_size = ( (container.width - pad*2) / cols - 8, None)
                    container.bind(width=lambda *_: setattr(lbl, 'text_size', ( (container.width - pad*2) / cols - 8, None)))
                except Exception:
                    pass
                lbl.bind(texture_size=lambda _i,_v: setattr(lbl, 'height', lbl.texture_size[1] + (2 if is_header else 0)))
                lbl.bind(on_ref_press=lambda _i, ref: webbrowser.open(ref))
                grid.add_widget(lbl)
            for h in headers:
                add_cell(h, True)
            for r in rows:
                for i in range(cols):
                    add_cell(r[i] if i < len(r) else '')
            grid.bind(minimum_height=grid.setter('height'))
            # card-like background
            def draw_bg(widget):
                widget.canvas.before.clear()
                with widget.canvas.before:
                    Color(0.14,0.14,0.18,0.8)
                    rr = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[8,])
                def upd(*_):
                    rr.pos = widget.pos; rr.size = widget.size
                widget.bind(pos=upd, size=upd)
            draw_bg(grid)
            container.add_widget(grid)
            return row_idx - start_idx
        
        i = 0
        while i < len(lines):
            raw = lines[i]
            line = raw.rstrip()
            # images ![alt](url)
            imgm = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line.strip())
            if imgm:
                flush_paragraph(); flush_codeblock()
                url = imgm.group(1)
                img = AsyncImage(source=url)
                img.size_hint_y = None
                img.keep_ratio = True
                img.allow_stretch = True
                # scale height on texture
                def on_tex(_i, _v):
                    try:
                        w, h = img.texture_size
                        if w and h:
                            target_w = container.width - pad*2
                            img.width = target_w
                            img.height = target_w * (h / float(w))
                    except Exception:
                        img.height = 180
                img.bind(texture=on_tex)
                container.bind(width=lambda *_: on_tex(None, None))
                img.height = 180
                container.add_widget(img)
                i += 1
                continue
            # code fences
            if line.strip().startswith('```'):
                if in_code:
                    in_code = False
                    flush_codeblock()
                else:
                    flush_paragraph()
                    in_code = True
                i += 1
                continue
            if in_code:
                code_lines.append(line)
                i += 1
                continue
            # tables
            delta = try_parse_table(i)
            if delta:
                i += delta
                continue
            # blank line
            if not line.strip():
                flush_paragraph()
                i += 1
                continue
            # headings
            if line.startswith('# '):
                flush_paragraph()
                lbl = Label(text=f"[b]{to_markup(line[2:])}[/b]", markup=True, color=(1,1,1,1), size_hint_y=None)
                lbl.font_size = '22sp'
                lbl.halign = 'left'; lbl.valign='top'
                fit_width(lbl)
                lbl.bind(texture_size=lambda _i,_v: setattr(lbl, 'height', lbl.texture_size[1]+6))
                lbl.bind(on_ref_press=lambda _i, ref: webbrowser.open(ref))
                container.add_widget(lbl)
                i += 1
                continue
            if line.startswith('## '):
                flush_paragraph()
                lbl = Label(text=f"[b]{to_markup(line[3:])}[/b]", markup=True, color=(0.86,0.90,0.98,1), size_hint_y=None)
                lbl.font_size = '18sp'
                lbl.halign = 'left'; lbl.valign='top'
                fit_width(lbl)
                lbl.bind(texture_size=lambda _i,_v: setattr(lbl, 'height', lbl.texture_size[1]+4))
                lbl.bind(on_ref_press=lambda _i, ref: webbrowser.open(ref))
                container.add_widget(lbl)
                i += 1
                continue
            # bullets
            if line.lstrip().startswith(('- ', '* ')):
                flush_paragraph()
                bullet = '• ' + to_markup(line.lstrip()[2:])
                lbl = Label(text=bullet, markup=True, color=(1,1,1,1), size_hint_y=None, halign='left', valign='top')
                fit_width(lbl)
                lbl.bind(texture_size=lambda _i,_v: setattr(lbl, 'height', lbl.texture_size[1]))
                lbl.bind(on_ref_press=lambda _i, ref: webbrowser.open(ref))
                container.add_widget(lbl)
                i += 1
                continue
            # paragraph accumulation
            paragraph.append(line)
            i += 1
        flush_paragraph()
        flush_codeblock()
        # ensure container resizes
        container.bind(minimum_height=container.setter('height'))
        try:
            container.width = container.parent.width if container.parent else container.width
        except Exception:
            pass
        container.parent and container.parent.bind(width=lambda *_: setattr(container, 'width', container.parent.width))
        container.parent and container.parent.parent and container.parent.parent.bind(width=lambda *_: setattr(container, 'width', container.parent.parent.width))

    def switch_to_section(self, name: str):
        # Repurpose navigation: only 'application_summary' shows Preview
        self._create_preview()
        self.root.ids.screen_manager.current = 'preview'
        self.root.title = 'Markdown Preview'
        self._hide_nav_overlay()
        self._update_back_buttons()

    def open_settings_screen(self):
        # Keep settings as-is for now (not shown in preview flow)
        sm: ScreenManager = self.root.ids.screen_manager
        screen_name = "settings"
        if not sm.has_screen(screen_name):
            sm.add_widget(SettingsScreen(name=screen_name, store=self.store, i18n=self.i18n))
        self.root.title = self.i18n.t("settings.title")
        sm.current = screen_name
        self._hide_nav_overlay()
        self._update_back_buttons()

    def generate_report(self):
        self.start_loading('Generating')
        def _do(_dt):
            job_id = self.current_job_id or self.repo.get_latest_job_id()
            if not job_id:
                self.root.title = "No job yet"
                self.stop_loading()
                return
            md = self._generate_markdown(job_id)
            self.repo.save_application_summary(job_id, md)
            try:
                self._render_markdown_to_preview(md)
                self.root.ids.md_code.text = md
                self.root.ids.screen_manager.current = 'preview'
            except Exception:
                pass
            self.root.title = "Preview updated"
            self.stop_loading()
        Clock.schedule_once(_do, 0.05)

    def download_pdf(self):
        try:
            md = self.root.ids.md_code.text or self.root.ids.md_preview.text
            if not md.strip():
                return
            pdf_bytes = self._markdown_to_pdf(md)
            # Safe default path (no OS dialog)
            out_dir = Path(os.path.expanduser('~/.jobops/exports'))
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = int(time.time())
            pdf_path = out_dir / f'application_{ts}.pdf'
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            self.root.title = f'Saved: {pdf_path}'
        except Exception as e:
            self.root.title = f'Export Error: {e}'

    def load_sample_data(self) -> None:
        try:
            self.start_loading('Loading sample')
            sample = self._sample_json()
            url = sample.get('url') or 'https://example.com/jobs/123'
            pos = sample.get('position_details', {})
            job_id = self.repo.get_or_create_job(url, pos.get('job_title'), pos.get('company_name'))
            self.current_job_id = job_id
            for key, payload in sample.items():
                if key == 'url':
                    continue
                if isinstance(payload, dict):
                    self.repo.upsert_section(job_id, key, payload)
            # Generate a zip (per-section) to exports and open folder
            zip_path = self.download_zip()
            self.stop_loading()
            if zip_path:
                self._open_in_file_manager(zip_path.parent)
        except Exception:
            self.stop_loading()

    def generate_and_open(self) -> None:
        try:
            zip_path = self.download_zip()
            if zip_path:
                self._open_in_file_manager(zip_path.parent)
        except Exception:
            pass

    def _sample_json(self) -> dict:
        return {
            "url": "https://careers.example.com/jobs/senior-python-engineer",
            "position_details": {
                "job_title": "Senior Python Engineer",
                "company_name": "Acme Corp",
                "location": "Remote (EU)",
                "employment_type": "Full-time",
                "job_description": "Design and build data-driven systems using FastAPI, Celery, and PostgreSQL."
            },
            "job_requirements": {
                "required_skills": "Python, FastAPI, SQLAlchemy, Celery, Docker, AWS",
                "preferred_skills": "Terraform, Kubernetes, Grafana",
                "required_experience": "5+ years"
            },
            "company_information": {
                "website": "https://example.com",
                "industry": "SaaS / Developer Tools",
                "company_size": "250-500",
                "headquarters": "Amsterdam, NL"
            },
            "skills_matrix": {
                "assessments": "Strong in async I/O, task queues, and observability.",
                "identified_gaps": "Would like deeper experience with Terraform modules."
            },
            "application_materials": {
                "resume_version": "resume_v7.pdf",
                "cover_letter_version": "cover_letter_acme.md"
            },
            "interview_schedule": {
                "stage": "Technical Screen",
                "date": "2025-08-20",
                "time": "10:00 CET",
                "notes": "Pair-programming with lead engineer"
            },
            "interview_preparation": {
                "questions_for_interviewer": "How do teams collaborate across timezones? What are on-call practices?",
                "technical_skills_reviewed": "async SQLAlchemy patterns, Redis reliability, CDK basics"
            },
            "communication_log": {"last_contact": "Recruiter confirmed interview for next Wednesday."},
            "key_contacts": {
                "recruiter_name": "Jamie Doe",
                "recruiter_contact": "jamie.doe@example.com",
                "hiring_manager": "Alex Smith"
            },
            "interview_feedback": {
                "self_assessment": "Good system design conversation, demoed retry/backoff patterns.",
                "interviewer_feedback": "Strong alignment with platform team; next round scheduled."
            },
            "offer_details": {
                "position_title": "Senior Python Engineer",
                "salary_offered": "€95,000 + stock options",
                "benefits_package": "Remote stipend, learning budget, private health"
            },
            "rejection_analysis": {
                "reason_for_rejection": "",
                "areas_for_improvement": ""
            },
            "privacy_policy": {
                "data_usage_consent": "yes",
                "retention_period": "12 months"
            },
            "lessons_learned": {
                "key_insights": "Keep concrete examples ready for idempotency and visibility timeouts.",
                "action_items": "Prepare a short Terraform module demo."
            },
            "performance_metrics": {
                "skills_match_percentage": "88%",
                "time_to_response_days": "3"
            },
            "advisor_review": {
                "advisor_name": "Mentor Bot",
                "observations": "Highlight observability achievements and incident retros."
            },
            "application_summary": {
                "summary": "Candidate shows strong backend platform experience and async correctness."
            }
        }

    def _generate_markdown(self, job_id: str) -> str:
        meta = self.repo.get_job_meta(job_id) or {}
        title = (meta.get('job_title') or 'Job Title').strip()
        company = (meta.get('company_name') or 'Company').strip()
        header = f"# {title} – {company}\n"
        sections = self.repo.list_sections_for_job(job_id)
        # Use SECTION_SPECS order
        order = [s["name"] for s in SECTION_SPECS if s["name"] != "application_summary"]
        parts = [header]
        for name in order:
            data = sections.get(name) or {}
            if not isinstance(data, dict) or not data:
                continue
            pretty = next((self.i18n.t(s["title_key"]) for s in SECTION_SPECS if s["name"] == name), name)
            parts.append(f"\n## {pretty}\n")
            for k, v in data.items():
                vtxt = v if isinstance(v, str) else str(v)
                if vtxt.strip():
                    parts.append(f"- **{k}**: {vtxt}")
        return "\n".join(parts).strip() + "\n"

    def download_zip(self):
        try:
            job_id = self.current_job_id or self.repo.get_latest_job_id()
            if not job_id:
                return None
            meta = self.repo.get_job_meta(job_id) or {}
            sections_all = self.repo.list_sections_for_job(job_id)
            order = [s["name"] for s in SECTION_SPECS if s["name"] != "application_summary"]
            out_dir = Path(os.path.expanduser('~/.jobops/exports'))
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = int(time.time())
            zip_path = out_dir / f'application_{ts}.zip'

            with ZipFile(zip_path, 'w') as zf:
                for idx, name in enumerate(order, start=1):
                    data = sections_all.get(name) or {}
                    if not isinstance(data, dict) or not data:
                        continue
                    pretty = next((s["title_key"] for s in SECTION_SPECS if s["name"] == name), name)
                    pretty_title = self.i18n.t(pretty) if hasattr(self, 'i18n') else name
                    md = self._generate_markdown_for_section(meta, pretty_title, data)
                    slug = self._slug(name)
                    num = f"{idx:02d}"
                    zf.writestr(f"{num}_{slug}.md", md.encode('utf-8'))
                    pdf_bytes = self._markdown_to_pdf(md)
                    zf.writestr(f"{num}_{slug}.pdf", pdf_bytes)
            self.root.title = f'Saved: {zip_path}'
            return zip_path
        except Exception as e:
            self.root.title = f'Export Error: {e}'
            return None

    def _generate_markdown_for_section(self, meta: dict, section_title: str, fields: dict) -> str:
        title = (meta.get('job_title') or 'Job Title').strip()
        company = (meta.get('company_name') or 'Company').strip()
        header = f"# {title} – {company}\n\n## {section_title}\n"
        parts = [header]
        for k, v in fields.items():
            vtxt = v if isinstance(v, str) else str(v)
            if vtxt.strip():
                parts.append(f"- **{k}**: {vtxt}")
        return "\n".join(parts).strip() + "\n"

    def _slug(self, text: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower())
        safe = re.sub(r"-+", "-", safe).strip('-')
        return safe or "section"

    def _markdown_to_pdf(self, md: str) -> bytes:
        # Render each section on a new page if it starts with '## '
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        from reportlab.lib.colors import HexColor
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        left = 20 * mm; right = 20 * mm; top = 20 * mm; bottom = 18 * mm
        x = left
        y = height - top
        page_num = 1
        import textwrap
        def footer():
            nonlocal page_num
            c.setFont('Helvetica', 9)
            c.setFillColor(HexColor('#94a3b8'))
            c.drawRightString(width - right, bottom - 6, f"Page {page_num}")
            c.setFillColor(HexColor('#000000'))
        def new_page():
            nonlocal y, page_num
            footer()
            c.showPage(); page_num += 1; y = height - top
        def draw_paragraph(text: str, font='Helvetica', size=11, color='#ffffff'):
            nonlocal y
            c.setFont(font, size)
            c.setFillColor(HexColor(color))
            for chunk in textwrap.wrap(text, width=100):
                c.drawString(x, y, chunk)
                y -= size + 2
                if y < bottom:
                    new_page()
            c.setFillColor(HexColor('#000000'))
        lines = md.splitlines()
        in_code = False
        code: list[str] = []
        for line in lines:
            if line.strip().startswith('```'):
                if in_code:
                    # flush code
                    c.setFillColor(HexColor('#0b1220'))
                    c.roundRect(x-2, y- (12*len(code)+10), width - left - right + 4, (12*len(code)+8), 6, fill=1, stroke=0)
                    c.setFillColor(HexColor('#e5e7eb'))
                    c.setFont('Courier', 10)
                    for cl in code:
                        c.drawString(x, y, cl)
                        y -= 12
                        if y < bottom:
                            new_page()
                    c.setFillColor(HexColor('#000000'))
                    code = []
                    in_code = False
                    y -= 6
                else:
                    in_code = True
                continue
            if in_code:
                code.append(line)
                continue
            if line.startswith('## '):
                if y != height - top:
                    new_page()
                c.setFont('Helvetica-Bold', 16)
                c.setFillColor(HexColor('#e2e8f0'))
                c.drawString(x, y, line[3:])
                c.setFillColor(HexColor('#000000'))
                y -= 20
                continue
            if line.startswith('# '):
                c.setFont('Helvetica-Bold', 20)
                c.setFillColor(HexColor('#60a5fa'))
                c.drawString(x, y, line[2:])
                c.setFillColor(HexColor('#000000'))
                y -= 24
                continue
            if line.lstrip().startswith(('- ', '* ')):
                bullet = '• ' + line.lstrip()[2:]
                draw_paragraph(bullet, size=11, color='#ffffff')
                continue
            if not line.strip():
                y -= 6
                if y < bottom:
                    new_page()
                continue
            draw_paragraph(line, size=11, color='#ffffff')
        footer(); c.save()
        return buffer.getvalue()

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
        if platform not in ('win', 'linux', 'macosx'):
            return False
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
            if platform not in ('win', 'linux', 'macosx'):
                return
            if self._tray_icon:
                return
            # Create a simple icon from the clipper asset or a placeholder
            icon_path = Path(__file__).resolve().parents[2] / "jobops_clipper" / "src" / "icon.png"
            if icon_path.exists():
                image = Image.open(str(icon_path)).convert('RGBA')
            else:
                image = Image.new('RGBA', (64, 64), (20, 20, 28, 220))
            menu = pystray.Menu(
                pystray.MenuItem('Show/Hide', self._toggle_visibility, default=True),
                pystray.MenuItem('Exit', self._exit_from_tray),
            )
            self._tray_icon = pystray.Icon("jobops", image=image, title="JobOps", menu=menu)
            try:
                self._tray_icon.run_detached()
            except Exception:
                # Fallback to manual thread
                def run_tray():
                    try:
                        self._tray_icon.run()
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
            if self._tray_icon and platform in ('win', 'linux', 'macosx'):
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
        # Show a file dialog (Kivy popup) to select a JSON file
        try:
            chooser = FileChooserIconView(filters=['*.json'], path=str(Path.home()))
            chooser.multiselect = False
            box = BoxLayout(orientation='vertical', spacing=6, padding=(8,8))
            box.add_widget(chooser)
            actions = BoxLayout(size_hint_y=None, height=46, spacing=8)
            ok_btn = Button(text='Open', size_hint_x=None, width=120)
            cancel_btn = Button(text='Cancel', size_hint_x=None, width=120)
            actions.add_widget(ok_btn); actions.add_widget(cancel_btn)
            box.add_widget(actions)
            popup = Popup(title='Select JSON to Open', content=box, size_hint=(0.9, 0.9))
            def do_open(*_):
                sel = chooser.selection[0] if chooser.selection else None
                popup.dismiss()
                if sel:
                    self._open_json(Path(sel))
            ok_btn.bind(on_release=do_open)
            cancel_btn.bind(on_release=lambda *_: popup.dismiss())
            popup.open()
        except Exception as e:
            self.root.title = f'Open error: {e}'

    def _open_json(self, import_path: Path) -> None:
        try:
            self.start_loading('Importing')
            if not import_path.exists():
                self.stop_loading()
                self.root.title = f'File not found: {import_path}'
                return
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stop_loading()
            self.root.title = f'Import Error: {e}'
            return
        if not isinstance(data, dict):
            self.stop_loading()
            self.root.title = 'Invalid JSON: expected an object'
            return
        url = data.get('url') or data.get('job_posting_url') or 'http://example.com/placeholder'
        job_id = self.repo.get_or_create_job(url, data.get('job_title'), data.get('company_name'))
        self.current_job_id = job_id
        for key, payload in data.items():
            if key == 'url':
                continue
            if isinstance(payload, dict):
                try:
                    self.repo.upsert_section(job_id, key, payload)
                except Exception:
                    pass
        self.stop_loading()
        self.root.title = 'Import completed'
        # refresh preview
        self._create_preview()

    def _update_active_tab(self, active_name: str) -> None:
        try:
            for name, btn in self._menu_buttons.items():
                base = TAB_COLORS.get(name, TAB_COLOR_GRAY_600)
                alpha = 1.0 if name == active_name else 0.7
                btn.background_color = (base[0], base[1], base[2], alpha)
        except Exception:
            pass

    def _update_back_buttons(self) -> None:
        try:
            back = self.root.ids.back_btn
            has_back = len(self._nav_history) > 0
            back.disabled = not has_back
            back.opacity = 1 if has_back else 0.45
        except Exception:
            pass

    def _go_back(self) -> None:
        try:
            if not self._nav_history:
                return
            name = self._nav_history.pop()
            self.switch_to_section(name)
        finally:
            self._update_back_buttons()

    def _go_home(self) -> None:
        try:
            home = SECTION_SPECS[0]["name"] if SECTION_SPECS else None
            if home:
                self._nav_history.clear()
                self.switch_to_section(home)
        except Exception:
            pass

    # Overlay navigation (mobile-first)
    def _build_nav_overlay(self) -> None:
        try:
            items = self.root.ids.nav_items
            items.clear_widgets()
            for spec in SECTION_SPECS:
                name = spec["name"]
                title = self.i18n.t(spec["title_key"])
                base = TAB_COLORS.get(name, TAB_COLOR_GRAY_600)
                b = Button(text=title, size_hint_y=None, height=50)
                b.__class__.__name__ = 'PillButton'
                b.background_normal = ''
                b.background_color = (base[0], base[1], base[2], 0.95)
                b.color = (1, 1, 1, 1)
                b.bind(on_release=lambda _btn, n=name: self.switch_to_section(n))
                items.add_widget(b)
            # Settings
            base = TAB_COLORS.get("settings", TAB_COLOR_GRAY_600)
            s = Button(text=self.i18n.t("settings.title"), size_hint_y=None, height=50)
            s.__class__.__name__ = 'PillButton'
            s.background_normal = ''
            s.background_color = (base[0], base[1], base[2], 0.95)
            s.color = (1, 1, 1, 1)
            s.bind(on_release=lambda *_: self.open_settings_screen())
            items.add_widget(s)
        except Exception:
            pass

    def _open_burger_menu(self):
        self._build_nav_overlay()
        self._show_nav_overlay()

    def _show_nav_overlay(self) -> None:
        try:
            overlay = self.root.ids.nav_overlay
            panel = self.root.ids.nav_panel
            overlay.disabled = False
            # Start hidden and slide/fade in
            overlay.opacity = 0
            panel.y = self.root.height
            Animation(opacity=1, d=0.18).start(overlay)
            Animation(y=self.root.height - panel.height, d=0.22, t='out_quad').start(panel)
        except Exception:
            pass

    def _hide_nav_overlay(self) -> None:
        try:
            overlay = self.root.ids.nav_overlay
            panel = self.root.ids.nav_panel
            if overlay.opacity == 0:
                overlay.disabled = True
                return
            def _disable(*_):
                overlay.disabled = True
            Animation(opacity=0, d=0.15).bind(on_complete=lambda *_: _disable()).start(overlay)
            Animation(y=self.root.height, d=0.18, t='in_quad').start(panel)
        except Exception:
            pass

    def _toggle_nav_mode(self) -> None:
        try:
            small = Window.width < 900
            burger = self.root.ids.burger_btn
            scroll = self.root.ids.top_menu_scroll
            burger.opacity = 1 if small else 0
            burger.disabled = not small
            scroll.opacity = 0 if small else 1
            scroll.disabled = small
        except Exception:
            pass

    def _refresh_explorer(self) -> None:
        try:
            tree_container = self.root.ids.file_tree
            tree_container.clear_widgets()
            # Hint row
            from kivy.uix.label import Label as KLabel
            hint = KLabel(text='Browse ~/.jobops/exports — click [DIR] to expand, click ZIP to extract, click file to preview', color=(1,1,1,0.7), size_hint_y=None)
            hint.bind(texture_size=lambda _i,_v: setattr(hint, 'height', max(24, hint.texture_size[1]+6)))
            tree_container.add_widget(hint)

            tv = TreeView(hide_root=True, indent_level=18)
            tv.size_hint_y = None
            tv.size_hint_x = 1
            tv.bind(minimum_height=tv.setter('height'))
            def _sync_width(*_):
                tv.width = tree_container.width
            _sync_width()
            tree_container.bind(width=_sync_width)

            root_node = tv.add_node(TreeViewLabel(text=f"[v] {self._exports_dir.name}", is_open=True, no_selection=False, bold=True))

            filter_q = (self._explorer_filter or '').lower().strip()

            def include_path(p: Path) -> bool:
                if not filter_q:
                    return True
                return filter_q in p.name.lower()

            def bind_dir_toggle(label_widget: TreeViewLabel, node_ref):
                def on_touch(_w, touch):
                    try:
                        if not label_widget.get_root_window():
                            return False
                        lx, ly = label_widget.to_window(label_widget.x, label_widget.y)
                        if lx <= touch.x <= lx + label_widget.width and ly <= touch.y <= ly + label_widget.height:
                            tv.toggle_node(node_ref)
                            # update arrow
                            prefix = '[v]' if node_ref.is_open else '[>]'
                            parts = label_widget.text.split(' ', 1)
                            label_widget.text = f"{prefix} {parts[1] if len(parts)>1 else ''}"
                            return True
                    except Exception:
                        return False
                    return False
                label_widget.bind(on_touch_down=on_touch)

            def bind_file_open(label_widget: TreeViewLabel, full_path: Path):
                def on_touch(_w, touch):
                    try:
                        if not label_widget.get_root_window():
                            return False
                        lx, ly = label_widget.to_window(label_widget.x, label_widget.y)
                        if lx <= touch.x <= lx + label_widget.width and ly <= touch.y <= ly + label_widget.height:
                            p = full_path
                            if p.suffix.lower() == '.zip':
                                target_dir = p.parent / p.stem
                                if not target_dir.exists():
                                    try:
                                        with ZipFile(p, 'r') as zf:
                                            zf.extractall(target_dir)
                                    except Exception as e:
                                        self.root.title = f'Unzip error: {e}'
                                        return True
                                self._refresh_explorer()
                                self.root.title = f'Extracted: {target_dir.name}'
                            elif p.suffix.lower() in ('.md', '.pdf'):
                                self._preview_file(p)
                            else:
                                self.root.title = f'Unsupported: {p.name}'
                            return True
                    except Exception:
                        return False
                    return False
                label_widget.bind(on_touch_down=on_touch)

            def add_dir(path: Path, parent) -> bool:
                has_visible = False
                try:
                    entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
                except Exception:
                    entries = []
                for p in entries:
                    if p.is_dir():
                        dir_label = TreeViewLabel(text=f"[>] {p.name}", is_open=False, no_selection=False)
                        dir_label.path = str(p)
                        node = tv.add_node(dir_label, parent)
                        bind_dir_toggle(dir_label, node)
                        child_visible = add_dir(p, node)
                        if not child_visible and not include_path(p):
                            tv.remove_node(node)
                        else:
                            has_visible = True
                    else:
                        if include_path(p):
                            tag = '[MD ]' if p.suffix.lower() == '.md' else ('[PDF]' if p.suffix.lower() == '.pdf' else '[ZIP]')
                            lbl = TreeViewLabel(text=f"{tag} {p.name}", no_selection=False)
                            lbl.path = str(p)
                            tv.add_node(lbl, parent)
                            bind_file_open(lbl, p)
                            has_visible = True
                return has_visible

            add_dir(self._exports_dir, root_node)
            tree_container.add_widget(tv)
        except Exception as e:
            self.root.title = f'Explorer error: {e}'

    def set_explorer_filter(self, text: str) -> None:
        self._explorer_filter = (text or '').strip()
        self._refresh_explorer()

    def open_exports_folder(self) -> None:
        try:
            webbrowser.open(self._exports_dir.as_uri())
        except Exception:
            pass

    def _preview_file(self, path: Path) -> None:
        try:
            preview_container = self.root.ids.md_render
            # Clear
            preview_container.clear_widgets()
            ext = path.suffix.lower()
            if ext == '.md':
                with open(path, 'r', encoding='utf-8') as f:
                    md = f.read()
                self._render_markdown_to_preview(md)
            else:
                preview_container.add_widget(self._mk_label('Only Markdown previews are supported here.'))
            self.root.title = f'Previewing: {path.name}'
        except Exception as e:
            self.root.title = f'Preview error: {e}'

    def _mk_label(self, text: str):
        from kivy.uix.label import Label
        lbl = Label(text=text, color=(1,1,1,1), size_hint_y=None, halign='left', valign='top')
        lbl.text_size = (self.root.ids.md_render.width - 24, None)
        lbl.bind(texture_size=lambda _i,_v: setattr(lbl, 'height', lbl.texture_size[1]))
        return lbl

    def _render_pdf_to_preview(self, pdf_path: Path) -> None:
        try:
            import fitz  # pymupdf
            container = self.root.ids.md_render
            doc = fitz.open(pdf_path)
            for page in doc:
                pix = page.get_pixmap(dpi=160)
                img = Image()
                img.texture = self._pixmap_to_texture(pix)
                img.size_hint_y = None
                img.height = img.texture.height
                img.width = container.width - 24
                img.allow_stretch = True
                img.keep_ratio = True
                container.add_widget(img)
            container.bind(minimum_height=container.setter('height'))
        except Exception as e:
            container = self.root.ids.md_render
            container.add_widget(self._mk_label(f'Failed to render PDF: {e}'))

    def _pixmap_to_texture(self, pix):
        from kivy.graphics.texture import Texture
        mode = 'rgba' if pix.alpha else 'rgb'
        tex = Texture.create(size=(pix.width, pix.height), colorfmt=mode)
        tex.blit_buffer(pix.samples, colorfmt=mode, bufferfmt='ubyte')
        tex.flip_vertical()
        return tex

    def _on_drop_file(self, *args):
        try:
            # Supports both events:
            # - on_dropfile(window, file_path)
            # - on_drop_file(window, file_path, x, y)
            if len(args) >= 2:
                file_path = args[1]
            elif len(args) == 1:
                file_path = args[0]
            else:
                self.root.title = 'Drop error: missing path'
                return
            path_str = file_path.decode('utf-8') if isinstance(file_path, (bytes, bytearray)) else str(file_path)
            p = Path(path_str)
            if not p.exists():
                self.root.title = f'Dropped path not found: {p}'
                return
            if p.suffix.lower() == '.zip':
                target = self._exports_dir / p.stem
                if not target.exists():
                    target.mkdir(parents=True, exist_ok=True)
                    with ZipFile(p, 'r') as zf:
                        zf.extractall(target)
                self._build_gallery(target)
                self.root.title = f'Loaded: {p.name}'
            else:
                self._set_gallery_hint('Please drop a .zip file exported by JobOps')
        except Exception as e:
            self.root.title = f'Drop error: {e}'

    def _set_gallery_hint(self, text: str) -> None:
        try:
            self.root.ids.gallery_hint.text = text
        except Exception:
            pass

    def _build_gallery(self, base_dir: Path) -> None:
        try:
            grid = self.root.ids.gallery_grid
            grid.clear_widgets()
            self._thumb_cards.clear()
            files = []
            # Only markdown files
            files.extend(base_dir.rglob('*.md'))
            files = sorted(files, key=lambda p: p.name.lower())
            if not files:
                self._set_gallery_hint('No markdown files found in the zip.')
            else:
                self._set_gallery_hint(f'Files in {base_dir.name} ({len(files)})')
            # Smaller thumbnails
            self._thumb_base_height = 120
            for f in files:
                card = self._make_thumb_card(f)
                grid.add_widget(card)
                self._thumb_cards[str(f)] = card
            self._resize_gallery()
            try:
                Window.bind(size=lambda *_: self._resize_gallery())
            except Exception:
                pass
            self.root.ids.screen_manager.current = 'gallery'
        except Exception as e:
            self.root.title = f'Gallery error: {e}'

    def _resize_gallery(self):
        try:
            grid = self.root.ids.gallery_grid
            scroll = self.root.ids.gallery_scroll
            n = len(grid.children)
            if n == 0:
                return
            spacing = 10
            padding_top_bottom = 8
            # Start with a reasonable col guess
            col_width = 240
            max_cols = max(1, int(self.root.width / 180))
            cols = max(1, min(max_cols, int(self.root.width / col_width)))
            rows = (n + cols - 1) // cols
            needed = rows * self._thumb_base_height + (rows - 1) * spacing + padding_top_bottom
            # Increase columns until it fits or we hit max_cols
            while needed > scroll.height and cols < max_cols:
                cols += 1
                rows = (n + cols - 1) // cols
                needed = rows * self._thumb_base_height + (rows - 1) * spacing + padding_top_bottom
            grid.cols = cols
            # ensure card heights are consistent
            for child in grid.children:
                try:
                    child.height = self._thumb_base_height
                except Exception:
                    pass
        except Exception:
            pass

    def _select_thumb(self, card_widget, path: Path):
        # Visual highlight for selection
        try:
            # reset previous
            if self._selected_thumb and self._selected_thumb in self._thumb_cards:
                prev = self._thumb_cards[self._selected_thumb]
                self._apply_card_bg(prev, (0.12, 0.12, 0.18, 0.9))
            self._selected_thumb = str(path)
            self._apply_card_bg(card_widget, (0.18, 0.18, 0.22, 0.95))
        except Exception:
            pass

    def _apply_card_bg(self, widget, rgba):
        try:
            widget.canvas.before.clear()
            with widget.canvas.before:
                Color(*rgba)
                rr = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[10,])
            def upd(*_):
                rr.pos = widget.pos; rr.size = widget.size
            widget.bind(pos=upd, size=upd)
        except Exception:
            pass

    def _make_thumb_card(self, path: Path):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        holder = BoxLayout(orientation='vertical', size_hint_y=None, height=self._thumb_base_height, padding=(8,8), spacing=6)
        self._apply_card_bg(holder, (0.12,0.12,0.18,0.9))
        # markdown quick preview (first 3 lines)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                first = '\n'.join(f.read().splitlines()[:3])
            lbl = Label(text=first or '(empty)', color=(1,1,1,0.9), size_hint_y=None, halign='left', valign='top')
            lbl.text_size = (220, None)
            lbl.bind(texture_size=lambda _i,_v: setattr(lbl, 'height', min(self._thumb_base_height-40, lbl.texture_size[1])))
            holder.add_widget(lbl)
        except Exception:
            holder.add_widget(Label(text='[MD preview failed]', color=(1,1,1,0.8), size_hint_y=None, height=self._thumb_base_height-40))
        cap = Label(text=path.name, color=(1,1,1,1), size_hint_y=None)
        cap.text_size=(220,None)
        cap.bind(texture_size=lambda _i,_v: setattr(cap, 'height', min(30, cap.texture_size[1])))
        holder.add_widget(cap)
        def on_touch(_w, touch):
            try:
                if not holder.get_root_window():
                    return False
                lx, ly = holder.to_window(holder.x, holder.y)
                if lx <= touch.x <= lx + holder.width and ly <= touch.y <= ly + holder.height:
                    self._select_thumb(holder, path)
                    now = time.time()
                    if self._last_click_path == str(path) and (now - self._last_click_ts) <= 0.35:
                        self._preview_file(path)
                        self.root.ids.screen_manager.current = 'preview'
                        self._last_click_path = None
                        self._last_click_ts = 0.0
                    else:
                        self._last_click_path = str(path)
                        self._last_click_ts = now
                    return True
            except Exception:
                return False
            return False
        holder.bind(on_touch_down=on_touch)
        return holder

    def _open_in_file_manager(self, path: Path) -> None:
        try:
            if sys.platform == 'darwin':
                subprocess.run(['open', str(path)], check=False)
            elif os.name == 'nt':
                os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                subprocess.run(['xdg-open', str(path)], check=False)
        except Exception:
            try:
                webbrowser.open(path.as_uri())
            except Exception:
                pass


def run():
    JobOpsApp().run()


KV = """
<RoundedTextInput@TextInput>:
    background_normal: ''
    background_active: ''
    foreground_color: 1, 1, 1, 0.96         # primary text
    hint_text_color: 0.78, 0.78, 0.82, 0.9  # muted hint
    selection_color: 0.231, 0.510, 0.965, 0.35  # selection highlight (blue)
    cursor_color: 0.231, 0.510, 0.965, 1    # primary blue
    padding: [16, 12]
    canvas.before:
        Color:
            rgba: 0.094, 0.094, 0.125, 0.85   # input background (dark theme)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10,]
        Color:
            rgba: (0.231, 0.510, 0.965, 0.45) if self.focus else (0.231, 0.510, 0.965, 0.18)
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 10)
            width: 1.5

<PillButton@Button>:
    background_normal: ''
    background_color: 0.231, 0.510, 0.965, 1  # primary blue
    color: 1, 1, 1, 1
    size_hint_y: None
    size_hint_x: None
    height: 44
    width: self.texture_size[0] + dp(28)
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
        # Simple top bar
        BoxLayout:
            size_hint_y: None
            height: 44
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

        # Content area (glass background)
        FloatLayout:
            canvas.before:
                Color:
                    rgba: 0.06, 0.06, 0.09, 0.5
                Rectangle:
                    pos: self.pos
                    size: self.size
            BoxLayout:
                orientation: 'horizontal'
                padding: 0, 8
                size_hint: 1, 1
                # Gallery and Preview area
                ScreenManager:
                    id: screen_manager
                    Screen:
                        name: 'gallery'
                        BoxLayout:
                            orientation: 'vertical'
                            spacing: 6
                            padding: 8, 8
                            Label:
                                id: gallery_hint
                                text: 'Drop a zip here'
                                color: 1,1,1,0.8
                                size_hint_y: None
                                height: 28
                            ScrollView:
                                id: gallery_scroll
                                do_scroll_x: False
                                do_scroll_y: True
                                bar_width: 2
                                GridLayout:
                                    id: gallery_grid
                                    cols: 3
                                    size_hint_y: None
                                    height: self.minimum_height
                                    spacing: 10
                                    padding: 4,4
                    Screen:
                        name: 'preview'
                        ScrollView:
                            do_scroll_x: False
                            do_scroll_y: True
                            bar_width: 2
                            scroll_type: ['bars', 'content']
                            size_hint: 1, 1
                            BoxLayout:
                                id: md_render
                                orientation: 'vertical'
                                padding: 12, 12
                                spacing: 8
                                size_hint_y: None
                                size_hint_x: 1
                                width: self.parent.width
                                height: self.minimum_height
                                Label:
                                    id: md_preview_fallback
                                    text: ''
                                    color: 1,1,1,1
                                    size_hint_y: None
                                    size_hint_x: 1
                                    text_size: self.width, None
                                    height: self.texture_size[1]
                                    halign: 'left'
                                    valign: 'top'
                        Screen:
                            name: 'code'
                            BoxLayout:
                                orientation: 'vertical'
                                padding: 8, 8
                                TextInput:
                                    id: md_code
                                    text: ''
                                    hint_text: 'Markdown code will appear here'
                                    foreground_color: 1,1,1,1
                                    background_color: 0.09,0.09,0.12,1
                                    cursor_color: 0.8,0.8,0.8,1
                                    size_hint: 1, 1
                                    multiline: True
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

        # Bottom sticky bar
        BoxLayout:
            size_hint_y: None
            height: 56
            padding: 10, 10
            spacing: 10
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.18, 0.8
                Rectangle:
                    pos: self.pos
                    size: self.size
            PillButton:
                text: 'Open'
                background_color: 0.26, 0.74, 0.96, 1
                on_release: app.import_json()
            PillButton:
                text: 'Demo'
                background_color: 0.118, 0.227, 0.541, 1
                on_release: app.load_sample_data()
            PillButton:
                text: 'Generate'
                background_color: 0.976, 0.451, 0.086, 1
                on_release: app.generate_and_open()
            Widget:
                size_hint_x: 1


JobOpsRoot:
"""
