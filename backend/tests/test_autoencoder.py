import numpy as np
from app.ai.autoencoder_model import AutoencoderAnomalyDetector


def test_normal_features_low_error():
    detector = AutoencoderAnomalyDetector()
    features = np.array([[5.0, 512.0, 3.0, 0.2]])
    error, is_anomaly = detector.is_anomaly(features)
    assert isinstance(error, float)


def test_extreme_features_flagged():
    detector = AutoencoderAnomalyDetector()
    features = np.array([[500.0, 8000.0, 50.0, 5.0]])
    error, is_anomaly = detector.is_anomaly(features)
    assert is_anomaly is True
