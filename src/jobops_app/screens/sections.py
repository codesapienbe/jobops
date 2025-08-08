from __future__ import annotations

from typing import Any, Dict, List

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window

from ..repository import Repository
from ..i18n import I18N


# Section specifications: name, title key, and form fields
SECTION_SPECS: List[Dict[str, Any]] = [
    {
        "name": "position_details",
        "title_key": "nav.position_details",
        "fields": [
            {"id": "job_title", "hint": "Job Title"},
            {"id": "company_name", "hint": "Company Name"},
            {"id": "location", "hint": "Location"},
            {"id": "employment_type", "hint": "Employment Type"},
            {"id": "job_description", "hint": "Job Description", "multiline": True},
        ],
    },
    {
        "name": "job_requirements",
        "title_key": "nav.job_requirements",
        "fields": [
            {"id": "required_skills", "hint": "Required Skills (comma-separated)"},
            {"id": "preferred_skills", "hint": "Preferred Skills (comma-separated)"},
            {"id": "required_experience", "hint": "Required Experience"},
        ],
    },
    {
        "name": "company_information",
        "title_key": "nav.company_information",
        "fields": [
            {"id": "website", "hint": "Website"},
            {"id": "industry", "hint": "Industry"},
            {"id": "company_size", "hint": "Company Size"},
            {"id": "headquarters", "hint": "Headquarters"},
        ],
    },
    {
        "name": "skills_matrix",
        "title_key": "nav.skills_matrix",
        "fields": [
            {"id": "assessments", "hint": "Assessments (free text)", "multiline": True},
            {"id": "identified_gaps", "hint": "Identified Gaps"},
        ],
    },
    {
        "name": "application_materials",
        "title_key": "nav.application_materials",
        "fields": [
            {"id": "resume_version", "hint": "Resume Version"},
            {"id": "cover_letter_version", "hint": "Cover Letter Version"},
        ],
    },
    {
        "name": "interview_schedule",
        "title_key": "nav.interview_schedule",
        "fields": [
            {"id": "stage", "hint": "Stage"},
            {"id": "date", "hint": "Date (YYYY-MM-DD)"},
            {"id": "time", "hint": "Time"},
            {"id": "notes", "hint": "Notes", "multiline": True},
        ],
    },
    {
        "name": "interview_preparation",
        "title_key": "nav.interview_preparation",
        "fields": [
            {"id": "questions_for_interviewer", "hint": "Questions for Interviewer", "multiline": True},
            {"id": "technical_skills_reviewed", "hint": "Technical Skills Reviewed"},
        ],
    },
    {
        "name": "communication_log",
        "title_key": "nav.communication_log",
        "fields": [
            {"id": "last_contact", "hint": "Last Contact Summary", "multiline": True},
        ],
    },
    {
        "name": "key_contacts",
        "title_key": "nav.key_contacts",
        "fields": [
            {"id": "recruiter_name", "hint": "Recruiter Name"},
            {"id": "recruiter_contact", "hint": "Recruiter Contact"},
            {"id": "hiring_manager", "hint": "Hiring Manager"},
        ],
    },
    {
        "name": "interview_feedback",
        "title_key": "nav.interview_feedback",
        "fields": [
            {"id": "self_assessment", "hint": "Self Assessment", "multiline": True},
            {"id": "interviewer_feedback", "hint": "Interviewer Feedback", "multiline": True},
        ],
    },
    {
        "name": "offer_details",
        "title_key": "nav.offer_details",
        "fields": [
            {"id": "position_title", "hint": "Position Title"},
            {"id": "salary_offered", "hint": "Salary Offered"},
            {"id": "benefits_package", "hint": "Benefits Package"},
        ],
    },
    {
        "name": "rejection_analysis",
        "title_key": "nav.rejection_analysis",
        "fields": [
            {"id": "reason_for_rejection", "hint": "Reason for Rejection"},
            {"id": "areas_for_improvement", "hint": "Areas for Improvement", "multiline": True},
        ],
    },
    {
        "name": "privacy_policy",
        "title_key": "nav.privacy_policy",
        "fields": [
            {"id": "data_usage_consent", "hint": "Data Usage Consent (yes/no)"},
            {"id": "retention_period", "hint": "Data Retention Period"},
        ],
    },
    {
        "name": "lessons_learned",
        "title_key": "nav.lessons_learned",
        "fields": [
            {"id": "key_insights", "hint": "Key Insights", "multiline": True},
            {"id": "action_items", "hint": "Action Items", "multiline": True},
        ],
    },
    {
        "name": "performance_metrics",
        "title_key": "nav.performance_metrics",
        "fields": [
            {"id": "skills_match_percentage", "hint": "Skills Match %"},
            {"id": "time_to_response_days", "hint": "Time to Response (days)"},
        ],
    },
    {
        "name": "advisor_review",
        "title_key": "nav.advisor_review",
        "fields": [
            {"id": "advisor_name", "hint": "Advisor Name"},
            {"id": "observations", "hint": "Observations", "multiline": True},
        ],
    },
    {
        "name": "application_summary",
        "title_key": "nav.application_summary",
        "fields": [
            {"id": "summary", "hint": "Summary", "multiline": True},
        ],
    },
]


