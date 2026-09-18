import time
import math
from collections import defaultdict, deque
from app.models.schemas import CheatSignal


class CheatDetector:


    MAX_SPEED_UNITS_PER_SEC = 15.0
    MIN_REPEAT_INTERVAL_SEC = 0.05
    MIN_ELAPSED_FOR_SPEED_CHECK = 0.02

    def __init__(self):
        self._last_position: dict[str, tuple[float, float, float]] = {}
        self._last_payloads: dict[str, deque] = defaultdict(lambda: deque(maxlen=5))

    def evaluate(self, client_id: str, action_type: str, payload: dict, timestamp: float | None = None) -> CheatSignal | None:
        now = timestamp if timestamp is not None else time.time()

        if action_type == "move" and "x" in payload and "y" in payload:
            speed_signal = self._check_speed(client_id, payload, now)
            if speed_signal:
                return speed_signal

        repeat_signal = self._check_repeat_payload(client_id, payload, now)
        if repeat_signal:
            return repeat_signal

        return None

    def _check_speed(self, client_id: str, payload: dict, now: float) -> CheatSignal | None:
        x, y = float(payload["x"]), float(payload["y"])

        if client_id in self._last_position:
            last_x, last_y, last_t = self._last_position[client_id]
            elapsed = now - last_t

            if elapsed < self.MIN_ELAPSED_FOR_SPEED_CHECK:
                self._last_position[client_id] = (x, y, now)
                return None

            distance = math.hypot(x - last_x, y - last_y)
            speed = distance / elapsed

            if speed > self.MAX_SPEED_UNITS_PER_SEC:
                self._last_position[client_id] = (x, y, now)
                return CheatSignal(
                    client_id=client_id,
                    signal_type="speed_hack",
                    detail=f"speed={speed:.2f} units/sec, limit={self.MAX_SPEED_UNITS_PER_SEC}",
                    detected_at=now,
                    severity="high",
                )

        self._last_position[client_id] = (x, y, now)
        return None

    def _check_repeat_payload(self, client_id: str, payload: dict, now: float) -> CheatSignal | None:
        history = self._last_payloads[client_id]
        signature = str(sorted(payload.items()))

        for prev_signature, prev_time in history:
            if prev_signature == signature and now - prev_time < self.MIN_REPEAT_INTERVAL_SEC:
                history.append((signature, now))
                return CheatSignal(
                    client_id=client_id,
                    signal_type="macro_bot_pattern",
                    detail="identical payload repeated below human reaction threshold",
                    detected_at=now,
                    severity="medium",
                )

        history.append((signature, now))
        return None


cheat_detector = CheatDetector()
