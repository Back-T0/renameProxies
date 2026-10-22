import ipaddress
import threading
from urllib.parse import quote

import requests

from .models import LocationResult


class LocationLookupError(RuntimeError):
    pass


class LocationResolver:
    def __init__(self, settings, session=None):
        self.settings = settings
        self.session = session or requests.Session()
        self._cache = {}
        self._pending = {}
        self._lock = threading.Lock()

    def lookup(self, ip):
        ip = str(ipaddress.ip_address(ip))
        with self._lock:
            if ip in self._cache:
                return self._cache[ip]
            event = self._pending.get(ip)
            if event is None:
                event = self._pending[ip] = threading.Event()
                owner = True
            else:
                owner = False

        if not owner:
            event.wait()
            with self._lock:
                result = self._cache.get(ip)
            if result is None:
                raise LocationLookupError(f"无法查询出口 IP {ip} 的国家/地区")
            return result

        result = None
        try:
            result = self._lookup_uncached(ip)
            return result
        finally:
            with self._lock:
                if result is not None:
                    self._cache[ip] = result
                self._pending.pop(ip).set()

    def _lookup_uncached(self, ip):
        errors = []
        for provider in self.settings.providers:
            try:
                if provider == "ipapi":
                    result = self._from_ipapi(ip)
                elif provider == "ipinfo":
                    result = self._from_ipinfo(ip)
                else:
                    errors.append(f"未知服务 {provider}")
                    continue
                if result:
                    return result
            except (requests.RequestException, ValueError, KeyError) as exc:
                errors.append(f"{provider}: {exc}")
        detail = "; ".join(errors) or "没有可用的国家查询服务"
        raise LocationLookupError(f"无法查询出口 IP {ip}: {detail}")

    def _from_ipapi(self, ip):
        response = self.session.get(
            f"https://api.ipapi.is/?q={quote(ip)}",
            timeout=self.settings.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        location = payload.get("location") or {}
        country = location.get("country")
        if not country:
            return None
        return LocationResult(
            country=str(country),
            country_code=str(location.get("country_code") or "").upper(),
        )

    def _from_ipinfo(self, ip):
        params = {}
        if self.settings.ipinfo_token:
            params["token"] = self.settings.ipinfo_token
        response = self.session.get(
            f"https://ipinfo.io/{quote(ip)}/json",
            params=params,
            timeout=self.settings.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("bogon") or not payload.get("country"):
            return None
        code = str(payload["country"]).upper()
        return LocationResult(country=code, country_code=code)
