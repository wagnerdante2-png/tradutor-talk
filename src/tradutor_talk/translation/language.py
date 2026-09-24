SUPPORTED_INITIAL_LANGUAGES = {
    "pt-BR": "Português (Brasil)",
    "en-US": "English (United States)",
}

PLANNED_LANGUAGES = {
    "es-ES": "Español",
    "ja-JP": "日本語",
    "zh-CN": "简体中文",
}


def validate_language(code: str, *, allow_planned: bool = False) -> str:
    accepted = set(SUPPORTED_INITIAL_LANGUAGES)
    if allow_planned:
        accepted.update(PLANNED_LANGUAGES)
    if code not in accepted:
        raise ValueError(f"unsupported language code: {code}")
    return code
