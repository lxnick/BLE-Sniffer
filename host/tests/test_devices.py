import json
import subprocess
import unittest

from ble_sniffer.devices import DeviceDiscoveryError, discover_devices


def completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, "failed" if returncode else "")


class DeviceDiscoveryTests(unittest.TestCase):
    def test_only_sniffer_is_returned_by_default(self) -> None:
        devices = [
            {
                "serialNumber": "C6C0",
                "serialPorts": [{"comName": "COM15", "vendorId": "1915", "productId": "522A"}],
                "usb": {"product": "nRF Sniffer for Bluetooth LE"},
            },
            {
                "serialNumber": "00105",
                "serialPorts": [{"comName": "COM8", "vendorId": "1366", "productId": "1061"}],
                "usb": {"product": "J-Link"},
            },
        ]
        line = json.dumps({"type": "info", "data": {"devices": devices}})
        result = discover_devices(nrfutil="nrfutil", runner=lambda _: completed(line))
        self.assertEqual([(item.stable_id, item.port) for item in result], [("C6C0", "COM15")])

    def test_all_includes_devkit_and_normalizes_leading_zeroes(self) -> None:
        devices = [
            {
                "serialNumber": "00105",
                "serialPorts": [{"comName": "COM8"}],
                "traits": {"devkit": True, "jlink": True},
                "usb": {"product": "J-Link"},
            },
            {
                "serialNumber": "STM32",
                "serialPorts": [{"comName": "COM4"}],
                "traits": {"devkit": False, "jlink": False, "nordicUsb": False},
                "usb": {"product": "STM32 Virtual ComPort"},
            },
        ]
        line = json.dumps({"type": "info", "data": {"devices": devices}})
        result = discover_devices(nrfutil="nrfutil", include_all=True, runner=lambda _: completed(line))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].stable_id, "105")

    def test_command_failure_is_reported(self) -> None:
        with self.assertRaises(DeviceDiscoveryError):
            discover_devices(nrfutil="nrfutil", runner=lambda _: completed("", 1))


if __name__ == "__main__":
    unittest.main()
