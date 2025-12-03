import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

# Загружаем .env, если он есть
env_path = ROOT_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings:
    # ELM327
    elm_host: str = os.getenv("ELM327_HOST", "127.0.0.1")
    elm_port: int = int(os.getenv("ELM327_PORT", "35000"))
    elm_connect_timeout: float = float(os.getenv("ELM327_CONNECT_TIMEOUT", "5"))
    elm_read_timeout: float = float(os.getenv("ELM327_READ_TIMEOUT", "2"))

    # InfluxDB
    influx_url: str = os.getenv("INFLUX_URL", "http://influxdb:8086")
    influx_org: str = os.getenv("INFLUX_ORG", "obd-org")
    influx_bucket: str = os.getenv("INFLUX_BUCKET", "obd-telemetry")
    influx_token: str = os.getenv("INFLUX_TOKEN", "")
    influx_username: str = os.getenv("INFLUX_USERNAME", "obdadmin")
    influx_password: str = os.getenv("INFLUX_PASSWORD", "obdpassword")

    # App
    log_level: str = os.getenv("APP_LOG_LEVEL", "INFO")
    poll_interval_default: float = float(os.getenv("APP_POLL_INTERVAL_DEFAULT", "1.0"))
    profiles_dir: Path = Path(os.getenv("APP_PROFILE_DIR", "/app/profiles"))
    pids_config: Path = Path(os.getenv("APP_PIDS_CONFIG", "/app/config/pids/standard_mode01.json"))


settings = Settings()
