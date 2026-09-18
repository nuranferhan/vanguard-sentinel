import time
import smtplib
from email.mime.text import MIMEText
from collections import deque
import httpx
from app.config import settings
from app.utils.logger import logger


class AlertManager:


    COOLDOWN_SECONDS = 300

    def __init__(self):
        self._recent_blocks: deque = deque()
        self._last_alert_sent: float = 0.0

    def record_block(self):
        now = time.time()
        self._recent_blocks.append(now)
        while self._recent_blocks and now - self._recent_blocks[0] > 60:
            self._recent_blocks.popleft()

        if len(self._recent_blocks) >= settings.critical_attack_threshold_per_min:
            self._maybe_send_alert(len(self._recent_blocks))

    def _maybe_send_alert(self, block_count: int):
        now = time.time()
        if now - self._last_alert_sent < self.COOLDOWN_SECONDS:
            return

        self._last_alert_sent = now
        message = (
            f"[Vanguard Sentinel] Kritik saldırı eşiği aşıldı: "
            f"son 1 dakikada {block_count} istek engellendi."
        )
        self._send_slack(message)
        if settings.alert_email_enabled:
            self._send_email(message)

    def _send_slack(self, message: str):
        if not settings.slack_webhook_url:
            logger.warning("Slack webhook tanımlı değil, alarm gönderilemedi")
            return
        try:
            httpx.post(settings.slack_webhook_url, json={"text": message}, timeout=5.0)
        except httpx.RequestError as exc:
            logger.error(f"Slack alarmı gönderilemedi: {exc}")

    def _send_email(self, message: str):
        try:
            msg = MIMEText(message)
            msg["Subject"] = "Vanguard Sentinel Kritik Alarm"
            msg["From"] = settings.alert_smtp_user
            msg["To"] = settings.alert_recipient

            with smtplib.SMTP(settings.alert_smtp_host, settings.alert_smtp_port) as server:
                server.starttls()
                server.login(settings.alert_smtp_user, settings.alert_smtp_password)
                server.send_message(msg)
        except Exception as exc:
            logger.error(f"E-posta alarmı gönderilemedi: {exc}")


alert_manager = AlertManager()
