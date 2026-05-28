import os
import tomllib
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


class Settings:
    def __init__(self, config_path: Path | None = None) -> None:
        path = Path(os.getenv("CONFIG_FILE") or config_path or DEFAULT_CONFIG_PATH)
        with path.open("rb") as f:
            data = tomllib.load(f)

        server = data.get("server", {})
        mysql = data.get("mysql", {})

        self.server_port: int = int(server.get("port", 8080))
        self.server_workers: int = int(server.get("workers", 1))

        self.mysql_url_override: str = mysql.get("url", "")
        self.mysql_host: str = mysql.get("host", "127.0.0.1")
        self.mysql_port: int = int(mysql.get("port", 3306))
        self.mysql_database: str = mysql.get("database", "api-svr")
        self.mysql_username: str = mysql.get("username", "root")
        self.mysql_password: str = mysql.get("password", "")
        self.mysql_pool_size: int = int(mysql.get("pool_size", 20))
        self.mysql_max_overflow: int = int(mysql.get("max_overflow", 40))
        self.mysql_pool_timeout: int = int(mysql.get("pool_timeout", 30))
        self.mysql_pool_recycle: int = int(mysql.get("pool_recycle", 1800))

    @property
    def mysql_url(self) -> str:
        if self.mysql_url_override != "":
            return self.mysql_url_override
        return (
            f"mysql+pymysql://{self.mysql_username}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )


settings = Settings()
