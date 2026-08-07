import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from ble_sniffer.cli import main
from ble_sniffer.diagnostics import CheckResult
from ble_sniffer.models import DeviceInfo


class CliTests(unittest.TestCase):
    @patch("ble_sniffer.cli.discover_devices", return_value=[DeviceInfo("ABC", "COM15", "Sniffer")])
    def test_devices_json(self, _discover: object) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["devices", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"port": "COM15"', output.getvalue())

    @patch("ble_sniffer.cli.run_doctor", return_value=[CheckResult("python", False, "old")])
    def test_doctor_failure_exit_code(self, _doctor: object) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["doctor"]), 1)


if __name__ == "__main__":
    unittest.main()
