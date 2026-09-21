# Vanguard Sentinel

Dağıtık oyun sunucuları için AI destekli API Gateway ve DDoS/Exploit engelleyici. 


## Mimari

```
İstemci -> [mTLS] -> Vanguard Gateway -> [Redis + AI Ensemble] -> Oyun Sunucusu
                              |
                    [Prometheus / Kafka / Dashboard]
```

## Kapsam ve Karşılık Gelen Dosyalar

### Çekirdek Gateway
- `app/proxy.py`, `app/main.py` — async reverse proxy
- `app/security/token_auth.py` — AES-CBC + HMAC token doğrulama
- `app/security/rate_limiter.py`, `app/security/blacklist.py` — Redis tabanlı rate limiting ve blacklist
- `app/security/mtls.py` — karşılıklı TLS sertifika doğrulama
- `app/security/replay_guard.py` — nonce + timestamp tabanlı replay koruması
- `app/security/geoip_filter.py` — MaxMind GeoIP2 ile bölgesel erişim kısıtlama

### Protokol Katmanı
- `app/protocols/udp_gateway.py` — UDP tabanlı oyun protokolü desteği
- `app/protocols/ws_gateway.py` — WebSocket gerçek zamanlı bağlantı katmanı
- `app/protocols/packet_codec.py`, `packet_schema.proto` — MessagePack/Protobuf şema doğrulama
- `SynFloodHeuristic` sınıfı (`udp_gateway.py` içinde) — volumetrik saldırı tespiti

### AI Katmanı
- `app/ai/anomaly_detector.py` — Isolation Forest
- `app/ai/autoencoder_model.py` — MLP tabanlı autoencoder
- `app/ai/ensemble.py` — iki modelin oylama mekanizması
- `app/ai/online_trainer.py` — periyodik yeniden eğitim
- `app/ai/feature_store.py` — Redis tabanlı davranış geçmişi deposu
- `app/ai/cheat_detector.py` — speed hacking ve paket tekrarı tespiti

### Gözlemlenebilirlik
- `app/observability/metrics.py` — Prometheus metrikleri (`/metrics`)
- `infra/grafana/dashboard.json` — Grafana dashboard tanımı
- `app/observability/tracing.py` — OpenTelemetry dağıtık izleme
- `app/observability/alerting.py` — Slack/e-posta kritik saldırı alarmı

### Yönetim Paneli
- `app/admin/rbac.py` — rol tabanlı erişim kontrolü (admin/analyst/viewer)
- `app/admin/rule_engine.py` — manuel filtre kural motoru
- `app/admin/audit_log.py` — audit log
- `app/admin/reports.py` — geçmiş saldırı trend raporları
- `dashboard/src/components/LoginPanel.jsx`, `RuleManager.jsx` — panel arayüzü

### Ölçeklenebilirlik ve DevOps
- `infra/kubernetes/` — Helm chart (Deployment, Service, HPA, ConfigMap)
- `docker-compose.yml` — Redis, Kafka, Prometheus, Grafana orkestrasyonu
- `app/observability/event_stream.py` — Kafka event streaming
- `.github/workflows/ci-cd.yml` — lint, test, build, push, deploy pipeline

### Test, Yük Testi, Dokümantasyon
- `infra/k6/load_test.js`, `attack_simulation.js` — yük ve saldırı simülasyonu
- `backend/tests/` — birim testleri
- FastAPI otomatik Swagger dokümantasyonu: `/docs`

## Kurulum

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```


### Sertifikalar (mTLS)
```bash
./scripts/generate_dev_certs.sh
```

### Model Dosyaları
```bash
python scripts/download_models.py
```

### Sahte oyun sunucusu (test)
```bash
cd backend
uvicorn mock_game_server:app --port 9000
```

### Dashboard
```bash
cd dashboard
npm install
npm run dev
```

### Docker Compose
```bash
docker compose up --build
```

Bu komut şu servisleri ayağa kaldırır:
- `gateway` → http://localhost:8000
- `dashboard` → http://localhost:3000
- `prometheus` → http://localhost:9090
- `grafana` → http://localhost:3001 (admin/admin)
- `redis`, `kafka`, `zookeeper`, `game-server`

## Kullanım

### 1. Oyuncu token'ı al
```bash
curl -X POST "http://localhost:8000/auth/issue-token?client_id=player1&session_id=sess1"
```

### 2. Gateway üzerinden istek at
```bash
curl -X POST http://localhost:8000/gateway/player/action \
  -H "X-Session-Token: <alinan_token>" \
  -H "Content-Type: application/json" \
  -d '{"action": "jump"}'
```

### 3. Admin paneline giriş yap
```bash
curl -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "vanguard_admin_pw"}'
```
Demo kullanıcılar: `admin/vanguard_admin_pw`, `analyst/vanguard_analyst_pw`, `viewer/vanguard_viewer_pw`
(prodüksiyonda `app/admin/rbac.py` içindeki `_DEMO_USERS` gerçek bir kullanıcı
veritabanı ile değiştirilmelidir).

### 4. Dashboard'ı aç

## Test

```bash
cd backend
pytest -v
```

Redis gerektiren testler (`test_rate_limiter_redis.py`, `test_blacklist_redis.py`)
çalışan bir Redis instance'ı bekler; `docker compose up redis` ile ayağa kaldırılabilir.

## Yük Testi

```bash
k6 run infra/k6/load_test.js
k6 run infra/k6/attack_simulation.js
```

## Kubernetes Dağıtımı

```bash
helm install vanguard-sentinel ./infra/kubernetes
```

## Bağımlılıklar

Backend bağımlılıkları `backend/requirements.txt` içinde sabit 
sürümlerle listelenmiştir; dashboard bağımlılıkları `dashboard/package.json`
içindedir. Güvenlik güncellemeleri için düzenli olarak
`pip list --outdated` / `npm outdated` ile kontrol edilmesi önerilir.

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
