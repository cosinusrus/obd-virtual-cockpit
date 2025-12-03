import json
from pathlib import Path
from typing import Dict, List

from elm327_client import ELM327Client
from utils import parse_obd_response


async def scan_supported_pids_mode01(client: ELM327Client) -> Dict[str, List[str]]:
    """Примитивное сканирование поддерживаемых PID Mode 01.
    Для начала опрашиваем 0100, 0120, 0140, 0160 и т.д.
    Возвращаем словарь: { "01": ["0C", "0D", "05", ...] }
    """
    ranges = ["0100", "0120", "0140", "0160"]
    supported: List[int] = []
    for cmd in ranges:
        resp = await client.send_command(cmd)
        cleaned = parse_obd_response(resp)
        # TODO: корректно распарсить битовую маску. Пока — заглушка.
        # На реальных логах твоего мотоцикла реализуем точный парсер.
        # Здесь просто собираем список команд, на которые пришёл ответ.
        if cleaned:
            supported.append(int(cmd[2:], 16))

    # Возвращаем пустой каркас, чтобы не ломать логику.
    return {"01": []}


def load_pid_definitions(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data
