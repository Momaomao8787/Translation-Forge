from __future__ import annotations

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
    lines: list[str] = []
    if result.message_keys:
        lines.extend(tr.t(key, **params) for key, params in result.message_keys)
    elif result.messages:
        lines.extend(result.messages)
    if getattr(result, "warning_keys", None):
        lines.extend(tr.t(key, **params) for key, params in result.warning_keys)
    return "\n".join(lines)
