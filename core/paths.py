from __future__ import annotations

import re
from pathlib import Path

from core.errors import LocalizedError

from core.models import RIMWORLD_LANGUAGES

INVALID_LANG_CHARS = re.compile(r'[<>:"/\\|?*]')
_RIMWORLD_LANGS = frozenset(RIMWORLD_LANGUAGES)


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def resolve_mod_path(path: str | Path, empty_key: str) -> Path:
    if path is None:
        raise LocalizedError(empty_key)
    text = str(path).strip()
    if not text or text == ".":
        raise LocalizedError(empty_key)
    return normalize_path(text)


def validate_lang_name(lang: str) -> str:
    lang = lang.strip()
    if not lang or INVALID_LANG_CHARS.search(lang):
        raise LocalizedError("err.invalid_lang_name")
    return lang


def validate_lang_name_strict(lang: str) -> str:
    lang = validate_lang_name(lang)
    if lang not in _RIMWORLD_LANGS:
        raise LocalizedError("err.invalid_lang_name")
    return lang


def discover_defs_roots(source_mod: Path) -> list[Path]:
    roots: list[Path] = []
    if not source_mod.is_dir():
        return roots
    for path in source_mod.rglob("Defs"):
        if not path.is_dir():
            continue
        if any(path.glob("*.xml")) or any(path.rglob("*.xml")):
            roots.append(path.resolve())
    unique = sorted(set(roots), key=lambda p: str(p).lower())
    return unique


def lang_root(target_mod: Path, target_lang: str) -> Path:
    return target_mod / "Languages" / target_lang


def definjected_root(target_mod: Path, target_lang: str) -> Path:
    return lang_root(target_mod, target_lang) / "DefInjected"
