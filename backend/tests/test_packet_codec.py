import time
from app.protocols.packet_codec import PacketCodec, GamePacket


def test_encode_decode_roundtrip():
    packet = GamePacket(
        client_id="c1",
        session_id="s1",
        action_type="move",
        payload={"x": 1, "y": 2},
        sequence_id=1,
        timestamp=time.time(),
        nonce="abc123",
    )
    encoded = PacketCodec.encode(packet)
    decoded = PacketCodec.decode(encoded)
    assert decoded is not None
    assert decoded.client_id == "c1"
    assert decoded.payload == {"x": 1, "y": 2}


def test_malformed_packet_rejected():
    decoded = PacketCodec.decode(b"not a valid msgpack payload \xff\xfe")
    assert decoded is None
