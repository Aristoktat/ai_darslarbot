from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator
import json

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    
    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[str, List[int]]) -> List[int]:
        if isinstance(v, str):
            try:
                # Try JSON parse first (for [123, 456])
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback to comma split (for 123,456)
                return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

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

    # WEB SERVER (for keep-alive)
    PORT: int = 8080

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
