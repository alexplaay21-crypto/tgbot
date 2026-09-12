from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    BACKEND_URL: str
    BACKEND_SERVICE_TOKEN: str  # must equal Backend's BOT_INTERNAL_TOKEN

    CREATOR_IDS: str = ""
    ADMIN_IDS: str = ""

    GITHUB_URL: str = ""
    CORE_DOWNLOAD_URL: str = ""
    CORE_INSTALL_URL: str = ""
    TERMUX_GUIDE_URL: str = ""
    VPS_GUIDE_URL: str = ""

    TERMS_URL: str = ""
    PRIVACY_URL: str = ""
    EULA_URL: str = ""
    DOCUMENTS_URL: str = ""

    SUPPORT_URL: str = ""
    STORE_URL: str = ""

    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    @property
    def creator_ids(self) -> list[int]:
        return [int(x) for x in self.CREATOR_IDS.split(",") if x.strip()]

    @property
    def admin_ids(self) -> list[int]:
        return [int(x) for x in self.ADMIN_IDS.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
