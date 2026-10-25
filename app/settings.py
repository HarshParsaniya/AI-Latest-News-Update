from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )

    gemini_api_key: str = ""
    groq_api_key: str = ""
    model_name: str = "gemini-2.0-flash"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_app_password: str = ""
    digest_from_email: str = ""
    digest_to_email: str = ""

    whatsapp_enabled: bool = False
    callmebot_phone: str = ""
    callmebot_apikey: str = ""
    callmebot_max_chars: int = 1500

    digest_tz: str = "Asia/Kolkata"
    target_item_count: int = Field(default=10, ge=1, le=30)
    sqlite_path: Path = Path("./data/digest.db")
    dry_run: bool = False
    extract_article_text: bool = False

    @property
    def email_recipients(self) -> list[str]:
        return [part.strip() for part in self.digest_to_email.split(",") if part.strip()]

    @property
    def smtp_ready(self) -> bool:
        return bool(
            self.smtp_host
            and self.smtp_user
            and self.smtp_app_password
            and self.email_recipients
        )

    @property
    def whatsapp_ready(self) -> bool:
        return bool(
            self.whatsapp_enabled and self.callmebot_phone and self.callmebot_apikey
        )

    @property
    def langfuse_ready(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def from_address(self) -> str:
        return self.digest_from_email or self.smtp_user


@lru_cache
def get_settings() -> Settings:
    return Settings()
