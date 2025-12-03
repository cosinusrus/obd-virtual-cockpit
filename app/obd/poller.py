import asyncio
from typing import Dict, Optional

from influxdb_client import InfluxDBClient, Point

from config import settings
from obd.elm327_client import ELM327Client
from obd.models import PollingConfig, PIDDefinition
from utils import parse_obd_response


class OBDPoller:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._config: Optional[PollingConfig] = None
        self._client: Optional[ELM327Client] = None
        self._influx: Optional[InfluxDBClient] = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def config(self) -> Optional[PollingConfig]:
        return self._config

    async def start(self, config: PollingConfig):
        if self.is_running:
            await self.stop()

        self._config = config
        self._client = ELM327Client(
            host=settings.elm_host,
            port=settings.elm_port,
            connect_timeout=settings.elm_connect_timeout,
            read_timeout=settings.elm_read_timeout,
        )
        await self._client.connect()
        await self._client.basic_init()

        self._influx = InfluxDBClient(
            url=settings.influx_url,
            token=settings.influx_token,
            org=settings.influx_org,
        )

        self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.close()
        if self._influx:
            self._influx.close()

        self._task = None
        self._config = None
        self._client = None
        self._influx = None

    async def _run(self):
        assert self._client is not None
        assert self._influx is not None
        assert self._config is not None

        write_api = self._influx.write_api()
        interval = self._config.interval or settings.poll_interval_default

        while True:
            for pid_full in self._config.pids:
                mode, pid = pid_full.split(":")
                cmd = f"{mode}{pid}"
                resp = await self._client.send_command(cmd)
                cleaned = parse_obd_response(resp)
                # TODO: распарсить значение. Сейчас пишем сырую строку.
                point = (
                    Point("obd_metrics")
                    .tag("vin", self._config.vin or "unknown")
                    .tag("mode", mode)
                    .tag("pid", pid)
                    .field("raw", cleaned)
                )
                write_api.write(
                    bucket=settings.influx_bucket,
                    org=settings.influx_org,
                    record=point,
                )
            await asyncio.sleep(interval)
