from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Vanguard Sentinel"
    upstream_game_server: str = "http://localhost:9000"
    upstream_udp_host: str = "127.0.0.1"
    upstream_udp_port: int = 9100

    rate_limit_capacity: int = 20
    rate_limit_refill_per_sec: float = 5.0

    aes_secret_key: str = "CHANGE_ME_32_BYTE_SECRET_KEY!!"
    jwt_secret: str = "CHANGE_ME_JWT_SECRET"
    jwt_algorithm: str = "HS256"

    anomaly_model_path: str = "app/ai/models/isolation_forest.joblib"
    autoencoder_model_path: str = "app/ai/models/autoencoder.joblib"
    anomaly_score_threshold: float = -0.15
    autoencoder_error_threshold: float = 0.35
    ensemble_vote_threshold: int = 2
    online_retrain_interval_sec: int = 900
    feature_store_window_size: int = 200

    blacklist_ttl_seconds: int = 3600
    max_violations_before_ban: int = 5

    redis_url: str = "redis://localhost:6379/0"

    mtls_enabled: bool = False
    mtls_ca_cert_path: str = "certs/ca.pem"
    mtls_server_cert_path: str = "certs/server.pem"
    mtls_server_key_path: str = "certs/server.key"

    replay_window_seconds: int = 30
    replay_nonce_ttl_seconds: int = 60

    geoip_enabled: bool = False
    geoip_db_path: str = "app/security/GeoLite2-Country.mmdb"
    geoip_allowed_countries: list[str] = ["TR", "DE", "NL", "FR", "US", "GB"]

    udp_gateway_host: str = "0.0.0.0"
    udp_gateway_port: int = 9200
    ws_gateway_path: str = "/ws/game"

    prometheus_enabled: bool = True
    otel_enabled: bool = False
    otel_exporter_endpoint: str = "http://localhost:4317"

    slack_webhook_url: str = ""
    alert_email_enabled: bool = False
    alert_smtp_host: str = "smtp.gmail.com"
    alert_smtp_port: int = 587
    alert_smtp_user: str = ""
    alert_smtp_password: str = ""
    alert_recipient: str = ""
    critical_attack_threshold_per_min: int = 50

    jwt_admin_secret: str = "CHANGE_ME_ADMIN_JWT_SECRET"
    audit_log_retention_days: int = 90

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_traffic_topic: str = "vanguard.traffic.events"
    event_streaming_enabled: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
