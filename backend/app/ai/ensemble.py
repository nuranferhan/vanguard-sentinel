from dataclasses import dataclass
from app.ai.anomaly_detector import anomaly_detector
from app.ai.autoencoder_model import autoencoder_detector
from app.config import settings


@dataclass
class EnsembleResult:
    is_anomaly: bool
    isolation_forest_score: float
    autoencoder_error: float
    votes: int


class AnomalyEnsemble:


    def evaluate(self, client_ip: str, endpoint: str, packet_size: int) -> EnsembleResult:
        features = anomaly_detector.extract_features(client_ip, endpoint, packet_size)

        if_score = anomaly_detector.decision_score(features)
        if_vote = anomaly_detector.is_outlier(features)

        ae_error, ae_vote = autoencoder_detector.is_anomaly(features)

        votes = int(if_vote) + int(ae_vote)
        is_anomaly = votes >= settings.ensemble_vote_threshold

        return EnsembleResult(
            is_anomaly=is_anomaly,
            isolation_forest_score=if_score,
            autoencoder_error=ae_error,
            votes=votes,
        )


anomaly_ensemble = AnomalyEnsemble()
