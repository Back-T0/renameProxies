import ipaddress
import socket
import subprocess
import threading
import time

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


def get_nation_info(server, nation_cache):
    if server in nation_cache:
        return nation_cache[server]
    ip = _resolve_server_to_ip(server)
    if not ip:
        nation_cache[server] = ("未知", "cn", 0)
        print(f"无法解析 {server}, 设置为未知.")
        return nation_cache[server]

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
        nation_cache[server] = ("未知", "cn", 0)
        print(f"无法确定 {server} 的归属国家.")
        return nation_cache[server]
    record = output["record"]
    pair = _country_from_record(record)
    if pair:
        nation, iso_code = pair
        nation_cache[server] = (nation, iso_code, 0)
        print(f"{server} 归属 {nation} ({iso_code})")
        return nation_cache[server]

    nation_cache[server] = ("未知", "cn", 0)
    print(f"无法确定 {server} 的归属国家.")
    return nation_cache[server]


def fetch_all_nations(domains, ips):
    print("获取所有服务器的国家信息...")
    nation_cache, threads = {}, []

    def thread_func(server):
        get_nation_info(server, nation_cache)

    for server in domains + ips:
        t = threading.Thread(target=thread_func, args=(server,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    return nation_cache
