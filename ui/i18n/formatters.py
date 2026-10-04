from __future__ import annotations

from core.errors import format_warning
from ui.i18n.translator import Translator


def format_error(result, tr: Translator) -> str:
    if getattr(result, "error_key", None):
        msg = tr.t(result.error_key, **getattr(result, "error_params", {}))
        hint_key = f"{result.error_key}_hint"
        hint = tr.t(hint_key)
        if hint != hint_key:
            return f"{msg}\n{hint}"
        return msg
    if getattr(result, "error", ""):
        return result.error
    return tr.t("err.unknown")


def format_check_messages(result, tr: Translator) -> str:
    if result.message_keys:
        messages = [tr.t(key, **params) for key, params in result.message_keys]
    else:
        messages = list(result.messages)
    lines = [tr.t("msg.check.heading_result")]
    lines.extend(f"• {text}" for text in messages)
    warnings = [format_warning(tr.t, key, params) for key, params in getattr(result, "warning_keys", [])]
    if warnings:
        lines.extend(["", tr.t("msg.check.heading_warnings")])
        lines.extend(f"• {text}" for text in warnings)
    return "\n".join(lines)
