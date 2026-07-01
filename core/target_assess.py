from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.export_merge import default_single_pending_path
from core.paths import definjected_root, lang_root


@dataclass
class TargetAssessResult:
    target_exists: bool
    about_exists: bool
    lang_path_exists: bool
    definjected_xml_count: int
    pending_file_exists: bool

    @property
    def needs_repeat_confirm(self) -> bool:
        if not self.target_exists:
            return False
        return self.about_exists or self.definjected_xml_count > 0 or self.pending_file_exists


def assess_existing_target(target_mod: Path, lang: str) -> TargetAssessResult:
    target_exists = target_mod.is_dir()
    about_exists = (target_mod / "About" / "About.xml").is_file()
    lr = lang_root(target_mod, lang)
    lang_path_exists = lr.is_dir()
    di_root = definjected_root(target_mod, lang)
    definjected_xml_count = len(list(di_root.rglob("*.xml"))) if di_root.is_dir() else 0
    pending_file_exists = any(
        default_single_pending_path(target_mod, fmt).is_file() for fmt in ("csv", "xml")
    )
    return TargetAssessResult(
        target_exists=target_exists,
        about_exists=about_exists,
        lang_path_exists=lang_path_exists,
        definjected_xml_count=definjected_xml_count,
        pending_file_exists=pending_file_exists,
    )
