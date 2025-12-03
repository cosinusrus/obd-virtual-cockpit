import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import VehicleProfile
from .elm327_client import ELM327Client
from .utils import parse_obd_response


async def read_vin(client: ELM327Client) -> Optional[str]:
    """Чтение VIN по Mode 09 PID 02 (если поддерживается)."""
    # Стандартный запрос: 09 02
    resp = await client.send_command("0902")
    cleaned = parse_obd_response(resp)
    # Здесь можно реализовать полноценный парсер ISO-TP / 09 02,
    # пока оставляем заглушку и возвращаем сырую строку.
    # Для твоего мотоцикла позже сделаем точный разбор.
    return cleaned or None


def load_profile(profiles_dir: Path, vin: str) -> Optional[VehicleProfile]:
    path = profiles_dir / f"{vin}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return VehicleProfile(**data)


def save_profile(profiles_dir: Path, profile: VehicleProfile) -> None:
    profiles_dir.mkdir(parents=True, exist_ok=True)
    path = profiles_dir / f"{profile.vin}.json"
    path.write_text(profile.model_dump_json(indent=2, by_alias=True), encoding="utf-8")


def create_or_update_profile(
    profiles_dir: Path,
    vin: str,
    supported_pids: Optional[dict] = None,
    ecus: Optional[list] = None,
) -> VehicleProfile:
    existing = load_profile(profiles_dir, vin)
    now = datetime.utcnow()
    if existing:
        existing.updated_at = now
        if supported_pids:
            existing.supported_pids = supported_pids
        if ecus:
            existing.ecus = ecus
        save_profile(profiles_dir, existing)
        return existing

    profile = VehicleProfile(
        vin=vin,
        created_at=now,
        updated_at=now,
        ecus=ecus or [],
        supported_pids=supported_pids or {},
    )
    save_profile(profiles_dir, profile)
    return profile
