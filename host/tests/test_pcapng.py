import io
import unittest

from ble_sniffer.pcapng import PcapngWriter, read_packets


class PcapngTests(unittest.TestCase):
    def test_round_trip_preserves_timestamp_and_payload(self) -> None:
        stream = io.BytesIO()
        with PcapngWriter(stream) as writer:
            writer.write_packet(0x123456789, b"\x01\x02\x03")
        stream.seek(0)
        self.assertEqual(list(read_packets(stream))[0].timestamp_us, 0x123456789)
        stream.seek(0)
        self.assertEqual(list(read_packets(stream))[0].payload, b"\x01\x02\x03")

    def test_truncated_block_is_rejected(self) -> None:
        stream = io.BytesIO()
        with PcapngWriter(stream) as writer:
            writer.write_packet(1, b"\x01")
        with self.assertRaises(ValueError):
            list(read_packets(io.BytesIO(stream.getvalue()[:-1])))


if __name__ == "__main__":
    unittest.main()
