# Vanguard Sentinel Mimari Dokümanı

## Protokol Katmanı

- HTTP: FastAPI üzerinden REST tabanlı oyun aksiyonları
- WebSocket: Düşük gecikmeli, persistent bağlantı gerektiren gerçek zamanlı etkileşimler
- UDP: Yüksek frekanslı pozisyon/aksiyon güncellemeleri, MessagePack ile kodlanmış GamePacket şeması

### UDP Katmanı Mimari Kararı: Ham Soket vs. Envoy External Authorization

UDP gateway `asyncio.DatagramProtocol` ile sıfırdan yazıldı (bkz. `app/protocols/udp_gateway.py`).
Bu bilinçli bir tercihti; alternatifi değerlendirmeye değer:

**Mevcut yaklaşım (ham soket):**
- Avantaj: Paket şeması doğrulama, replay koruması, anomali skorlama tek bir kod
  tabanında, ek altyapı bağımlılığı olmadan çalışır. Düşük seviye protokol
  davranışı üzerinde tam kontrol sağlar.
- Dezavantaj: Paket fragmentation, backpressure ve bağlantı durumu yönetimi
  gibi edge-case'lere karşı prodüksiyon sertliği (hardening) elle eklenmelidir;
  bunlar şu an kapsam dışıdır.

**Alternatif (Envoy/Nginx + External Authorization filtresi):**
- Avantaj: UDP taşıma katmanı olgun, savaş testi geçmiş bir proxy'ye (Envoy)
  bırakılır; gateway servisi yalnızca yetkilendirme kararı veren ince bir
  filtre olarak kalır. Prodüksiyon ortamında tercih edilen mimari budur.
- Dezavantaj: Ek altyapı bağımlılığı (Envoy config, xDS), yerel geliştirme ve
  hata ayıklama karmaşıklığını artırır.

Bu proje kapsamında ham soket yaklaşımı seçildi çünkü amaç protokol seviyesinde
güvenlik mekanizmalarını (replay koruması, paket şeması doğrulama, anomali
skorlama) uçtan uca göstermekti. Gerçek bir prodüksiyon dağıtımında, trafik
hacmi arttıkça bu katmanın Envoy'a devredilmesi ve gateway'in yalnızca
`ext_authz` filtresi olarak çalışması önerilir.

## Güvenlik Katmanları (Sırasıyla Uygulanır)

1. mTLS handshake (opsiyonel, TLS seviyesinde)
2. AES-CBC + HMAC-SHA256 token doğrulama
3. IP blacklist kontrolü
4. GeoIP bölgesel erişim kontrolü
5. Manuel kural motoru (endpoint desenine özel limit/ülke kısıtlaması)
6. Replay attack koruması (nonce + timestamp penceresi)
7. Redis tabanlı token bucket rate limiting
8. AI ensemble anomali tespiti (Isolation Forest + Autoencoder oylaması)
9. Hile tespiti (speed hacking, paket tekrarı) — WebSocket/UDP katmanında

## Gözlemlenebilirlik

- Prometheus: /metrics endpoint'i üzerinden sayaç ve gauge metrikleri
- OpenTelemetry: istek yaşam döngüsü boyunca dağıtık trace
- Kafka: trafik olaylarının dashboard'dan bağımsız, ayrıştırılmış event akışı
- Slack/e-posta: kritik saldırı eşiği aşıldığında otomatik alarm

## Veri Katmanı

- Redis: rate limit state, blacklist, nonce kayıtları, feature store, kural motoru, audit log
- Prodüksiyonda tek node Redis yerine Redis Cluster (6 node, 3 master + 3 replica) önerilir

## Ölçeklenebilirlik

- Gateway stateless tasarlandı; tüm paylaşılan state Redis'te tutulduğu için
  yatay ölçeklenebilir (Kubernetes HPA ile CPU bazlı otomatik ölçekleme)
- Kafka event streaming, dashboard ve raporlama servislerini gateway'in
  performansından izole eder

## Diğer Mimari Kararlar ve Gerekçeleri

### Online Learning: Gerçek Arka Plan Görevi vs. Simülasyon
`app/ai/online_trainer.py`, sentetik/örnek veriyle çalışan gerçek bir
`asyncio` arka plan görevidir (cron-job simülasyonu değil). Belirlenen
aralıkla feature store'dan veri toplar ve modeli yeniden eğitir. Bilinen
sınırlama: gerçek, insan onaylı temiz trafik verisi olmadan bu döngü
kirli veriyle kendini yeniden eğitebilir (model poisoning riski) — bu
`online_trainer.py` içindeki docstring'de açıkça belirtilmiştir.
Prodüksiyona geçmeden önce eğitim verisine bir onay/karantina adımı
eklenmelidir.

### RBAC Depolama: Redis vs. SQLite
Kullanıcı-rol eşleşmesi `app/admin/rbac.py` içinde bellek içi bir sözlükte
(`_DEMO_USERS`) tutulur; kural motoru ve audit log ise Redis'te. SQLite
yerine Redis tercih edilmesinin sebebi, projenin geri kalanının zaten
Redis'e bağımlı olması ve tek bir veri deposu ile operasyonel karmaşıklığın
azaltılmasıdır. Çok kullanıcılı, kalıcı bir kullanıcı yönetimi gerekiyorsa
(parola sıfırlama, kullanıcı oluşturma arayüzü vb.) PostgreSQL gibi
ilişkisel bir veritabanına geçilmesi önerilir.

