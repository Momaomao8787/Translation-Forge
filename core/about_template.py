from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from core.meta import APP_DISPLAY_NAME
from core.models import LANG_PACKAGE_SUFFIX
from core.path_suggest import basename_for_source, lang_package_suffix, sanitize_basename


def _text(el: ET.Element | None) -> str:
    if el is not None and el.text:
        return el.text.strip()
    return ""


def read_source_about(source_mod: Path) -> dict:
    about_path = source_mod / "About" / "About.xml"
    if not about_path.is_file():
        return {}
    try:
        root = ET.parse(about_path).getroot()
    except ET.ParseError:
        return {}
    data: dict = {
        "name": _text(root.find("name")),
        "packageId": _text(root.find("packageId")),
        "author": _text(root.find("author")),
    }
    versions: list[str] = []
    sv = root.find("supportedVersions")
    if sv is not None:
        for li in sv.findall("li"):
            if li.text and li.text.strip():
                versions.append(li.text.strip())
    data["supportedVersions"] = versions
    deps: list[dict[str, str]] = []
    md = root.find("modDependencies")
    if md is not None:
        for li in md.findall("li"):
            pid = _text(li.find("packageId"))
            if not pid:
                continue
            deps.append(
                {
                    "packageId": pid,
                    "displayName": _text(li.find("displayName")) or _text(root.find("name")),
                    "steamWorkshopUrl": _text(li.find("steamWorkshopUrl")),
                }
            )
    data["modDependencies"] = deps
    load_after: list[str] = []
    la = root.find("loadAfter")
    if la is not None:
        for li in la.findall("li"):
            if li.text and li.text.strip():
                load_after.append(li.text.strip())
    data["loadAfter"] = load_after
    return data


def default_package_id(source_mod: Path, lang: str, suffix_override: str = "") -> str:
    about = read_source_about(source_mod)
    source_pid = about.get("packageId", "")
    suffix = (suffix_override or lang_package_suffix(lang)).strip()
    suffix = "".join(c for c in suffix if c.isalnum() or c == ".")
    if source_pid:
        base = source_pid.rstrip(".")
        return f"{base}.{suffix}" if suffix else base
    folder = sanitize_basename(source_mod.name)
    return f"Unknown.{folder}.{suffix}" if suffix else f"Unknown.{folder}"


def default_about_name(target_mod: Path) -> str:
    return target_mod.name


def default_description(app_title: str | None = None) -> str:
    title = (app_title or APP_DISPLAY_NAME).strip()
    return f"本模組使用 {title} 完成"


def build_about_fields(
    source_mod: Path,
    target_mod: Path,
    lang: str,
    *,
    about_name: str = "",
    package_id: str = "",
    package_id_suffix: str = "",
    description: str = "",
    load_after: list[str] | None = None,
    supported_versions: list[str] | None = None,
    app_title: str | None = None,
) -> dict:
    about = read_source_about(source_mod)
    source_pid = about.get("packageId", "")
    name = (about_name or default_about_name(target_mod)).strip()
    pid = (package_id or default_package_id(source_mod, lang, package_id_suffix)).strip()
    desc = (description or default_description(app_title)).strip()
    versions = list(supported_versions if supported_versions is not None else about.get("supportedVersions", []))
    la = list(load_after if load_after is not None else [])
    if not la and source_pid:
        la = [source_pid]
    dep_pid = source_pid
    dep_name = about.get("name") or basename_for_source(source_mod)
    dep_url = ""
    deps = about.get("modDependencies") or []
    if deps:
        dep_pid = deps[0].get("packageId", dep_pid)
        dep_name = deps[0].get("displayName", dep_name)
        dep_url = deps[0].get("steamWorkshopUrl", "")
    elif source_pid:
        deps = [{"packageId": source_pid, "displayName": dep_name, "steamWorkshopUrl": ""}]
    else:
        deps = []
    return {
        "name": name,
        "packageId": pid,
        "description": desc,
        "supportedVersions": versions,
        "loadAfter": la,
        "modDependencies": deps,
        "dependencyPackageId": dep_pid,
        "dependencyDisplayName": dep_name,
        "dependencyWorkshopUrl": dep_url,
    }


def write_about_xml(target_mod: Path, fields: dict) -> Path:
    about_dir = target_mod / "About"
    about_dir.mkdir(parents=True, exist_ok=True)
    path = about_dir / "About.xml"
    root = ET.Element("ModMetaData")
    ET.SubElement(root, "name").text = fields.get("name", "")
    pid = fields.get("packageId", "")
    if pid:
        ET.SubElement(root, "packageId").text = pid
    desc = fields.get("description", "")
    if desc:
        ET.SubElement(root, "description").text = desc
    versions = fields.get("supportedVersions") or []
    if versions:
        sv = ET.SubElement(root, "supportedVersions")
        for v in versions:
            ET.SubElement(sv, "li").text = v
    deps = fields.get("modDependencies") or []
    if deps:
        md = ET.SubElement(root, "modDependencies")
        for dep in deps:
            li = ET.SubElement(md, "li")
            if dep.get("packageId"):
                ET.SubElement(li, "packageId").text = dep["packageId"]
            if dep.get("displayName"):
                ET.SubElement(li, "displayName").text = dep["displayName"]
            if dep.get("steamWorkshopUrl"):
                ET.SubElement(li, "steamWorkshopUrl").text = dep["steamWorkshopUrl"]
    la_list = fields.get("loadAfter") or []
    if la_list:
        la = ET.SubElement(root, "loadAfter")
        for item in la_list:
            ET.SubElement(la, "li").text = item
    xml_body = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(f'<?xml version="1.0" encoding="utf-8"?>{xml_body}').toprettyxml(
        indent="\t", encoding="utf-8"
    )
    path.write_bytes(pretty)
    return path
