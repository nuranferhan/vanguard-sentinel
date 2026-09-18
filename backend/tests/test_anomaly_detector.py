from app.ai.anomaly_detector import AnomalyDetector


def test_normal_traffic_score_is_float():
    detector = AnomalyDetector()
    for _ in range(5):
        score, is_anomaly = detector.score("10.0.0.1", "/player/action", 512)
    assert isinstance(score, float)


def test_burst_traffic_flagged_eventually():
    detector = AnomalyDetector()
    flagged = False
    for _ in range(300):
        score, is_anomaly = detector.score("10.0.0.2", "/player/action", 64)
        if is_anomaly:
            flagged = True
            break
    assert flagged is True
