import os
import re
import yaml
import threading
import time
import ipaddress
import requests
import socket
import subprocess
import base64
import io
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

RESOURCE_FILE = "resource.yaml"
RESOURCE_DIR = "resource"
TEMPLATE_DIR = "template"
RESULT_DIR = "result"

# template2.yaml 仅由 renameProxies1.py 使用（扩展脚本代理组 + 合并模板）
SKIP_TEMPLATES_FOR_NATION = frozenset({"template2.yaml"})

EXCLUDE_KEYWORDS = [
    "国内",
    "官网",
    "官網",
    "邀请",
    "剩余",
    "到期",
    "訂閱",
    "新年",
    "以下",
    "客户端",
]

os.makedirs(RESOURCE_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)


def load_resource_config():
    print("加载资源配置文件...")
    with open(RESOURCE_FILE, "r") as file:
        return yaml.safe_load(file).get("resource", {})


def fetch_yaml(url, filename):
    filepath = os.path.join(RESOURCE_DIR, filename)
    print(f"尝试从 {url} 下载 {filename}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(filepath, "w") as file:
            file.write(response.text)
        print(f"文件下载成功: {filename}")
    except Exception as e:
        print(f"下载失败: {filename}, 使用本地文件. 错误: {e}")

    print(f"读取本地 YAML 文件: {filename}...")
    with open(filepath, "r") as file:
        return yaml.safe_load(file)


def parse_yaml(yaml_content):
    print("解析 YAML 文件...")
    return yaml_content.get("proxies", [])


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
            infos = socket.getaddrinfo(
                s, None, socket.AF_UNSPEC, socket.SOCK_STREAM
            )
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


def generate_number_image_base64(number: int, image_size=(100, 100), font_size=50):
    img = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=font_size)
    text = str(number)
    text_size = draw.textbbox((0, 0), text, font=font)
    text_width = text_size[2] - text_size[0]
    text_height = text_size[3] - text_size[1]
    position = ((image_size[0] - text_width) // 2, (image_size[1] - text_height) // 3)
    draw.text(position, text, fill="black", font=font)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def apply_nation_names(proxies, nation_cache):
    """按 GeoIP 重命名节点，并生成扩展脚本分组所需的 entries。"""
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
        entries.append({"name": (p.get("name") or "").strip(), "orig": orig})
    return new_proxies, entries, nation_counter


def build_extension_proxy_groups(entries):
    """
    与 clashverge/扩展脚本1.js 一致的代理组结构。
    entries: 每项为 {"name": 当前节点名, "orig": 订阅原始名（用于排除关键词）}
    """
    exclude_pat = re.compile("|".join(re.escape(k) for k in EXCLUDE_KEYWORDS))
    groups = defaultdict(list)
    all_names = []
    for e in entries:
        name = (e.get("name") or "").strip()
        orig = (e.get("orig") if e.get("orig") is not None else name).strip()
        if not name:
            continue
        all_names.append(name)
        if exclude_pat.search(orig):
            continue
        parts = re.split(r"[ _-]+", name)
        loc = parts[0] if parts else None
        if loc:
            groups[loc].append(name)

    sorted_items = sorted(groups.items(), key=lambda x: (-len(x[1]), x[0]))
    renamed_groups = {}
    for location, names in sorted_items:
        renamed_groups[f"{len(names)} {location}"] = names

    group_names = list(renamed_groups.keys())
    location_groups = []
    for location_key, names in renamed_groups.items():
        use_url_test = len(names) > 20
        g = {
            "name": location_key,
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
        location_groups.append(g)

    specify_node = {
        "name": "指定节点",
        "type": "select",
        "proxies": [*all_names, "COMPATIBLE"],
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/select.png",
    }
    specify_group = {
        "name": "指定分组",
        "type": "select",
        "proxies": [*group_names, "COMPATIBLE"],
        "icon": "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/urltest.png",
    }
    specify_provider = {
        "name": "指定供应",
        "type": "select",
        "proxies": ["COMPATIBLE"],
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


def rename_proxies(proxies, nation_cache):
    print("重命名代理并创建代理组（经典分区 + 手动/自动选择）...")
    new_proxies, _, nation_counter = apply_nation_names(proxies, nation_cache)
    proxy_groups = []
    for nation, count in nation_counter.items():
        print(f"创建 {nation} 代理组, 共 {count} 个代理.")
        proxy_groups.append(
            {
                "type": "url-test",
                "name": f"{nation}分区",
                "proxies": [f"{nation} {i}" for i in range(1, count + 1)],
                "icon": f"data:image/png;base64,{generate_number_image_base64(count)}",
            }
        )

    all_proxy_names = [p["name"] for p in new_proxies]
    proxy_groups.insert(
        0,
        {
            "type": "select",
            "name": "手动选择",
            "include-all-proxies": True,
            "icon": f"data:image/png;base64,{generate_number_image_base64(len(all_proxy_names))}",
        },
    )
    proxy_groups.insert(
        0,
        {
            "type": "url-test",
            "name": "自动选择",
            "include-all-proxies": True,
            "icon": f"data:image/png;base64,{generate_number_image_base64(len(all_proxy_names))}",
            "hidden": True,
        },
    )
    proxy_groups.insert(
        0,
        {
            "type": "select",
            "name": "默认代理",
            "icon": "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Final.png",
            "proxies": [item["name"] for item in proxy_groups],
        },
    )
    return new_proxies, proxy_groups


def rename_proxies_with_extension_groups(proxies, nation_cache):
    print("重命名代理并创建代理组（扩展脚本1.js 结构）...")
    new_proxies, entries, _ = apply_nation_names(proxies, nation_cache)
    return new_proxies, build_extension_proxy_groups(entries)


def replace_yaml_sections(template_path, new_proxies, new_proxy_groups, output_path):
    print(f"处理模板: {template_path}...")
    with open(template_path, "r") as file:
        yaml_content = yaml.safe_load(file)
    yaml_content["proxies"] = new_proxies
    yaml_content["proxy-groups"] = new_proxy_groups
    with open(output_path, "w") as file:
        yaml.dump(yaml_content, file, allow_unicode=True)
    print(f"生成成功: {output_path}")


def main():
    print("开始处理代理配置...")
    resource_config = load_resource_config()
    templates = [
        os.path.join(TEMPLATE_DIR, t)
        for t in os.listdir(TEMPLATE_DIR)
        if t.endswith(".yaml") and t not in SKIP_TEMPLATES_FOR_NATION
    ]

    for output_file, url in resource_config.items():
        yaml_content = fetch_yaml(url, output_file)
        proxies = parse_yaml(yaml_content)
        domains, ips = collect_servers(proxies)
        nation_cache = fetch_all_nations(domains, ips)
        renamed_proxies, proxy_groups = rename_proxies(proxies, nation_cache)

        for template in templates:
            output_name = os.path.basename(output_file).replace(".yaml", "")
            template_name = os.path.basename(template).replace(".yaml", "")
            result_path = os.path.join(
                RESULT_DIR, f"{output_name}_{template_name}.yaml"
            )
            replace_yaml_sections(template, renamed_proxies, proxy_groups, result_path)
    print("所有代理配置处理完成！")


if __name__ == "__main__":
    main()
