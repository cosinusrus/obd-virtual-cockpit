import asyncio
from typing import Optional

import httpx

# Для простоты используем TCP поверх asyncio.open_connection
# (httpx тут не требуется, оставлен как возможный клиент для REST-проксей)


class ELM327Client:
    def __init__(self, host: str, port: int, connect_timeout: float = 5.0, read_timeout: float = 2.0):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def connect(self):
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=self.connect_timeout
        )

    async def close(self):
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None

    async def write_line(self, cmd: str):
        if not cmd.endswith("\r"):
            cmd += "\r"
        if not self._writer:
            raise RuntimeError("ELM327 not connected")
        self._writer.write(cmd.encode("ascii"))
        await self._writer.drain()

    async def read_until_prompt(self) -> str:
        if not self._reader:
            raise RuntimeError("ELM327 not connected")
        data = b""
        while True:
            try:
                chunk = await asyncio.wait_for(self._reader.read(64), timeout=self.read_timeout)
            except asyncio.TimeoutError:
                break
            if not chunk:
                break
            data += chunk
            if b">" in chunk:
                break
        return data.decode(errors="ignore")

    async def send_command(self, cmd: str) -> str:
        await self.write_line(cmd)
        return await self.read_until_prompt()

    async def basic_init(self) -> str:
        """Минимальный набор AT-команд для инициализации."""
        out = []
        for c in ["ATZ", "ATE0", "ATL0", "ATS0", "ATH1", "ATI"]:
            out.append(f"$ {c}")
            resp = await self.send_command(c)
            out.append(resp)
        return "\n".join(out)
