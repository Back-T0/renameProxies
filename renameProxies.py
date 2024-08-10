import yaml
import requests
import socket
import subprocess
import threading
from collections import defaultdict


# 从网址获取YAML文件
def fetch_yaml(url):
    response = requests.get(url)
    response.raise_for_status()
    print(f"文件读取成功: {url}")
    return yaml.safe_load(response.text)


# 解析YAML文件
def parse_yaml(yaml_content):
    return yaml_content.get("proxies", [])


# 收集服务器地址
def collect_servers(proxies):
    domains = set()
    ips = set()
    for proxy in proxies:
        server = proxy.get("server")
        if server:
            try:
                socket.inet_aton(server)  # 检查是否是IP地址
                ips.add(server)
            except socket.error:
                domains.add(server)
    return list(domains), list(ips)


# 获取国家信息
def get_nation_info(server, nation_cache):
    if server in nation_cache:
        return nation_cache[server]

    try:
        socket.inet_aton(server)  # 判断是否为IP地址
        ip = server
    except socket.error:
        ip = socket.gethostbyname(server)  # 获取域名对应的IP

    # 使用 mmdbinspect 获取国家信息
    result = subprocess.run(
        ["mmdbinspect", "-db", "Country.mmdb", ip], capture_output=True, text=True
    )
    output = yaml.safe_load(result.stdout)

    # 确保解析到正确的国家信息
    if output and isinstance(output, list) and "Records" in output[0]:
        records = output[0]["Records"]
        if records:
            record = records[0]["Record"]
            country_info = record.get("country") or record.get("registered_country")
            if country_info:
                nation = country_info["names"].get("zh-CN", "未知")
                nation_cache[server] = nation
                return nation

    # 调试信息
    print(f"域名 {server} 无法检测, ip为 {ip}")

    nation_cache[server] = "未知"
    return "未知"


# 多线程获取所有服务器的国家信息
def fetch_all_nations(domains, ips):
    nation_cache = {}
    threads = []

    def thread_func(server):
        get_nation_info(server, nation_cache)

    for server in domains + ips:
        t = threading.Thread(target=thread_func, args=(server,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return nation_cache


# 重命名代理
def rename_proxies(proxies, nation_cache):
    nation_counter = defaultdict(int)
    new_proxies = []

    for proxy in proxies:
        server = proxy.get("server")
        if server:
            nation = nation_cache.get(server, "未知")
            nation_counter[nation] += 1
            new_name = f"{nation}-{nation_counter[nation]}"
            proxy["name"] = new_name
        new_proxies.append(proxy)

    return new_proxies


# 保存结果到YAML文件
def save_yaml(proxies, output_file):
    with open(output_file, "w") as file:
        yaml.dump({"proxies": proxies}, file, allow_unicode=True)


def main():
    url = "https://mirror.ghproxy.com/https://raw.githubusercontent.com/dongchengjie/airport/main/subs/merged/tested_within.yaml"
    yaml_content = fetch_yaml(url)
    proxies = parse_yaml(yaml_content)

    domains, ips = collect_servers(proxies)
    nation_cache = fetch_all_nations(domains, ips)

    renamed_proxies = rename_proxies(proxies, nation_cache)
    save_yaml(renamed_proxies, "renameProxies.yaml")

    print("所有节点均命名完毕, 已写入 renameProxies.yaml 文件")


if __name__ == "__main__":
    main()
