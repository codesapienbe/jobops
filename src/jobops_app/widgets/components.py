from __future__ import annotations

from kivymd.uix.textfield import MDTextField


def text_input(hint: str, multiline: bool = False) -> MDTextField:
    tf = MDTextField(hint_text=hint, multiline=multiline)
    return tf
