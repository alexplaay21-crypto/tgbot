from localization.loader import t


def test_known_key_ru():
    assert t("menu.my_account", "ru") == "👤 Мой аккаунт"


def test_known_key_en():
    assert t("menu.my_account", "en") == "👤 My Account"


def test_missing_key_falls_back_to_raw_key():
    assert t("nonexistent.key", "ru") == "nonexistent.key"


def test_unsupported_language_falls_back_to_default():
    assert t("menu.my_account", "fr") == t("menu.my_account", "ru")


def test_formatting():
    assert t("account.telegram", "ru", username="alex") == "Telegram: @alex"
