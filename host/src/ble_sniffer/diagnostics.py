"""Host prerequisite checks used by the doctor command."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from .devices import DeviceDiscoveryError, discover_devices, find_nrfutil

RunCommand = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    passed: bool
    detail: str
    required: bool = True

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)


def _find_wireshark_tool(name: str) -> str | None:
    if executable := shutil.which(name):
        return executable
    for root in (r"C:\Program Files\Wireshark", r"C:\Program Files (x86)\Wireshark"):
        candidate = f"{root}\\{name}.exe"
        if Path(candidate).is_file():
            return candidate
    return None


def run_doctor(*, runner: RunCommand = _run) -> list[CheckResult]:
    checks = [
        CheckResult(
            "python",
            sys.version_info >= (3, 11),
            f"{platform.python_implementation()} {platform.python_version()}",
        )
    ]
    nrfutil = find_nrfutil()
    checks.append(CheckResult("nrfutil", nrfutil is not None, nrfutil or "not found"))
    if nrfutil:
        search = runner([nrfutil, "search"])
        output = search.stdout
        checks.append(CheckResult("nrfutil-device", search.returncode == 0 and "device" in output, "installed" if "device" in output else "not installed"))
        checks.append(CheckResult("nrfutil-ble-sniffer", search.returncode == 0 and "ble-sniffer" in output, "installed" if "ble-sniffer" in output else "not installed"))
        try:
            sniffers = discover_devices(nrfutil=nrfutil, runner=runner)
            detail = ", ".join(f"{item.stable_id} ({item.port})" for item in sniffers) or "none detected"
            checks.append(CheckResult("sniffer-device", bool(sniffers), detail))
        except DeviceDiscoveryError as error:
            checks.append(CheckResult("sniffer-device", False, str(error)))
    else:
        checks.extend(
            [
                CheckResult("nrfutil-device", False, "cannot check without nrfutil"),
                CheckResult("nrfutil-ble-sniffer", False, "cannot check without nrfutil"),
                CheckResult("sniffer-device", False, "cannot check without nrfutil"),
            ]
        )
    for name in ("wireshark", "tshark", "capinfos"):
        executable = _find_wireshark_tool(name)
        checks.append(CheckResult(name, executable is not None, executable or "not found"))
    return checks
