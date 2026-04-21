import re
from collections import defaultdict
from functools import lru_cache

from .config import (
    EXCLUDE_KEYWORDS,
    LIMIT_SPECIFY_TO_VISIBLE_LOCATIONS,
    VISIBLE_LOCATIONS,
)
from .naming import apply_nation_names


def _extract_location(name):
    parts = re.split(r"[ _-]+", (name or "").strip())
    return parts[0] if parts else None


@lru_cache(maxsize=1)
def _get_exclude_pattern():
    if not EXCLUDE_KEYWORDS:
        return None
    return re.compile("|".join(re.escape(k) for k in EXCLUDE_KEYWORDS))


def build_extension_proxy_groups(entries):
    """
    与 clashverge/扩展脚本1.js 一致的代理组结构。
    entries: 每项为 {"name": 当前节点名, "orig": 订阅原始名（用于排除关键词）}
    """
    exclude_pat = _get_exclude_pattern()
    groups = defaultdict(list)
    all_names = []
    for e in entries:
        name = (e.get("name") or "").strip()
        orig = (e.get("orig") if e.get("orig") is not None else name).strip()
        if not name:
            continue
        all_names.append(name)
        if exclude_pat and exclude_pat.search(orig):
            continue
        loc = _extract_location(name)
        if loc:
            groups[loc].append(name)

    sorted_items = sorted(groups.items(), key=lambda x: (-len(x[1]), x[0]))
    renamed_groups = {}
    for location, names in sorted_items:
        renamed_groups[f"{len(names)} {location}"] = names

    group_names = list(renamed_groups.keys())
    location_groups = []
    visible_node_names = []
    visible_group_names = []
    for location_key, names in renamed_groups.items():
        use_url_test = len(names) > 20
        location_name = (
            location_key.split(" ", 1)[1] if " " in location_key else location_key
        )
        if location_name in VISIBLE_LOCATIONS:
            visible_node_names.extend(names)
            visible_group_names.append(location_key)
        g = {
            "name": location_key,
            "type": "url-test" if use_url_test else "load-balance",
            "proxies": names,
            "url": "http://www.gstatic.com/generate_204",
            "lazy": True,
            "hidden": not LIMIT_SPECIFY_TO_VISIBLE_LOCATIONS,
        }
        if use_url_test:
            g["interval"] = "180"
            g["timeout"] = "300"
        else:
            g["strategy"] = "round-robin"
            g["interval"] = "500"
            g["timeout"] = "800"
        location_groups.append(g)

    specify_node_proxies = [*all_names, "COMPATIBLE"]
    specify_group_proxies = [*group_names, "COMPATIBLE"]
    if LIMIT_SPECIFY_TO_VISIBLE_LOCATIONS:
        specify_node_proxies = [*visible_node_names, "COMPATIBLE"]
        specify_group_proxies = [*visible_group_names, "COMPATIBLE"]

    specify_node = {
        "name": "指定节点",
        "type": "select",
        "proxies": specify_node_proxies,
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/select.png",
    }
    specify_group = {
        "name": "指定分组",
        "type": "select",
        "proxies": specify_group_proxies,
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/urltest.png",
    }
    specify_provider = {
        "name": "指定供应",
        "type": "select",
        "proxies": ["COMPATIBLE","DIRECT"],
        "include-all-providers": True,
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/fallback.png",
    }
    default_sel = {
        "name": "默认",
        "type": "select",
        "proxies": ["指定节点", "指定分组", "指定供应", "DIRECT"],
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/relay.png",
    }
    large_model = {
        "name": "大模型",
        "type": "select",
        "proxies": ["指定节点", "指定分组", "指定供应", "DIRECT"],
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/anthropic.png",
    }
    match = {
        "name": "其他",
        "type": "select",
        "proxies": ["默认", "指定节点", "指定分组", "指定供应", "DIRECT"],
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/loadbalance.png",
    }
    return [
        default_sel,
        large_model,
        match,
        specify_node,
        specify_group,
        specify_provider,
        *location_groups,
    ]


def rename_proxies_with_extension_groups(proxies, nation_cache):
    print("重命名代理并创建代理组（扩展脚本1.js 结构）...")
    new_proxies, entries, _ = apply_nation_names(proxies, nation_cache)
    if LIMIT_SPECIFY_TO_VISIBLE_LOCATIONS:
        filtered_proxies = []
        filtered_entries = []
        for proxy, entry in zip(new_proxies, entries):
            if _extract_location(entry.get("name")) in VISIBLE_LOCATIONS:
                filtered_proxies.append(proxy)
                filtered_entries.append(entry)
        new_proxies = filtered_proxies
        entries = filtered_entries
    return new_proxies, build_extension_proxy_groups(entries)
