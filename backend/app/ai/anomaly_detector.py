import os
import time
import numpy as np
import joblib
from collections import deque, defaultdict
from sklearn.ensemble import IsolationForest
from app.config import settings


class AnomalyDetector:


    def __init__(self):
        self._history: dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self._model: IsolationForest | None = None
        self._load_or_bootstrap_model()

    def _load_or_bootstrap_model(self):
        os.makedirs(os.path.dirname(settings.anomaly_model_path), exist_ok=True)
        if os.path.exists(settings.anomaly_model_path):
            self._model = joblib.load(settings.anomaly_model_path)
        else:
            self._model = self._train_baseline_model()
            joblib.dump(self._model, settings.anomaly_model_path)

    def _train_baseline_model(self) -> IsolationForest:
        rng = np.random.default_rng(42)
        normal_traffic = rng.normal(loc=[5, 200, 3, 0.2], scale=[3.0, 200.0, 2.0, 0.15], size=(3000, 4))
        normal_traffic = np.clip(normal_traffic, 0, None)

        model = IsolationForest(n_estimators=150, contamination=0.05, random_state=42)
        model.fit(normal_traffic)
        return model

    def extract_features(self, client_ip: str, endpoint: str, packet_size: int) -> np.ndarray:
        now = time.time()
        self._history[client_ip].append((now, endpoint, packet_size))

        events = list(self._history[client_ip])
        window = [e for e in events if now - e[0] <= 1.0]

        requests_per_sec = len(window)
        avg_packet_size = float(np.mean([e[2] for e in window])) if window else float(packet_size)
        unique_endpoints = len({e[1] for e in window}) if window else 1

        timestamps = [e[0] for e in events[-10:]]
        interval_variance = float(np.var(np.diff(timestamps))) if len(timestamps) > 2 else 0.2

        return np.array([[requests_per_sec, avg_packet_size, unique_endpoints, interval_variance]])

    def score(self, client_ip: str, endpoint: str, packet_size: int) -> tuple[float, bool]:
        features = self.extract_features(client_ip, endpoint, packet_size)
        raw_score = self.decision_score(features)
        is_anomaly = self.is_outlier(features)
        return raw_score, is_anomaly

    def decision_score(self, features: np.ndarray) -> float:
        return float(self._model.decision_function(features)[0])

    def is_outlier(self, features: np.ndarray) -> bool:

        return int(self._model.predict(features)[0]) == -1

    def reload_model(self):
        self._model = joblib.load(settings.anomaly_model_path)


anomaly_detector = AnomalyDetector()
