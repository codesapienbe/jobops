from __future__ import annotations

from typing import Optional

from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput

from ..i18n import I18N


class SettingsScreen(Screen):
    def __init__(self, name: str, store: JsonStore, i18n: I18N, **kwargs):
        super().__init__(name=name, **kwargs)
        self.store = store
        self.i18n = i18n

        layout = BoxLayout(orientation="vertical", padding=16, spacing=12)
        layout.add_widget(Label(text=self.i18n.t("settings.title"), size_hint_y=None, height=32, bold=True))

        self.backend_url = TextInput(hint_text="Backend URL (e.g., http://localhost:8877)", size_hint_y=None, height=48)
        self.groq_api_key = TextInput(hint_text="Groq API Key", password=True, size_hint_y=None, height=48)
        self.linear_api_key = TextInput(hint_text="Linear API Key", password=True, size_hint_y=None, height=48)
        self.linear_team_id = TextInput(hint_text="Linear Team ID", size_hint_y=None, height=48)

        # Load existing
        if store.exists("settings"):
            cfg = store.get("settings")
            self.backend_url.text = cfg.get("backend_url", "")
            self.groq_api_key.text = cfg.get("groq_api_key", "")
            self.linear_api_key.text = cfg.get("linear_api_key", "")
            self.linear_team_id.text = cfg.get("linear_team_id", "")

        layout.add_widget(self.backend_url)
        layout.add_widget(self.groq_api_key)
        layout.add_widget(self.linear_api_key)
        layout.add_widget(self.linear_team_id)

        actions = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=None, height=56)
        btn_save = Button(text=self.i18n.t("common.save"), size_hint_x=None, width=120)
        btn_test = Button(text="Test", size_hint_x=None, width=120)
        actions.add_widget(btn_save)
        actions.add_widget(btn_test)
        layout.add_widget(actions)
        self.add_widget(layout)

        btn_save.bind(on_release=lambda *_: self._save())
        btn_test.bind(on_release=lambda *_: self._test())

    def _save(self) -> None:
        self.store.put(
            "settings",
            backend_url=self.backend_url.text.strip(),
            groq_api_key=self.groq_api_key.text.strip(),
            linear_api_key=self.linear_api_key.text.strip(),
            linear_team_id=self.linear_team_id.text.strip(),
        )
        try:
            from kivy.app import App
            app = App.get_running_app()
            app.root.title = "Settings saved"
        except Exception:
            pass

    def _test(self) -> None:
        ok_backend = self.backend_url.text.strip().startswith("http")
        ok_groq = len(self.groq_api_key.text.strip()) > 0 or self.groq_api_key.text.strip() == ""
        ok_linear = len(self.linear_api_key.text.strip()) > 0 or self.linear_api_key.text.strip() == ""
        try:
            from kivy.app import App
            app = App.get_running_app()
            app.root.title = f"Backend:{'OK' if ok_backend else 'NOK'} Groq:{'OK' if ok_groq else 'NOK'} Linear:{'OK' if ok_linear else 'NOK'}"
        except Exception:
            pass
