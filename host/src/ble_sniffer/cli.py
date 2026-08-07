"""CLI entry point; commands are added incrementally during M1."""

from __future__ import annotations

import argparse
import json
import sys

from .devices import DeviceDiscoveryError, discover_devices
from .diagnostics import run_doctor


def _print_devices(*, include_all: bool, as_json: bool) -> int:
    try:
        devices = discover_devices(include_all=include_all)
    except DeviceDiscoveryError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    rows = [
        {"id": item.stable_id, "port": item.port, "product": item.product}
        for item in devices
    ]
    if as_json:
        print(json.dumps({"devices": rows}, indent=2))
    elif rows:
        print(f"{'ID':<18} {'PORT':<12} PRODUCT")
        for row in rows:
            print(f"{row['id']:<18} {row['port']:<12} {row['product']}")
    else:
        print("No compatible BLE sniffer found.")
    return 0 if rows else 3


def _print_doctor(*, as_json: bool) -> int:
    checks = run_doctor()
    if as_json:
        print(json.dumps({"checks": [check.as_dict() for check in checks]}, indent=2))
    else:
        for check in checks:
            status = "PASS" if check.passed else "FAIL"
            print(f"{status:<4} {check.name:<22} {check.detail}")
        passed = sum(check.passed for check in checks)
        print(f"\nRequired checks: {passed}/{len(checks)} passed")
    return 0 if all(check.passed or not check.required for check in checks) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ble-sniffer")
    parser.add_argument("--version", action="version", version="ble-sniffer 0.1.0")
    subparsers = parser.add_subparsers(dest="command", required=True)
    devices_parser = subparsers.add_parser("devices", help="list BLE sniffer devices")
    devices_parser.add_argument("--all", action="store_true", help="include Nordic EVKs")
    devices_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    doctor_parser = subparsers.add_parser("doctor", help="check host prerequisites")
    doctor_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    if args.command == "devices":
        return _print_devices(include_all=args.all, as_json=args.json)
    return _print_doctor(as_json=args.json)
