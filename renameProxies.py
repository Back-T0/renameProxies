import re
import yaml
import requests
import socket
import subprocess
import threading
from collections import defaultdict

def fetch_yaml(url):
    """下载并解析 YAML 文件，去除不兼容的字符串标签"""
    response = requests.get(url)
    response.raise_for_status()
    yaml_text = re.sub(r'!\<str\>\s*', '', response.text)
    print(f"成功读取 YAML 文件: {url}")
    return yaml.safe_load(yaml_text)

def parse_yaml(yaml_content):
    """解析 YAML 文件，提取代理列表"""
    return yaml_content.get("proxies", [])

def collect_servers(proxies):
    """提取代理服务器的 IP 和域名"""
    domains, ips = set(), set()
    for proxy in proxies:
        server = proxy.get("server")
        if server:
            (ips if is_valid_ip(server) else domains).add(server)
    return list(domains), list(ips)

def is_valid_ip(address):
    """检查地址是否是有效的 IP"""
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False

def get_nation_info(server, nation_cache):
    """获取服务器的国家信息，使用缓存优化查询"""
    if server in nation_cache:
        return nation_cache[server]

    ip = server if is_valid_ip(server) else socket.gethostbyname(server)
    result = subprocess.run(["mmdbinspect", "-db", "Country.mmdb", ip], capture_output=True, text=True)
    output = yaml.safe_load(result.stdout)

    if output and isinstance(output, list) and "Records" in output[0]:
        record = output[0]["Records"][0]["Record"]
        country_info = record.get("country") or record.get("registered_country")
        if country_info:
            nation = country_info["names"].get("zh-CN", "未知")
            iso_code = country_info.get("iso_code", "cn")
            nation_cache[server] = (nation, iso_code, 0)
            return nation_cache[server]

    nation_cache[server] = ("未知", "cn", 0)
    return nation_cache[server]

def fetch_all_nations(domains, ips):
    """使用多线程批量获取所有服务器的国家信息"""
    nation_cache = {}
    threads = [threading.Thread(target=get_nation_info, args=(server, nation_cache)) for server in domains + ips]
    [t.start() for t in threads]
    [t.join() for t in threads]
    return nation_cache

def rename_proxies(proxies, nation_cache):
    """重命名代理并创建代理分组"""
    nation_counter = defaultdict(int)
    for proxy in proxies:
        server = proxy.get("server")
        if server:
            nation, iso_code, _ = nation_cache.get(server, ("未知", "cn", 0))
            nation_counter[nation] += 1
            proxy["name"] = f"{nation}-{nation_counter[nation]}"
            nation_cache[server] = (nation, iso_code, nation_counter[nation])
    return proxies, [{"type": "select", "name": "默认代理", "proxies": [p["name"] for p in proxies]}]

def replace_yaml_sections(template_path, new_proxies, new_proxy_groups, output_path):
    """更新 YAML 文件中的代理和代理组"""
    with open(template_path, "r") as file:
        yaml_content = yaml.safe_load(file)
    yaml_content.update({"proxies": new_proxies, "proxy-groups": new_proxy_groups})
    with open(output_path, "w") as file:
        yaml.dump(yaml_content, file, allow_unicode=True)
    print(f"更新配置文件: {output_path}")

def process_yaml(url, output_path):
    """下载 YAML 并处理代理数据"""
    proxies = parse_yaml(fetch_yaml(url))
    domains, ips = collect_servers(proxies)
    nation_cache = fetch_all_nations(domains, ips)
    renamed_proxies, proxy_groups = rename_proxies(proxies, nation_cache)
    replace_yaml_sections("template.yaml", renamed_proxies, proxy_groups, output_path)

def main():
    process_yaml("https://raw.githubusercontent.com/dongchengjie/airport/main/subs/merged/tested_within.yaml", "finalConfig.yaml")
    process_yaml("https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.yaml", "finalConfig1.yaml")

if __name__ == "__main__":
    main()
