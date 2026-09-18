from app.ai.cheat_detector import CheatDetector


def test_normal_movement_not_flagged():
    detector = CheatDetector()
    detector.evaluate("player1", "move", {"x": 0, "y": 0}, timestamp=1000.0)
    signal = detector.evaluate("player1", "move", {"x": 1, "y": 1}, timestamp=1000.5)
    assert signal is None


def test_teleport_speed_flagged():
    detector = CheatDetector()
    detector.evaluate("player2", "move", {"x": 0, "y": 0}, timestamp=1000.0)
    signal = detector.evaluate("player2", "move", {"x": 9999, "y": 9999}, timestamp=1000.5)
    assert signal is not None
    assert signal.signal_type == "speed_hack"


def test_repeated_payload_flagged():
    detector = CheatDetector()
    payload = {"action": "fire"}
    detector.evaluate("player3", "shoot", payload, timestamp=2000.0)
    signal = detector.evaluate("player3", "shoot", payload, timestamp=2000.01)
    assert signal is not None
    assert signal.signal_type == "macro_bot_pattern"


def test_speed_check_skipped_for_subframe_updates():
    detector = CheatDetector()
    detector.evaluate("player4", "move", {"x": 0, "y": 0}, timestamp=3000.0)
    signal = detector.evaluate("player4", "move", {"x": 500, "y": 500}, timestamp=3000.005)
    assert signal is None
