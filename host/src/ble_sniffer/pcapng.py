"""Small PCAPNG boundary used by adapters and deterministic tests."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from collections.abc import Iterator
from typing import BinaryIO

LINKTYPE_NORDIC_BLE = 272
_SHB = 0x0A0D0D0A
_IDB = 0x00000001
_EPB = 0x00000006


def _block(block_type: int, body: bytes) -> bytes:
    length = 12 + len(body)
    return struct.pack("<II", block_type, length) + body + struct.pack("<I", length)


class PcapngWriter:
    def __init__(self, stream: BinaryIO, *, snaplen: int = 0xFFFF) -> None:
        self._stream = stream
        self._closed = False
        self._stream.write(_block(_SHB, struct.pack("<IHHq", 0x1A2B3C4D, 1, 0, -1)))
        self._stream.write(_block(_IDB, struct.pack("<HHI", LINKTYPE_NORDIC_BLE, 0, snaplen)))

    def write_packet(self, timestamp_us: int, payload: bytes) -> None:
        if self._closed:
            raise ValueError("writer is closed")
        if timestamp_us < 0:
            raise ValueError("timestamp_us must be non-negative")
        if not payload:
            raise ValueError("payload must not be empty")
        padding = b"\0" * ((-len(payload)) % 4)
        body = struct.pack(
            "<IIIII", 0, timestamp_us >> 32, timestamp_us & 0xFFFFFFFF, len(payload), len(payload)
        )
        self._stream.write(_block(_EPB, body + payload + padding))

    def close(self) -> None:
        if not self._closed:
            self._stream.flush()
            self._closed = True

    def __enter__(self) -> PcapngWriter:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


@dataclass(frozen=True, slots=True)
class PcapngPacket:
    timestamp_us: int
    payload: bytes


def read_packets(stream: BinaryIO) -> Iterator[PcapngPacket]:
    while header := stream.read(8):
        if len(header) != 8:
            raise ValueError("truncated PCAPNG block header")
        block_type, length = struct.unpack("<II", header)
        if length < 12 or length % 4:
            raise ValueError("invalid PCAPNG block length")
        remainder = stream.read(length - 8)
        if len(remainder) != length - 8:
            raise ValueError("truncated PCAPNG block")
        if struct.unpack_from("<I", remainder, len(remainder) - 4)[0] != length:
            raise ValueError("PCAPNG block lengths do not match")
        if block_type == _EPB:
            interface_id, high, low, captured_len, packet_len = struct.unpack_from("<IIIII", remainder)
            if interface_id != 0 or captured_len != packet_len:
                raise ValueError("unsupported enhanced packet block")
            yield PcapngPacket((high << 32) | low, remainder[20 : 20 + captured_len])
