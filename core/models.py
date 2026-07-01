from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_FIELDS = (
    "label",
    "description",
    "title",
    "titleShort",
    "labelPlural",
    "pawnSingular",
    "pawnsPlural",
    "leaderTitle",
    "labelNoun",
    "jobString",
    "verbString",
    "gerundive",
    "reportString",
    "inspectString",
    "letterLabel",
    "letterText",
    "deathMessage",
    "deathMessageFemale",
    "helpText",
)

DEFAULT_EXPORT_BASENAME = "DefInjected-missing"

COMMON_LANGUAGES = (
    "ChineseTraditional",
    "ChineseSimplified",
    "English",
    "Japanese",
    "Korean",
    "Russian",
    "French",
    "German",
    "Spanish",
)

RIMWORLD_LANGUAGES = COMMON_LANGUAGES + (
    "Italian",
    "PortugueseBrazilian",
    "Polish",
    "Czech",
    "Turkish",
    "Ukrainian",
)

LANG_PACKAGE_SUFFIX: dict[str, str] = {
    "ChineseTraditional": "TC",
    "ChineseSimplified": "ZH",
    "Japanese": "JP",
    "Korean": "KO",
    "English": "EN",
    "Russian": "RU",
    "French": "FR",
    "German": "DE",
    "Spanish": "ES",
    "Italian": "IT",
    "PortugueseBrazilian": "PTBR",
    "Polish": "PL",
    "Czech": "CS",
    "Turkish": "TR",
    "Ukrainian": "UK",
}

WORK_MODE_MAINTAIN = "maintain"
WORK_MODE_SCAFFOLD = "scaffold"
WORK_MODE_SETTINGS = "settings"

SCAFFOLD_PLACEHOLDER_TODO = "todo"
SCAFFOLD_PLACEHOLDER_EMPTY = "empty"
SCAFFOLD_PLACEHOLDER_SOURCE = "source"

EXPORT_LAYOUT_SINGLE = "single"
EXPORT_LAYOUT_BY_SOURCE = "by_source"

EXPORT_PLACEHOLDER_EMPTY = "empty"
EXPORT_PLACEHOLDER_TODO = "todo"
EXPORT_PLACEHOLDER_SOURCE = "source"

WRITE_MODE_MERGE_EXISTING = "merge_existing"
WRITE_MODE_NEW_FILE = "new_file"


@dataclass
class ProjectConfig:
    source_mod: Path
    target_mod: Path
    target_lang: str


@dataclass
class DefRecord:
    def_name: str
    def_type: str
    source_rel: str
    source_def_file: str
    fields: dict[str, str]


@dataclass
class PendingEntry:
    def_name: str
    def_type: str
    field: str
    source_text: str
    translation: str
    source_def_file: str


@dataclass
class CheckResult:
    ok: bool
    defs_roots: list[str] = field(default_factory=list)
    lang_path: str = ""
    lang_will_create: bool = False
    pending_count: int = 0
    duplicate_def_names: list[str] = field(default_factory=list)
    leaf_collisions: list[str] = field(default_factory=list)
    duplicate_tags: list[str] = field(default_factory=list)
    write_strategy_mix: list[str] = field(default_factory=list)
    strategy_hints: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    message_keys: list[tuple[str, dict]] = field(default_factory=list)
    warning_keys: list[tuple[str, dict]] = field(default_factory=list)
    error: str = ""
    error_key: str | None = None
    error_params: dict = field(default_factory=dict)


@dataclass
class ExportResult:
    ok: bool
    output_path: str = ""
    entry_count: int = 0
    meta_path: str = ""
    warnings: list[str] = field(default_factory=list)
    warning_keys: list[tuple[str, dict]] = field(default_factory=list)
    error: str = ""
    error_key: str | None = None
    error_params: dict = field(default_factory=dict)


@dataclass
class ExportOptions:
    layout: str = EXPORT_LAYOUT_SINGLE
    placeholder: str = EXPORT_PLACEHOLDER_TODO
    write_mode: str = WRITE_MODE_MERGE_EXISTING
    prefix: str = ""
    fmt: str = "csv"


@dataclass
class ScaffoldOptions:
    create_about: bool = True
    about_name: str = ""
    package_id: str = ""
    package_id_suffix: str = ""
    about_description: str = ""
    load_after: list[str] = field(default_factory=list)
    supported_versions: list[str] = field(default_factory=list)


@dataclass
class ScaffoldPreview:
    ok: bool
    target_path: str = ""
    lang_path: str = ""
    def_count: int = 0
    def_types: list[str] = field(default_factory=list)
    create_about: bool = False
    about_path: str = ""
    warnings: list[str] = field(default_factory=list)
    warning_keys: list[tuple[str, dict]] = field(default_factory=list)
    error: str = ""
    error_key: str | None = None
    error_params: dict = field(default_factory=dict)


@dataclass
class ScaffoldResult:
    ok: bool
    target_mod_path: str = ""
    lang_path: str = ""
    files_created: int = 0
    entries_written: int = 0
    about_created: bool = False
    warnings: list[str] = field(default_factory=list)
    warning_keys: list[tuple[str, dict]] = field(default_factory=list)
    error: str = ""
    error_key: str | None = None
    error_params: dict = field(default_factory=dict)


@dataclass
class ImportResult:
    ok: bool
    written: int = 0
    skipped: int = 0
    updated: int = 0
    files_created: int = 0
    target_lang_path: str = ""
    warnings: list[str] = field(default_factory=list)
    error: str = ""
    error_key: str | None = None
    error_params: dict = field(default_factory=dict)
