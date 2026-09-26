from __future__ import annotations

import re
import xml.etree.ElementTree as ET
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


_VERSION_TEXT = re.compile(r"^\d+(\.\d+){1,3}$")

Version = tuple[int, ...]


def parse_version(text: str | None) -> Version | None:
    text = (text or "").strip()
    if not _VERSION_TEXT.match(text):
        return None
    return tuple(int(p) for p in text.split("."))


def format_version(version: Version) -> str:
    return f"{version[0]}.{version[1]}"


def supported_versions(mod_root: Path) -> list[Version]:
    about = mod_root / "About" / "About.xml"
    if not about.is_file():
        return []
    try:
        root = ET.parse(about).getroot()
    except ET.ParseError:
        return []
    out = []
    for li in root.findall("supportedVersions/li"):
        version = parse_version(li.text)
        if version is not None:
            out.append(version[:2])
    return out


def resolve_game_version(game_version: str | None, *mods: Path | None) -> Version | None:
    explicit = parse_version(game_version)
    if explicit is not None:
        return explicit[:2]
    for mod in mods:
        if mod is not None:
            versions = supported_versions(mod)
            if versions:
                return max(versions)
    return None


def is_mod_root(path: Path) -> bool:
    return (path / "About" / "About.xml").is_file() or (path / "LoadFolders.xml").is_file()


def _parse_load_folders(path: Path) -> dict[str, list[str]]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return {}
    table: dict[str, list[str]] = {}
    for node in root:
        if not isinstance(node.tag, str):
            continue
        key = node.tag.lower()
        if key.startswith("v"):
            key = key[1:]
        folders = table.setdefault(key, [])
        for li in node:
            if not isinstance(li.tag, str):
                continue
            text = (li.text or "").strip()
            folders.append("" if text in ("/", "\\") else text.replace("\\", "/"))
    return table


def _version_leq(version: Version, limit: Version | None) -> bool:
    return limit is None or version <= limit


def _load_folders_from_table(table: dict[str, list[str]], version: Version | None) -> list[str] | None:
    if version is not None:
        exact = table.get(format_version(version))
        if exact:
            return exact
    candidates = [
        key for key in table
        if key != "default" and "." in key and parse_version(key) is not None
        and _version_leq(parse_version(key), version)
    ]
    if candidates:
        return table[sorted(candidates, reverse=True)[0]]
    return table.get("default")


def _version_folder(mod_root: Path, version: Version | None) -> Path | None:
    if version is not None:
        exact = mod_root / format_version(version)
        if exact.is_dir():
            return exact
    found: dict[Version, Path] = {}
    for child in mod_root.iterdir():
        parsed = parse_version(child.name) if child.is_dir() else None
        if parsed is not None:
            found[parsed] = child
    best: Version = (0, 0)
    for candidate in sorted(found):
        beyond = version is not None and best > version
        if (candidate > best or beyond) and (_version_leq(candidate, version) or best[0] == 0):
            best = candidate
    return found.get(best) if best[0] > 0 else None


def load_folders(mod_root: Path, version: Version | None) -> list[Path]:
    load_folders_xml = mod_root / "LoadFolders.xml"
    if load_folders_xml.is_file():
        table = _parse_load_folders(load_folders_xml)
        if table:
            folders = _load_folders_from_table(table, version)
            if folders is not None:
                return list(dict.fromkeys(mod_root / f if f else mod_root for f in folders))
    out: list[Path] = []
    version_dir = _version_folder(mod_root, version)
    if version_dir is not None:
        out.append(version_dir)
    common = mod_root / "Common"
    if common.is_dir():
        out.append(common)
    out.append(mod_root)
    return out


def discover_mod_subfolders(source_mod: Path, name: str, version: Version | None = None) -> list[Path]:
    if not source_mod.is_dir():
        return []
    if is_mod_root(source_mod):
        roots = [folder / name for folder in load_folders(source_mod, version)]
        return list(dict.fromkeys(r.resolve() for r in roots if r.is_dir()))
    roots = [p.resolve() for p in source_mod.rglob(name) if p.is_dir() and any(p.rglob("*.xml"))]
    return sorted(set(roots), key=lambda p: str(p).lower())


def discover_defs_roots(source_mod: Path, version: Version | None = None) -> list[Path]:
    return discover_mod_subfolders(source_mod, "Defs", version)


def lang_root(target_mod: Path, target_lang: str) -> Path:
    return target_mod / "Languages" / target_lang


def definjected_root(target_mod: Path, target_lang: str) -> Path:
    return lang_root(target_mod, target_lang) / "DefInjected"
