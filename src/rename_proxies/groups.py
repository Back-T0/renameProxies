import re

from .config import EXCLUDE_KEYWORDS


_EXCLUDE_PATTERN = (
    re.compile("|".join(re.escape(keyword) for keyword in EXCLUDE_KEYWORDS))
    if EXCLUDE_KEYWORDS
    else None
)


def filter_proxies(proxies):
    output = []
    for proxy in proxies:
        name = str(proxy.get("name") or "").strip()
        if not name or (_EXCLUDE_PATTERN and _EXCLUDE_PATTERN.search(name)):
            continue
        if not proxy.get("server"):
            continue
        output.append(proxy)
    return output


def build_proxy_groups(proxies, entries=None):
    """生成模板规则依赖的固定选择组。"""
    fixed_options = ["指定节点", "指定供应", "DIRECT"]

    icons = {
        "默认": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/relay.png",
        "大模型": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/anthropic.png",
        "其他": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/loadbalance.png",
    }
    groups = [
        {
            "name": name,
            "type": "select",
            "proxies": list(fixed_options),
            "icon": icons[name],
            "hidden": False,
        }
        for name in ("默认", "大模型", "其他")
    ]
    groups.extend(
        [
            {
                "name": "指定节点",
                "type": "select",
                "include-all-proxies": True,
                "proxies": ["COMPATIBLE"],
                "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/categoryproductivity.png",
                "hidden": False,
            },
            {
                "name": "指定供应",
                "type": "select",
                "proxies": ["COMPATIBLE"],
                "include-all-providers": True,
                "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/cisco.png",
                "hidden": False,
            },
        ]
    )
    return groups


def rename_proxies(proxies, nation_cache=None, **_ignored):
    from .naming import apply_nation_names

    renamed, entries, _ = apply_nation_names(proxies, nation_cache or {})
    return renamed, build_proxy_groups(renamed, entries)
