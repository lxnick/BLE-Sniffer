import unittest

from ble_sniffer.session import CaptureSession, CaptureState


class CaptureSessionTests(unittest.TestCase):
    def test_happy_path(self) -> None:
        session = CaptureSession()
        for state in (
            CaptureState.OPENING,
            CaptureState.READY,
            CaptureState.CAPTURING,
            CaptureState.STOPPING,
            CaptureState.CLOSED,
        ):
            session.transition(state)
        self.assertEqual(session.state, CaptureState.CLOSED)

    def test_disconnect_during_capture_is_partial_failure(self) -> None:
        session = CaptureSession()
        session.transition(CaptureState.OPENING)
        session.transition(CaptureState.READY)
        session.transition(CaptureState.CAPTURING)
        session.fail("dongle disconnected", partial=True)
        self.assertEqual(session.state, CaptureState.FAILED)
        self.assertTrue(session.partial)

    def test_invalid_transition_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CaptureSession().transition(CaptureState.CAPTURING)


if __name__ == "__main__":
    unittest.main()

