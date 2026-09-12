import json
from functools import lru_cache
from pathlib import Path

_LOCALES_DIR = Path(__file__).parent
_SUPPORTED = ("ru", "en")
_DEFAULT = "ru"


@lru_cache
def _load(lang: str) -> dict:
    path = _LOCALES_DIR / f"{lang}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def t(key: str, lang: str | None, **kwargs) -> str:
    """Dotted-key lookup, e.g. t('menu.help', 'ru')."""
    lang = lang if lang in _SUPPORTED else _DEFAULT
    node = _load(lang)
    for part in key.split("."):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    if not isinstance(node, str):
        if lang != _DEFAULT:
            return t(key, _DEFAULT, **kwargs)
        return key
    return node.format(**kwargs) if kwargs else node
