import ipaddress
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import yaml

from .models import LocationResult


def _resolve_server_to_ip(server):
    server = str(server or "").strip()
    if not server:
        return None
    try:
        return str(ipaddress.ip_address(server))
    except ValueError:
        pass
    for attempt in range(3):
        try:
            infos = socket.getaddrinfo(
                server, None, socket.AF_UNSPEC, socket.SOCK_STREAM
            )
            ipv6 = None
            for family, _, _, _, sockaddr in infos:
                if family == socket.AF_INET:
                    return sockaddr[0]
                if family == socket.AF_INET6 and ipv6 is None:
                    ipv6 = sockaddr[0]
            return ipv6
        except socket.gaierror:
            if attempt < 2:
                time.sleep(0.3)
    return None


def _country_from_record(record):
    for key in ("country", "registered_country", "represented_country"):
        info = record.get(key)
        if not isinstance(info, dict):
            continue
        names = info.get("names") or {}
        country = next(
            (names[key] for key in ("zh-CN", "en", "en-US") if names.get(key)),
            None,
        )
        country = country or (next(iter(names.values())) if names else None)
        country = country or info.get("iso_code")
        if country:
            return LocationResult(country, str(info.get("iso_code") or "").upper())
    return None


class GeoIPResolver:
    """服务器地址 GeoIP 查询，仅用于 Mihomo 实测失败后的兜底。"""

    def __init__(self, database="Country.mmdb", binary="mmdbinspect"):
        self.database = database
        self.binary = binary
        self._cache = {}
        self._pending = {}
        self._lock = threading.Lock()

    def lookup(self, server):
        key = str(server or "").strip()
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            event = self._pending.get(key)
            if event is None:
                event = self._pending[key] = threading.Event()
                owner = True
            else:
                owner = False

        if not owner:
            event.wait()
            with self._lock:
                return self._cache[key]

        try:
            result = self._lookup_uncached(key)
            with self._lock:
                self._cache[key] = result
            return result
        except Exception:
            result = LocationResult("未知")
            with self._lock:
                self._cache[key] = result
            return result
        finally:
            with self._lock:
                self._pending.pop(key).set()

    def _lookup_uncached(self, server):
        ip = _resolve_server_to_ip(server)
        if not ip:
            return LocationResult("未知")
        try:
            process = subprocess.run(
                [self.binary, "-db", self.database, ip],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            payload = yaml.safe_load(process.stdout) or {}
        except (OSError, subprocess.TimeoutExpired, yaml.YAMLError):
            return LocationResult("未知")
        if not isinstance(payload, dict):
            return LocationResult("未知")
        return _country_from_record(payload.get("record") or {}) or LocationResult("未知")


def collect_servers(proxies):
    domains, ips = set(), set()
    for proxy in proxies:
        server = str(proxy.get("server") or "").strip()
        if not server:
            continue
        try:
            ipaddress.ip_address(server)
            ips.add(server)
        except ValueError:
            domains.add(server)
    return list(domains), list(ips)


def fetch_all_nations(domains, ips):
    """保留旧 API；新流水线只为失败节点按需调用 GeoIPResolver。"""
    resolver = GeoIPResolver()
    servers = list(dict.fromkeys([*domains, *ips]))
    with ThreadPoolExecutor(max_workers=min(32, max(1, len(servers)))) as executor:
        results = executor.map(resolver.lookup, servers)
        return {
            server: (result.country, result.country_code, 0)
            for server, result in zip(servers, results)
        }
