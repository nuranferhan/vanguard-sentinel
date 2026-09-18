import time
from fastapi import WebSocket, WebSocketDisconnect
from app.protocols.packet_codec import PacketCodec
from app.security.replay_guard import replay_guard
from app.security.token_auth import token_authenticator
from app.ai.anomaly_detector import anomaly_detector
from app.ai.cheat_detector import cheat_detector
from app.models.schemas import TrafficEvent, ActionType, Protocol
from app.websocket.broadcaster import stats_broadcaster
from app.utils.logger import logger


class WebSocketGameGateway:


    async def handle_connection(self, websocket: WebSocket, token: str | None):
        if token is None or token_authenticator.verify_token(token) is None:
            await websocket.close(code=4401)
            return

        await websocket.accept()
        client_ip = websocket.client.host if websocket.client else "unknown"

        try:
            while True:
                raw = await websocket.receive_bytes()
                await self._process_message(client_ip, raw)
        except WebSocketDisconnect:
            logger.info(f"WebSocket bağlantısı kapandı: {client_ip}")

    async def _process_message(self, client_ip: str, raw: bytes):
        packet = PacketCodec.decode(raw)
        if packet is None:
            await self._emit(client_ip, "malformed", len(raw), ActionType.AUTH_FAILED)
            return

        replay_result = await replay_guard.validate(packet.client_id, packet.nonce, packet.timestamp)
        if not replay_result.is_valid:
            await self._emit(client_ip, packet.action_type, len(raw), ActionType.REPLAY_BLOCKED)
            return

        cheat_signal = cheat_detector.evaluate(packet.client_id, packet.action_type, packet.payload, packet.timestamp)
        if cheat_signal is not None:
            await self._emit(client_ip, packet.action_type, len(raw), ActionType.CHEAT_DETECTED)
            return

        score, is_anomaly = anomaly_detector.score(client_ip, packet.action_type, len(raw))
        action = ActionType.ANOMALY_BLOCKED if is_anomaly else ActionType.ALLOWED
        await self._emit(client_ip, packet.action_type, len(raw), action, score)

    async def _emit(self, client_ip, endpoint, size, action, score=None):
        event = TrafficEvent(
            timestamp=time.time(),
            client_ip=client_ip,
            endpoint=endpoint,
            method="WS",
            packet_size=size,
            action=action,
            protocol=Protocol.WEBSOCKET,
            anomaly_score=score,
        )
        await stats_broadcaster.broadcast(event.model_dump())


ws_game_gateway = WebSocketGameGateway()
