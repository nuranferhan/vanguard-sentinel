import asyncio
import time
from collections import defaultdict, deque
from app.protocols.packet_codec import PacketCodec, GamePacket
from app.security.token_auth import token_authenticator
from app.security.replay_guard import replay_guard
from app.ai.anomaly_detector import anomaly_detector
from app.models.schemas import TrafficEvent, ActionType, Protocol
from app.websocket.broadcaster import stats_broadcaster
from app.utils.logger import logger
from app.config import settings


class SynFloodHeuristic:


    def __init__(self, window_seconds: float = 2.0, max_new_sessions: int = 30):
        self.window_seconds = window_seconds
        self.max_new_sessions = max_new_sessions
        self._session_events: dict[str, deque] = defaultdict(deque)

    def register_and_check(self, client_ip: str, session_id: str) -> bool:
        now = time.time()
        events = self._session_events[client_ip]
        events.append((now, session_id))

        while events and now - events[0][0] > self.window_seconds:
            events.popleft()

        unique_sessions = {sid for _, sid in events}
        return len(unique_sessions) > self.max_new_sessions


syn_flood_guard = SynFloodHeuristic()


class UDPGatewayProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport: asyncio.transports.DatagramTransport | None = None

    def connection_made(self, transport):
        self.transport = transport
        logger.info(f"UDP gateway dinlemede: {settings.udp_gateway_host}:{settings.udp_gateway_port}")

    def datagram_received(self, data: bytes, addr):
        asyncio.create_task(self._handle_packet(data, addr))

    async def _handle_packet(self, data: bytes, addr):
        client_ip = addr[0]
        packet = PacketCodec.decode(data)

        if packet is None:
            await self._emit(client_ip, "malformed", 0, ActionType.AUTH_FAILED)
            return

        if syn_flood_guard.register_and_check(client_ip, packet.session_id):
            await self._emit(client_ip, packet.action_type, len(data), ActionType.RATE_LIMITED)
            return

        replay_result = await replay_guard.validate(packet.client_id, packet.nonce, packet.timestamp)
        if not replay_result.is_valid:
            await self._emit(client_ip, packet.action_type, len(data), ActionType.REPLAY_BLOCKED)
            return

        score, is_anomaly = anomaly_detector.score(client_ip, packet.action_type, len(data))
        if is_anomaly:
            await self._emit(client_ip, packet.action_type, len(data), ActionType.ANOMALY_BLOCKED, score)
            return

        await self._emit(client_ip, packet.action_type, len(data), ActionType.ALLOWED, score)
        self._forward_to_upstream(data, addr)

    def _forward_to_upstream(self, data: bytes, addr):
        if self.transport:
            ack = PacketCodec.encode(
                GamePacket(
                    client_id="server",
                    session_id="server",
                    action_type="ack",
                    payload={"status": "accepted"},
                    sequence_id=0,
                    timestamp=time.time(),
                    nonce="server_ack",
                )
            )
            self.transport.sendto(ack, addr)

    async def _emit(self, client_ip, endpoint, size, action, score=None):
        event = TrafficEvent(
            timestamp=time.time(),
            client_ip=client_ip,
            endpoint=endpoint,
            method="UDP",
            packet_size=size,
            action=action,
            protocol=Protocol.UDP,
            anomaly_score=score,
        )
        await stats_broadcaster.broadcast(event.model_dump())


async def start_udp_gateway():
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: UDPGatewayProtocol(),
        local_addr=(settings.udp_gateway_host, settings.udp_gateway_port),
    )
