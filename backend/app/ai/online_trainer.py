import asyncio
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
from app.ai.feature_store import feature_store
from app.ai.anomaly_detector import anomaly_detector
from app.config import settings
from app.utils.logger import logger


class OnlineRetrainer:


    def __init__(self, interval_seconds: int):
        self.interval_seconds = interval_seconds
        self._known_clients: set[str] = set()

    def track_client(self, client_id: str):
        self._known_clients.add(client_id)

    async def run_forever(self):
        while True:
            await asyncio.sleep(self.interval_seconds)
            await self._retrain_cycle()

    async def _retrain_cycle(self):
        if len(self._known_clients) < 5:
            logger.info("Online retrain atlandı: yeterli istemci verisi yok")
            return

        feature_rows = []
        for client_id in list(self._known_clients)[:200]:
            matrix = await feature_store.get_feature_matrix(client_id, limit=20)
            if matrix.shape[0] > 0:
                feature_rows.append(matrix)

        if not feature_rows:
            return

        combined = np.vstack(feature_rows)
        if combined.shape[0] < 50:
            logger.info("Online retrain atlandı: örneklem sayısı yetersiz")
            return

        new_model = IsolationForest(n_estimators=150, contamination=0.05, random_state=42)
        new_model.fit(combined)
        joblib.dump(new_model, settings.anomaly_model_path)
        anomaly_detector.reload_model()

        logger.info(f"Model yeniden eğitildi, örneklem sayısı: {combined.shape[0]}")


online_retrainer = OnlineRetrainer(interval_seconds=settings.online_retrain_interval_sec)
