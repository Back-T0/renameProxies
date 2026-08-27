from collections import defaultdict

from .models import ProxyNode


COUNTRY_NAMES = {
    "AU": "澳大利亚",
    "CA": "加拿大",
    "CN": "中国",
    "DE": "德国",
    "FR": "法国",
    "GB": "英国",
    "HK": "香港",
    "IN": "印度",
    "JP": "日本",
    "KR": "韩国",
    "MO": "澳门",
    "MY": "马来西亚",
    "NL": "荷兰",
    "PH": "菲律宾",
    "RO": "罗马尼亚",
    "RU": "俄罗斯",
    "SG": "新加坡",
    "TH": "泰国",
    "TR": "土耳其",
    "TW": "台湾",
    "US": "美国",
    "VN": "越南",
}


def display_country(country, country_code=""):
    return COUNTRY_NAMES.get((country_code or "").upper(), country or "未知")


def make_nodes(proxies):
    nodes = []
    for index, proxy in enumerate(proxies):
        original_name = str(proxy.get("name") or "").strip()
        nodes.append(
            ProxyNode(
                index=index,
                original_name=original_name,
                proxy=dict(proxy),
                test_name=f"RENAME-NODE-{index:05d}",
            )
        )
    return nodes


def apply_completion_names(nodes):
    counters = defaultdict(int)
    for node in sorted(
        nodes,
        key=lambda item: (
            item.completed_order if item.completed_order is not None else float("inf"),
            item.index,
        ),
    ):
        country = display_country(node.country, node.country_code)
        counters[country] += 1
        node.final_name = f"{country} {counters[country]}"

    return [materialize_proxy(node) for node in sorted(nodes, key=lambda item: item.index)]


def materialize_proxy(node):
    proxy = dict(node.proxy)
    proxy["name"] = node.final_name or "未知"
    return proxy


def apply_nation_names(proxies, nation_cache):
    """兼容旧调用；新流水线使用 apply_completion_names。"""
    nodes = make_nodes(proxies)
    for order, node in enumerate(nodes, start=1):
        nation, code, _ = nation_cache.get(node.server, ("未知", "", 0))
        node.country = nation
        node.country_code = code
        node.completed_order = order
    renamed = apply_completion_names(nodes)
    entries = [
        {"name": proxy["name"], "orig": node.original_name, "type": proxy.get("type")}
        for proxy, node in zip(renamed, nodes)
    ]
    return renamed, entries, defaultdict(int)
