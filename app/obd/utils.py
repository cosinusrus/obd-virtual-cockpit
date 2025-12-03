from typing import List


def parse_obd_response(line: str) -> str:
    """Базовая чистка строки ответа ELM (обрезка промпта, CR/LF)."""
    return line.strip().replace(">", "")


def split_bytes(hex_str: str) -> List[int]:
    """"7E8 03 41 0C 1A F8" -> [0x03, 0x41, 0x0C, 0x1A, 0xF8]"""
    parts = hex_str.split()
    return [int(p, 16) for p in parts if all(c in "0123456789ABCDEFabcdef" for c in p)]
