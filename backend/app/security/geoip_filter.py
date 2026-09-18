import geoip2.database
import geoip2.errors
from app.config import settings
from app.utils.logger import logger


class GeoIPFilter:

    def __init__(self):
        self._reader: geoip2.database.Reader | None = None
        if settings.geoip_enabled:
            try:
                self._reader = geoip2.database.Reader(settings.geoip_db_path)
            except FileNotFoundError:
                logger.warning(
                    f"GeoIP veritabanı bulunamadı: {settings.geoip_db_path}. "
                    "GeoIP filtresi devre dışı kalacak."
                )

    def resolve_country(self, ip: str) -> str | None:
        if self._reader is None:
            return None
        try:
            response = self._reader.country(ip)
            return response.country.iso_code
        except geoip2.errors.AddressNotFoundError:
            return None
        except ValueError:
            return None

    def is_allowed(self, ip: str) -> tuple[bool, str | None]:
        if self._reader is None:
            return True, None

        country_code = self.resolve_country(ip)
        if country_code is None:
            return True, None

        allowed = country_code in settings.geoip_allowed_countries
        return allowed, country_code

    def close(self):
        if self._reader is not None:
            self._reader.close()


geoip_filter = GeoIPFilter()
