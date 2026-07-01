from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from core.models import LANG_PACKAGE_SUFFIX

INVALID_PATH_CHARS = re.compile(r'[<>:"/\\|?*]')
STRIP_SUFFIXES = (
    "Localized",
    "Translation",
    *sorted(LANG_PACKAGE_SUFFIX.values(), key=len, reverse=True),
)
WINDOWS_RESERVED = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)
MAX_BASENAME_LEN = 80


def lang_package_suffix(lang: str) -> str:
    return LANG_PACKAGE_SUFFIX.get(lang, lang[:6] if lang else "LOC")


def sanitize_basename(name: str) -> str:
    text = (name or "").strip().strip(".")
    text = INVALID_PATH_CHARS.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text.upper() in WINDOWS_RESERVED:
        return "Mod"
    if len(text) > MAX_BASENAME_LEN:
        text = text[:MAX_BASENAME_LEN].rstrip(". ")
    return text or "Mod"


def strip_known_suffixes(basename: str) -> str:
    text = basename.strip()
    changed = True
    while changed and text:
        changed = False
        for suffix in STRIP_SUFFIXES:
            token = f"-{suffix}"
            if text.endswith(token):
                text = text[: -len(token)].rstrip(". ")
                changed = True
                break
    return text or basename


def read_about_name(source_mod: Path) -> str:
    about_path = source_mod / "About" / "About.xml"
    if not about_path.is_file():
        return ""
    try:
        root = ET.parse(about_path).getroot()
    except ET.ParseError:
        return ""
    name_el = root.find("name")
    if name_el is not None and name_el.text:
        return name_el.text.strip()
    return ""


def basename_for_source(source_mod: Path) -> str:
    about_name = read_about_name(source_mod)
    if about_name:
        return sanitize_basename(about_name)
    return sanitize_basename(source_mod.name)


def default_rimworld_mods_dir() -> Path | None:
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    default = Path(pf86) / "Steam" / "steamapps" / "common" / "RimWorld" / "Mods"
    if default.is_dir():
        return default
    return None


def resolve_rimworld_mods_dir(source_mod: Path) -> Path | None:
    resolved = source_mod.resolve()
    parts = resolved.parts
    for idx, part in enumerate(parts):
        if part.lower() == "mods":
            return Path(*parts[: idx + 1])
    for idx, part in enumerate(parts):
        if part.lower() == "steamapps":
            candidate = Path(*parts[: idx + 1]) / "common" / "RimWorld" / "Mods"
            if candidate.is_dir():
                return candidate
    return default_rimworld_mods_dir()


def parent_dir_for_target(source_mod: Path) -> Path:
    fixed = default_rimworld_mods_dir()
    if fixed is not None:
        return fixed
    mods_dir = resolve_rimworld_mods_dir(source_mod)
    if mods_dir is not None:
        return mods_dir
    return source_mod.resolve().parent


def allocate_unique_folder(parent: Path, folder_name: str) -> tuple[Path, str]:
    candidate = parent / folder_name
    if not candidate.exists():
        return candidate, folder_name
    n = 2
    while True:
        alt_name = f"{folder_name}-{n}"
        alt = parent / alt_name
        if not alt.exists():
            return alt, alt_name
        n += 1


def suggest_folder_name(source_mod: Path, lang: str) -> str:
    base = strip_known_suffixes(basename_for_source(source_mod))
    suffix = lang_package_suffix(lang)
    return f"{base}-{suffix}"


def suggest_target_mod_path(source_mod: Path, lang: str) -> tuple[Path, str]:
    parent = parent_dir_for_target(source_mod)
    folder_name = suggest_folder_name(source_mod, lang)
    path, final_name = allocate_unique_folder(parent, folder_name)
    return path, final_name


def is_subpath(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def paths_equal(a: Path, b: Path) -> bool:
    return str(a.resolve()).lower() == str(b.resolve()).lower()


def validate_scaffold_target(source_mod: Path, target_mod: Path) -> str | None:
    if not source_mod.is_dir():
        return "err.source_mod_missing"
    if paths_equal(source_mod, target_mod):
        return "err.scaffold_target_same_as_source"
    if is_subpath(target_mod, source_mod):
        return "err.scaffold_target_inside_source"
    if target_mod.exists() and target_mod.is_file():
        return "err.scaffold_target_is_file"
    parent = target_mod.parent
    if parent.exists() and not os.access(parent, os.W_OK):
        return "err.scaffold_parent_not_writable"
    return None
