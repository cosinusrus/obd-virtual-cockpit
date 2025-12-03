from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class PIDDefinition(BaseModel):
    mode: str
    pid: str
    name: str
    description: str
    unit: str
    formula: str  # строка с формулой, например: "((A*256)+B)/4"


class VehicleProfile(BaseModel):
    vin: str
    created_at: datetime
    updated_at: datetime
    ecus: List[str]
    supported_pids: Dict[str, List[str]]  # mode -> [pid_hex,...]


class PollingConfig(BaseModel):
    vin: Optional[str] = None
    pids: List[str]  # список строк вида "01:0C"
    interval: float  # сек


class StatusResponse(BaseModel):
    elm_connected: bool
    elm_error: Optional[str] = None
    influx_connected: bool
    influx_error: Optional[str] = None
    active_profile: Optional[str] = None
    polling_active: bool
    polling_config: Optional[PollingConfig] = None
