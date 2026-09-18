import os
import numpy as np
import joblib
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from app.config import settings


class AutoencoderAnomalyDetector:


    THRESHOLD_STD_MULTIPLIER = 4.0

    def __init__(self):
        self._model: MLPRegressor | None = None
        self._scaler: StandardScaler | None = None
        self._threshold: float = settings.autoencoder_error_threshold
        self._load_or_bootstrap_model()

    def _load_or_bootstrap_model(self):
        os.makedirs(os.path.dirname(settings.autoencoder_model_path), exist_ok=True)
        if os.path.exists(settings.autoencoder_model_path):
            bundle = joblib.load(settings.autoencoder_model_path)
            self._model = bundle["model"]
            self._scaler = bundle["scaler"]
            self._threshold = bundle["threshold"]
        else:
            self._model, self._scaler, self._threshold = self._train_baseline_model()
            joblib.dump(
                {"model": self._model, "scaler": self._scaler, "threshold": self._threshold},
                settings.autoencoder_model_path,
            )

    def _train_baseline_model(self) -> tuple[MLPRegressor, StandardScaler, float]:
        rng = np.random.default_rng(7)
        normal_traffic = rng.normal(loc=[5, 200, 3, 0.2], scale=[3.0, 200.0, 2.0, 0.15], size=(3000, 4))
        normal_traffic = np.clip(normal_traffic, 0, None)

        scaler = StandardScaler()
        scaled = scaler.fit_transform(normal_traffic)

        model = MLPRegressor(
            hidden_layer_sizes=(8, 2, 8),
            activation="relu",
            max_iter=800,
            random_state=7,
        )
        model.fit(scaled, scaled)

        reconstructed = model.predict(scaled)
        training_errors = np.mean((scaled - reconstructed) ** 2, axis=1)
        threshold = float(training_errors.mean() + self.THRESHOLD_STD_MULTIPLIER * training_errors.std())

        return model, scaler, threshold

    def reconstruction_error(self, features: np.ndarray) -> float:
        scaled = self._scaler.transform(features)
        reconstructed = self._model.predict(scaled)
        error = float(np.mean((scaled - reconstructed) ** 2))
        return error

    def is_anomaly(self, features: np.ndarray) -> tuple[float, bool]:
        error = self.reconstruction_error(features)
        return error, error > self._threshold

    def reload_model(self):
        bundle = joblib.load(settings.autoencoder_model_path)
        self._model = bundle["model"]
        self._scaler = bundle["scaler"]
        self._threshold = bundle["threshold"]


autoencoder_detector = AutoencoderAnomalyDetector()
