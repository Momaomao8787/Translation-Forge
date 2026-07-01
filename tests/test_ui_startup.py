from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Iterable
from unittest.mock import patch

import flet as ft
import pytest

from ui.main import main


class FakePage:
    def __init__(self) -> None:
        self.window = SimpleNamespace(width=None, height=None)
        self.controls: list[Any] = []
        self.title = ""
        self.padding = 0
        self.theme_mode = None
        self.scroll = None
        self.file_picker = None

    def add(self, *controls: Any) -> None:
        self.controls.extend(controls)
        self.update()

    def update(self) -> None:
        assert_controls_serializable(self.controls)

    def run_task(self, _coro: Any) -> None:
        return None

    def show_dialog(self, _dialog: Any) -> None:
        return None

    def pop_dialog(self) -> None:
        return None


def iter_child_controls(control: Any) -> Iterable[Any]:
    for attr in ("controls", "content", "actions"):
        value = getattr(control, attr, None)
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                if item is not None:
                    yield item
        else:
            yield value


def walk_controls(roots: Iterable[Any]) -> Iterable[Any]:
    stack = list(roots)
    while stack:
        current = stack.pop()
        yield current
        stack.extend(iter_child_controls(current))


def assert_controls_serializable(roots: Iterable[Any]) -> None:
    for control in walk_controls(roots):
        if isinstance(control, ft.SegmentedButton):
            assert isinstance(control.selected, list), (
                "SegmentedButton.selected must be list for Flet serialization"
            )
        if isinstance(control, ft.ExpansionTile):
            assert isinstance(control.expanded, bool)


@pytest.mark.parametrize("locale", ["zh-Hant", "zh-Hans", "en"])
def test_main_startup_builds_ui(locale: str) -> None:
    with patch("ui.main.load_ui_locale", return_value=locale):
        with patch("ui.main.resolve_ui_locale", return_value=locale):
            page = FakePage()
            main(page)

    assert page.title
    assert page.controls
    mode_buttons = [c for c in page.controls if isinstance(c, ft.SegmentedButton)]
    assert mode_buttons
    assert len(mode_buttons[0].segments) == 3
    assert any(isinstance(c, ft.Column) for c in walk_controls(page.controls))


def test_main_startup_with_saved_project_settings() -> None:
    saved = {
        "workMode": "scaffold",
        "sourceMod": r"C:\Mods\Source",
        "targetMod": r"C:\Mods\Target-TC",
        "modLanguage": "ChineseTraditional",
        "exportPath": r"C:\temp\pending.csv",
        "exportFormat": "csv",
        "createAbout": True,
    }
    with patch("ui.main.load_ui_locale", return_value="zh-Hant"):
        with patch("ui.main.resolve_ui_locale", return_value="zh-Hant"):
            with patch("ui.main.parse_saved_project_settings", return_value=saved):
                page = FakePage()
                main(page)

    mode_buttons = [c for c in page.controls if isinstance(c, ft.SegmentedButton)]
    assert mode_buttons
    assert mode_buttons[0].selected == ["scaffold"]
