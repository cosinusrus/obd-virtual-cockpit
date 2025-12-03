import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from .config import settings
from .obd.elm327_client import ELM327Client
from .obd.models import PollingConfig, StatusResponse
from .obd.pid_scanner import load_pid_definitions, scan_supported_pids_mode01
from .obd.vin_profile import create_or_update_profile, read_vin
from .obd.poller import OBDPoller

from influxdb_client import InfluxDBClient


app = FastAPI(title="OBD Virtual Cockpit")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web" / "static")), name="static")

poller = OBDPoller()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/status", response_model=StatusResponse)
async def api_status():
    # Проверяем ELM
    elm_ok = False
    elm_err: Optional[str] = None
    client = ELM327Client(
        host=settings.elm_host,
        port=settings.elm_port,
        connect_timeout=settings.elm_connect_timeout,
        read_timeout=settings.elm_read_timeout,
    )
    try:
        await client.connect()
        resp = await client.send_command("ATZ")
        if resp:
            elm_ok = True
    except Exception as e:
        elm_err = str(e)
    finally:
        try:
            await client.close()
        except Exception:
            pass

    # Проверяем Influx
    influx_ok = False
    influx_err: Optional[str] = None
    try:
        influx = InfluxDBClient(
            url=settings.influx_url,
            token=settings.influx_token,
            org=settings.influx_org,
        )
        _ = influx.health()
        influx_ok = True
        influx.close()
    except Exception as e:
        influx_err = str(e)

    return StatusResponse(
        elm_connected=elm_ok,
        elm_error=elm_err,
        influx_connected=influx_ok,
        influx_error=influx_err,
        active_profile=None,
        polling_active=poller.is_running,
        polling_config=poller.config,
    )


@app.post("/api/elm/init")
async def api_elm_init():
    client = ELM327Client(
        host=settings.elm_host,
        port=settings.elm_port,
        connect_timeout=settings.elm_connect_timeout,
        read_timeout=settings.elm_read_timeout,
    )
    try:
        await client.connect()
        out = await client.basic_init()
        return {"ok": True, "log": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            await client.close()
        except Exception:
            pass


@app.get("/api/vin/read")
async def api_read_vin():
    client = ELM327Client(
        host=settings.elm_host,
        port=settings.elm_port,
        connect_timeout=settings.elm_connect_timeout,
        read_timeout=settings.elm_read_timeout,
    )
    try:
        await client.connect()
        vin_raw = await read_vin(client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            await client.close()
        except Exception:
            pass

    if not vin_raw:
        raise HTTPException(status_code=500, detail="VIN not detected (raw response empty)")

    profile = create_or_update_profile(settings.profiles_dir, vin_raw, supported_pids=None, ecus=None)
    return {"vin": vin_raw, "profile": profile}


@app.post("/api/pids/scan")
async def api_scan_pids():
    client = ELM327Client(
        host=settings.elm_host,
        port=settings.elm_port,
        connect_timeout=settings.elm_connect_timeout,
        read_timeout=settings.elm_read_timeout,
    )
    try:
        await client.connect()
        supported = await scan_supported_pids_mode01(client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            await client.close()
        except Exception:
            pass

    return supported


@app.post("/api/polling/start")
async def api_polling_start(config: PollingConfig):
    try:
        await poller.start(config)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/polling/stop")
async def api_polling_stop():
    await poller.stop()
    return {"ok": True}


@app.post("/api/command")
async def api_command(command: str):
    client = ELM327Client(
        host=settings.elm_host,
        port=settings.elm_port,
        connect_timeout=settings.elm_connect_timeout,
        read_timeout=settings.elm_read_timeout,
    )
    try:
        await client.connect()
        resp = await client.send_command(command)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            await client.close()
        except Exception:
            pass

    return {"command": command, "response": resp}
