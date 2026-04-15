import ipaddress
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import yaml


def collect_servers(proxies):
    print("收集代理服务器信息...")
    domains, ips = set(), set()
    for proxy in proxies:
        server = proxy.get("server")
        if not server:
            continue
        s = server.strip()
        try:
            ipaddress.ip_address(s)
            ips.add(s)
        except ValueError:
            domains.add(s)
    print(f"发现 {len(domains)} 个域名, {len(ips)} 个 IP 地址.")
    return list(domains), list(ips)


def _resolve_server_to_ip(server):
    """将 IPv4/IPv6 字面量或主机名解析为用于 GeoIP 的 IP 字符串。"""
    s = (server or "").strip()
    if not s:
        return None
    try:
        return str(ipaddress.ip_address(s))
    except ValueError:
        pass
    for attempt in range(3):
        try:
            infos = socket.getaddrinfo(s, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for fam, _, _, _, sockaddr in infos:
                if fam == socket.AF_INET:
                    return sockaddr[0]
            for fam, _, _, _, sockaddr in infos:
                if fam == socket.AF_INET6:
                    return sockaddr[0]
        except socket.gaierror:
            if attempt < 2:
                time.sleep(0.3)
    return None


def _pick_country_display_name(country_info):
    """优先中文国名，其次英文，再取 names 中任意一项，最后用 iso_code。"""
    if not country_info:
        return None
    names = country_info.get("names") or {}
    for key in ("zh-CN", "en", "en-US"):
        v = names.get(key)
        if v:
            return v
    if names:
        return next(iter(names.values()))
    return country_info.get("iso_code")


def _country_from_record(record):
    """依次尝试 country / registered_country / represented_country。"""
    for key in ("country", "registered_country", "represented_country"):
        info = record.get(key)
        if not isinstance(info, dict):
            continue
        nation = _pick_country_display_name(info)
        iso_code = info.get("iso_code") or "cn"
        if nation:
            return nation, iso_code
    return None


def _cache_get(nation_cache, server, lock=None):
    if lock is None:
        return nation_cache.get(server)
    with lock:
        return nation_cache.get(server)


def _cache_set(nation_cache, server, value, lock=None):
    if lock is None:
        nation_cache[server] = value
        return value
    with lock:
        nation_cache[server] = value
    return value


def get_nation_info(server, nation_cache, lock=None):
    cached = _cache_get(nation_cache, server, lock)
    if cached is not None:
        return cached
    ip = _resolve_server_to_ip(server)
    if not ip:
        _cache_set(nation_cache, server, ("未知", "cn", 0), lock)
        print(f"无法解析 {server}, 设置为未知.")
        return _cache_get(nation_cache, server, lock)

    result = subprocess.run(
        ["mmdbinspect", "-db", "Country.mmdb", ip],
        capture_output=True,
        text=True,
    )
    output = yaml.safe_load(result.stdout)
    if not output or "record" not in output:
        err = (result.stderr or "").strip()
        if err:
            print(f"{server} mmdbinspect: {err[:300]}")
        _cache_set(nation_cache, server, ("未知", "cn", 0), lock)
        print(f"无法确定 {server} 的归属国家.")
        return _cache_get(nation_cache, server, lock)
    record = output["record"]
    pair = _country_from_record(record)
    if pair:
        nation, iso_code = pair
        _cache_set(nation_cache, server, (nation, iso_code, 0), lock)
        print(f"{server} 归属 {nation} ({iso_code})")
        return _cache_get(nation_cache, server, lock)

    _cache_set(nation_cache, server, ("未知", "cn", 0), lock)
    print(f"无法确定 {server} 的归属国家.")
    return _cache_get(nation_cache, server, lock)


def fetch_all_nations(domains, ips):
    print("获取所有服务器的国家信息...")
    nation_cache = {}
    lock = threading.Lock()

    def thread_func(server):
        with lock:
            cached = nation_cache.get(server)
        if cached is not None:
            return cached
        return get_nation_info(server, nation_cache, lock=lock)

    servers = list(dict.fromkeys([*domains, *ips]))
    max_workers = min(32, max(1, len(servers)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(thread_func, servers))
    return nation_cache
