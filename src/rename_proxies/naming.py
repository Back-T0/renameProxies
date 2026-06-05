from collections import defaultdict


def apply_nation_names(proxies, nation_cache):
    """按 GeoIP 重命名节点，并生成代理组构建所需的 entries。"""
    nation_counter = defaultdict(int)
    new_proxies = []
    entries = []
    for proxy in proxies:
        orig = (proxy.get("name") or "").strip()
        p = dict(proxy)
        server = p.get("server")
        if server:
            nation, _, _ = nation_cache.get(server, ("未知", "cn", 0))
            nation_counter[nation] += 1
            p["name"] = f"{nation} {nation_counter[nation]}"
        new_proxies.append(p)
        entries.append({"name": (p.get("name") or "").strip(), "orig": orig, "type": p.get("type")})
    return new_proxies, entries, nation_counter
