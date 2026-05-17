from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings.

    Values are loaded from the .env file.
    Keeping all environment-based configuration here makes the app easier
    to deploy and safer to share publicly.
    """

    APP_NAME: str = "SimplifiQ Lead Automation"
    APP_ENV: str = "development"

    DATABASE_URL: str = "sqlite:///./simplifiq_leads.db"

    OPENAI_API_KEY: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    REPORT_OUTPUT_DIR: str = "generated_reports"

    GOOGLE_SHEETS_ENABLED: bool = False
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "google_service_account.json"
    GOOGLE_SHEET_ID: str = ""
    GOOGLE_SHEET_RANGE: str = "Leads!A:G"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()