def build_section_screen(spec: Dict[str, Any], repo: Repository, i18n: I18N) -> Screen:
    name = spec["name"]
    screen = Screen(name=name)

    scroll = ScrollView()
    # Center wrapper to keep content centered and with a max width
    wrapper = AnchorLayout(anchor_x='center', anchor_y='top')
    content = BoxLayout(orientation="vertical", padding=(16, 16), spacing=12, size_hint=(None, None))
    # Mobile-first width: use 92% of window up to 1040px
    target_width = min(int(Window.width * 0.92), 1040)
    content.width = target_width
    content.size_hint_y = None
    content.bind(minimum_height=content.setter("height"))

    # Glass card around the form
    form_card = BoxLayout(orientation='vertical', padding=(16, 16), spacing=12, size_hint_y=None)
    form_card.bind(minimum_height=form_card.setter('height'))

    def card_canvas(widget):
        widget.canvas.before.clear()
        from kivy.graphics import Color, RoundedRectangle, Line
        with widget.canvas.before:
            Color(0.12, 0.12, 0.18, 0.55)
            rr = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[16,])
            Color(1, 1, 1, 0.10)
            Line(rounded_rectangle=(widget.x, widget.y, widget.width, widget.height, 16), width=1)
        def update_rect(_instance, _value):
            rr.pos = widget.pos
            rr.size = widget.size
        widget.bind(pos=update_rect, size=update_rect)

    card_canvas(form_card)

    title = Label(text=i18n.t(spec["title_key"]), size_hint_y=None, height=32, color=(1,1,1,1))
    form_card.add_widget(title)

    fields_widgets: Dict[str, TextInput] = {}
    for f in spec["fields"]:
        ti = TextInput(hint_text=f["hint"], multiline=f.get("multiline", False), size_hint_y=None)
        # Apply the RoundedTextInput rule by class name
        ti.__class__.__name__ = 'RoundedTextInput'  # hint to kv rule
        ti.height = 120 if f.get("multiline", False) else 56
        fields_widgets[f["id"]] = ti
        form_card.add_widget(ti)

    actions = BoxLayout(orientation="horizontal", size_hint_y=None, height=56, spacing=12)
    btn_save = Button(text=i18n.t("common.save"), size_hint_x=None, width=140)
    btn_next = Button(text=i18n.t("common.next"), size_hint_x=None, width=140)
    # Pill styling via kv rule name
    btn_save.__class__.__name__ = 'PillButton'
    btn_next.__class__.__name__ = 'PillButton'
    actions.add_widget(Widget())
    actions.add_widget(btn_save)
    actions.add_widget(btn_next)
    form_card.add_widget(actions)

    content.add_widget(form_card)
    wrapper.add_widget(content)
    scroll.add_widget(wrapper)
    screen.add_widget(scroll)

    def on_save(*_):
        url_field = fields_widgets.get("job_posting_url")
        url = url_field.text if url_field else "http://example.com/placeholder"
        job_id = repo.get_or_create_job(url)
        try:
            from kivy.app import App
            app = App.get_running_app()
            if hasattr(app, "current_job_id"):
                app.current_job_id = job_id
        except Exception:
            pass
        data = {fid: fw.text for fid, fw in fields_widgets.items()}
        repo.upsert_section(job_id, name, data)

    def on_next(*_):
        from kivy.app import App
        app = App.get_running_app()
        names = [s["name"] for s in SECTION_SPECS]
        try:
            idx = names.index(name)
            next_name = names[(idx + 1) % len(names)]
            app.root.ids.screen_manager.current = next_name
            app.root.title = i18n.t(next(s["title_key"] for s in SECTION_SPECS if s["name"] == next_name))
        except Exception:
            pass

    btn_save.bind(on_release=on_save)
    btn_next.bind(on_release=on_next)

    # Expose fields to screen for external population (import feature)
    try:
        setattr(screen, "_fields_widgets", fields_widgets)
    except Exception:
        pass

    return screen
