from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    
    # DATABASE
    # If using postgres
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "bot_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    
    # Or SQLite
    SQLITE_DB: str = "sqlite+aiosqlite:///./bot.db"
    USE_POSTGRES: bool = False

    # CHANNELS
    PUBLIC_CHANNEL_USERNAMES: str  # Comma separated list in env, parsed later or type List[str] if pydantic supports comma split automatically (it usually needs validator). Let's keep str and split.
    PRIVATE_GROUP_ID: int         # ex: -100xxxxxxxxxx

    # PAYMENTS
    PROVIDER_TOKEN: str           # From @BotFather
    CURRENCY: str = "UZS"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
