import unittest

from ble_sniffer.models import CapturedFrame, DeviceInfo


class ModelTests(unittest.TestCase):
    def test_unknown_metadata_remains_none(self) -> None:
        frame = CapturedFrame(1, b"\x01", "dongle-1")
        self.assertIsNone(frame.channel)
        self.assertIsNone(frame.direction)

    def test_invalid_channel_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CapturedFrame(1, b"\x01", "dongle-1", channel=40)

    def test_device_requires_stable_identity(self) -> None:
        with self.assertRaises(ValueError):
            DeviceInfo("", "COM15", "nRF Sniffer")


if __name__ == "__main__":
    unittest.main()

