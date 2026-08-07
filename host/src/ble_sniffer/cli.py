"""CLI entry point; commands are added incrementally during M1."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ble-sniffer")
    parser.add_argument("--version", action="version", version="ble-sniffer 0.1.0")
    parser.parse_args(argv)
    return 0

