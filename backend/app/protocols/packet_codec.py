import msgpack
from pydantic import BaseModel, ValidationError


class GamePacket(BaseModel):


    client_id: str
    session_id: str
    action_type: str
    payload: dict
    sequence_id: int
    timestamp: float
    nonce: str


class PacketCodec:


    @staticmethod
    def encode(packet: GamePacket) -> bytes:
        return msgpack.packb(packet.model_dump(), use_bin_type=True)

    @staticmethod
    def decode(raw: bytes) -> GamePacket | None:
        try:
            data = msgpack.unpackb(raw, raw=False)
            return GamePacket(**data)
        except (msgpack.exceptions.ExtraData, ValueError, ValidationError, TypeError):
            return None
