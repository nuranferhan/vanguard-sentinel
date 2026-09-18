import time
import hmac
import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from app.config import settings
from app.models.schemas import ClientToken


class TokenAuthenticator:
    def __init__(self, secret_key: str):
        self._key = hashlib.sha256(secret_key.encode()).digest()

    def _sign(self, payload: bytes) -> str:
        return hmac.new(self._key, payload, hashlib.sha256).hexdigest()

    def encrypt_token(self, client_id: str, session_id: str) -> str:
        cipher = AES.new(self._key, AES.MODE_CBC)
        raw = f"{client_id}:{session_id}:{time.time()}".encode()
        encrypted = cipher.encrypt(pad(raw, AES.block_size))
        payload = cipher.iv + encrypted
        signature = self._sign(payload)
        token = base64.urlsafe_b64encode(payload).decode() + "." + signature
        return token

    def verify_token(self, token: str) -> ClientToken | None:
        try:
            payload_b64, signature = token.split(".")
            payload = base64.urlsafe_b64decode(payload_b64)

            if not hmac.compare_digest(self._sign(payload), signature):
                return None

            iv, encrypted = payload[:16], payload[16:]
            cipher = AES.new(self._key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted), AES.block_size).decode()

            client_id, session_id, issued_at = decrypted.split(":")
            return ClientToken(
                client_id=client_id,
                session_id=session_id,
                issued_at=float(issued_at),
                signature=signature,
            )
        except Exception:
            return None


token_authenticator = TokenAuthenticator(settings.aes_secret_key)
