import re
from collections import defaultdict

from .config import EXCLUDE_KEYWORDS
from .naming import apply_nation_names


def _extract_location(name):
    parts = re.split(r"[ _-]+", (name or "").strip())
    return parts[0] if parts else None


_EXCLUDE_PATTERN = (
    re.compile("|".join(re.escape(k) for k in EXCLUDE_KEYWORDS))
    if EXCLUDE_KEYWORDS
    else None
)


def _parse_filter_list(items):
    """
    解析筛选列表，返回 (include_set, exclude_set)。
    - 包含模式: ["trojan", "vmess"] → ({"trojan","vmess"}, None)
    - 排除模式: ["!hysteria2", "!ss"] → (None, {"hysteria2","ss"})
    - 混合时排除项忽略，仅取非排除项
    """
    if not items:
        return None, None
    excludes = {v[1:] for v in items if v.startswith("!")}
    includes = {v for v in items if not v.startswith("!")}
    if excludes and not includes:
        return None, excludes
    if includes:
        return includes, None
    return None, None


def _match_filter(value, include_set, exclude_set):
    """判断 value 是否通过筛选。"""
    if include_set is not None:
        return value in include_set
    if exclude_set is not None:
        return value not in exclude_set
    return True


def _make_location_groups(location_map, include_set, exclude_set):
    """生成地区分组，按 include/exclude 筛选。"""
    groups = []
    group_names = []
    for location, names in sorted(
        location_map.items(), key=lambda x: (-len(x[1]), x[0])
    ):
        if not _match_filter(location, include_set, exclude_set):
            continue
        key = f"{len(names)} {location}"
        group_names.append(key)
        use_url_test = len(names) > 20
        g = {
            "name": key,
            "type": "url-test" if use_url_test else "load-balance",
            "proxies": names,
            "url": "http://www.gstatic.com/generate_204",
            "lazy": True,
            "hidden": True,
        }
        if use_url_test:
            g["interval"] = "180"
            g["timeout"] = "300"
        else:
            g["strategy"] = "round-robin"
            g["interval"] = "500"
            g["timeout"] = "800"
        groups.append(g)
    return groups, group_names


def _make_protocol_groups(protocol_map, include_set, exclude_set):
    """生成协议分组，按 include/exclude 筛选。"""
    groups = []
    group_names = []
    for proto, names in sorted(protocol_map.items(), key=lambda x: (-len(x[1]), x[0])):
        if not _match_filter(proto, include_set, exclude_set):
            continue
        names.sort()
        key = f"{len(names)} {proto}"
        group_names.append(key)
        use_url_test = len(names) > 20
        g = {
            "name": key,
            "type": "url-test" if use_url_test else "load-balance",
            "proxies": names,
            "url": "http://www.gstatic.com/generate_204",
            "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/loon.png",
            "lazy": True,
            "hidden": True,
        }
        if use_url_test:
            g["interval"] = "180"
            g["timeout"] = "300"
        else:
            g["strategy"] = "round-robin"
            g["interval"] = "500"
            g["timeout"] = "800"
        groups.append(g)
    return groups, group_names


def build_proxy_groups(proxies, entries, visible_locations=None, protocol_groups=None):
    """
    构建代理组结构。
    visible_locations / protocol_groups:
      None=不生成组/不筛选, []=生成但不筛选,
      ["a","b"]=仅含a和b, ["!a","!b"]=排除a和b。
    返回 (groups_list, output_proxies)。
    """
    exclude_pat = _EXCLUDE_PATTERN

    has_location = visible_locations is not None
    has_protocol = protocol_groups is not None

    loc_inc, loc_exc = _parse_filter_list(visible_locations)
    proto_inc, proto_exc = _parse_filter_list(protocol_groups)

    # 第一遍: 按地区和协议分组, 同时收集筛选后的节点
    location_map = defaultdict(list)
    protocol_map = defaultdict(list)
    filtered_names = []
    filtered_proxies = []
    for proxy, entry in zip(proxies, entries):
        name = (entry.get("name") or "").strip()
        orig = (entry.get("orig") if entry.get("orig") is not None else name).strip()
        if not name:
            continue
        if exclude_pat and exclude_pat.search(orig):
            continue
        loc = _extract_location(name)
        proto = entry.get("type")
        if loc:
            location_map[loc].append(name)
        if proto:
            protocol_map[proto].append(name)
        # 筛选: 需要同时满足所有激活的筛选条件
        loc_ok = not has_location or _match_filter(loc, loc_inc, loc_exc)
        proto_ok = not has_protocol or _match_filter(proto, proto_inc, proto_exc)
        if loc_ok and proto_ok:
            filtered_names.append(name)
            filtered_proxies.append(proxy)

    # 生成地区分组
    if has_location:
        loc_groups, loc_group_names = _make_location_groups(
            location_map, loc_inc, loc_exc,
        )
    else:
        loc_groups, loc_group_names = [], []

    # 生成协议分组
    if has_protocol:
        proto_groups, proto_group_names = _make_protocol_groups(
            protocol_map, proto_inc, proto_exc,
        )
    else:
        proto_groups, proto_group_names = [], []

    # 固定 select 组
    specify_node = {
        "name": "指定节点",
        "type": "select",
        "proxies": [*filtered_names, "COMPATIBLE"],
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/categoryproductivity.png",
    }
    specify_provider = {
        "name": "指定供应",
        "type": "select",
        "proxies": ["COMPATIBLE"],
        "include-all-providers": True,
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/cisco.png",
    }

    # 可选 select 组
    specify_location = None
    if has_location:
        specify_location = {
            "name": "指定地区",
            "type": "select",
            "proxies": [*loc_group_names, "COMPATIBLE"],
            "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/urltest.png",
        }
    specify_protocol = None
    if has_protocol:
        specify_protocol = {
            "name": "指定协议",
            "type": "select",
            "proxies": [*proto_group_names, "COMPATIBLE"],
            "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/fallback.png",
        }

    # 构建三大固定组的可选项列表
    def _fixed_proxies():
        opts = []
        if specify_protocol:
            opts.append("指定协议")
        if specify_location:
            opts.append("指定地区")
        opts.extend(["指定节点", "指定供应", "DIRECT"])
        return opts

    default_sel = {
        "name": "默认",
        "type": "select",
        "proxies": _fixed_proxies(),
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/relay.png",
    }
    large_model = {
        "name": "大模型",
        "type": "select",
        "proxies": _fixed_proxies(),
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/anthropic.png",
    }
    match = {
        "name": "其他",
        "type": "select",
        "proxies": _fixed_proxies(),
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/loadbalance.png",
    }

    # 组装输出
    groups_list = [
        default_sel,
        large_model,
        match,
        specify_node,
        specify_provider,
    ]
    if specify_location:
        groups_list.append(specify_location)
    if specify_protocol:
        groups_list.append(specify_protocol)
    groups_list.extend(loc_groups)
    groups_list.extend(proto_groups)

    return groups_list, filtered_proxies


def rename_proxies(proxies, nation_cache, visible_locations=None, protocol_groups=None):
    print("重命名代理并创建代理组...")
    new_proxies, entries, _ = apply_nation_names(proxies, nation_cache)
    groups, filtered_proxies = build_proxy_groups(
        new_proxies,
        entries,
        visible_locations=visible_locations,
        protocol_groups=protocol_groups,
    )
    return filtered_proxies, groups
