"""nRF Util device discovery and normalization."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from .models import DeviceInfo

RunCommand = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


class DeviceDiscoveryError(RuntimeError):
    pass


def find_nrfutil() -> str | None:
    if executable := shutil.which("nrfutil.exe") or shutil.which("nrfutil"):
        return executable
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    packages = Path(local_app_data, "Microsoft", "WinGet", "Packages")
    candidates = sorted(packages.glob("NordicSemiconductor.nrfutil_*/nrfutil.exe"))
    return str(candidates[0]) if candidates else None


def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)


def _extract_devices(output: str) -> list[dict[str, object]]:
    devices: list[dict[str, object]] | None = None
    for line in output.splitlines():
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        data = message.get("data", {})
        if message.get("type") == "info" and isinstance(data.get("devices"), list):
            devices = data["devices"]
        result = data.get("result")
        if isinstance(result, dict) and result.get("type") == "devices":
            result_data = result.get("data", {})
            if isinstance(result_data.get("devices"), list):
                devices = result_data["devices"]
    if devices is None:
        raise DeviceDiscoveryError("nrfutil returned no device result")
    return devices


def is_sniffer(raw: dict[str, object]) -> bool:
    usb = raw.get("usb")
    product = usb.get("product", "") if isinstance(usb, dict) else ""
    ports = raw.get("serialPorts", [])
    return "nRF Sniffer for Bluetooth LE" in str(product) or any(
        isinstance(port, dict)
        and port.get("vendorId") == "1915"
        and port.get("productId") == "522A"
        for port in ports
    )


def discover_devices(
    *, nrfutil: str | None = None, include_all: bool = False, runner: RunCommand = _run
) -> list[DeviceInfo]:
    executable = nrfutil or find_nrfutil()
    if not executable:
        raise DeviceDiscoveryError("nrfutil was not found")
    completed = runner([executable, "device", "list", "--json"])
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise DeviceDiscoveryError(f"nrfutil device list failed: {detail}")

    normalized: list[DeviceInfo] = []
    for raw in _extract_devices(completed.stdout):
        if not include_all and not is_sniffer(raw):
            continue
        ports = raw.get("serialPorts", [])
        port_names = [str(port["comName"]) for port in ports if isinstance(port, dict) and port.get("comName")]
        if not port_names:
            continue
        usb = raw.get("usb")
        product = usb.get("product", "Unknown USB device") if isinstance(usb, dict) else "Unknown USB device"
        stable_id = str(raw.get("serialNumber", "")).lstrip("0") or "0"
        normalized.append(DeviceInfo(stable_id, ",".join(port_names), str(product)))
    return sorted(normalized, key=lambda device: (device.product, device.stable_id))

