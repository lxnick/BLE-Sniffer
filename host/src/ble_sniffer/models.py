"""Normalized data contracts at the device-adapter boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Phy(str, Enum):
    LE_1M = "le_1m"
    LE_2M = "le_2m"
    LE_CODED = "le_coded"


class Direction(str, Enum):
    MASTER_TO_SLAVE = "master_to_slave"
    SLAVE_TO_MASTER = "slave_to_master"


class CrcStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    stable_id: str
    port: str
    product: str
    firmware_version: str | None = None

    def __post_init__(self) -> None:
        if not self.stable_id.strip():
            raise ValueError("stable_id must not be empty")
        if not self.port.strip():
            raise ValueError("port must not be empty")


@dataclass(frozen=True, slots=True)
class CapturedFrame:
    host_timestamp_ns: int
    payload: bytes
    source_device_id: str
    sniffer_timestamp_us: int | None = None
    channel: int | None = None
    rssi_dbm: int | None = None
    phy: Phy | None = None
    crc_status: CrcStatus | None = None
    direction: Direction | None = None
    connection_event: int | None = None
    firmware_version: str | None = None

    def __post_init__(self) -> None:
        if self.host_timestamp_ns < 0:
            raise ValueError("host_timestamp_ns must be non-negative")
        if not self.payload:
            raise ValueError("payload must not be empty")
        if not self.source_device_id.strip():
            raise ValueError("source_device_id must not be empty")
        if self.channel is not None and not 0 <= self.channel <= 39:
            raise ValueError("channel must be between 0 and 39")

