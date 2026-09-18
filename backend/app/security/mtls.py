import ssl
from app.config import settings
from app.utils.logger import logger


class MTLSContextBuilder:


    def __init__(self):
        self._context: ssl.SSLContext | None = None

    def build(self) -> ssl.SSLContext | None:
        if not settings.mtls_enabled:
            logger.info("mTLS devre dışı, standart TLS/plaintext ile çalışılıyor")
            return None

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            certfile=settings.mtls_server_cert_path,
            keyfile=settings.mtls_server_key_path,
        )
        context.load_verify_locations(cafile=settings.mtls_ca_cert_path)
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1_2

        self._context = context
        logger.info("mTLS context yüklendi, istemci sertifikası zorunlu")
        return context

    @property
    def context(self) -> ssl.SSLContext | None:
        return self._context


mtls_builder = MTLSContextBuilder()
