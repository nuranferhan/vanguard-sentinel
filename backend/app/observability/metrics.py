from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNTER = Counter(
    "vanguard_requests_total",
    "Toplam gateway isteği sayısı",
    ["action", "protocol"],
)

REQUEST_LATENCY = Histogram(
    "vanguard_request_latency_seconds",
    "Gateway istek işleme süresi",
    ["protocol"],
)

ANOMALY_SCORE_GAUGE = Gauge(
    "vanguard_last_anomaly_score",
    "Son hesaplanan Isolation Forest anomali skoru",
)

AUTOENCODER_ERROR_GAUGE = Gauge(
    "vanguard_last_autoencoder_error",
    "Son hesaplanan autoencoder yeniden yapılandırma hatası",
)

BLOCKED_REQUESTS_COUNTER = Counter(
    "vanguard_blocked_requests_total",
    "Engellenen istek sayısı",
    ["reason"],
)

ACTIVE_BLACKLIST_GAUGE = Gauge(
    "vanguard_active_blacklist_entries",
    "Şu anda kara listede olan IP sayısı",
)

ACTIVE_WS_CONNECTIONS_GAUGE = Gauge(
    "vanguard_active_websocket_connections",
    "Aktif WebSocket bağlantı sayısı",
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
