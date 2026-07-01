from __future__ import annotations

import re
from pathlib import Path


def default_prefix(source_mod_path: str | Path) -> str:
    name = Path(source_mod_path).name
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.replace(" ", "_").strip("_")
    return name or "Mod"
