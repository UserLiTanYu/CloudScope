from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CloudScope"
    environment: str = "development"
    log_level: str = "INFO"
    log_dir: Path = Path("../logs")

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "cloudscope"
    mysql_password: str = "cloudscope"
    mysql_database: str = "cloudscope"

    source_data_dir: Path = Path(r"C:\Users\litan\Desktop\code\可视化大屏\数据")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def database_url(self) -> str:
        return (
            "mysql+pymysql://"
            f"{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
