from locales import en, ru

SUPPORTED_LANGS: dict[str, dict[str, str]] = {
    "ru": ru.STRINGS,
    "en": en.STRINGS,
}
DEFAULT_LANG = "en"


def get_text(key: str, lang: str, **kwargs) -> str:
    strings = SUPPORTED_LANGS.get(lang, SUPPORTED_LANGS[DEFAULT_LANG])
    template = strings.get(key) or SUPPORTED_LANGS[DEFAULT_LANG].get(key) or key
    return template.format(**kwargs) if kwargs else template


def detect_lang(telegram_language_code: str | None) -> str:
    if not telegram_language_code:
        return DEFAULT_LANG
    prefix = telegram_language_code.split("-")[0].lower()
    return prefix if prefix in SUPPORTED_LANGS else DEFAULT_LANG
