import json
import subprocess
import unittest
from unittest.mock import patch

from ble_sniffer.diagnostics import run_doctor


class DoctorTests(unittest.TestCase):
    @patch("ble_sniffer.diagnostics._find_wireshark_tool", return_value=None)
    @patch("ble_sniffer.diagnostics.find_nrfutil", return_value=None)
    def test_missing_tools_fail_required_checks(self, _nrfutil: object, _wireshark: object) -> None:
        failures = {check.name for check in run_doctor() if not check.passed}
        self.assertIn("nrfutil", failures)
        self.assertIn("sniffer-device", failures)
        self.assertIn("tshark", failures)

    @patch("ble_sniffer.diagnostics._find_wireshark_tool", return_value="tool.exe")
    @patch("ble_sniffer.diagnostics.find_nrfutil", return_value="nrfutil.exe")
    def test_healthy_toolchain_passes(self, _nrfutil: object, _wireshark: object) -> None:
        device = {
            "serialNumber": "ABC",
            "serialPorts": [{"comName": "COM15", "vendorId": "1915", "productId": "522A"}],
            "usb": {"product": "nRF Sniffer for Bluetooth LE"},
        }

        def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
            if command[-1] == "search":
                return subprocess.CompletedProcess(command, 0, "device 1.0 Installed\nble-sniffer 1.0 Installed", "")
            line = json.dumps({"type": "info", "data": {"devices": [device]}})
            return subprocess.CompletedProcess(command, 0, line, "")

        self.assertTrue(all(check.passed for check in run_doctor(runner=runner)))


if __name__ == "__main__":
    unittest.main()
