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

    result = subprocess.run(
        ["mmdbinspect", "-db", "Country.mmdb", ip], capture_output=True, text=True
    )
    output = yaml.safe_load(result.stdout)

    if output and isinstance(output, list) and "Records" in output[0]:
        records = output[0]["Records"]
        if records:
            record = records[0]["Record"]
            country_info = record.get("country") or record.get("registered_country")
            if country_info:
                nation = country_info["names"].get("zh-CN", "未知")
                iso_code = country_info.get("iso_code", "cn")
                nation_cache[server] = (nation, iso_code, 0)
                return nation_cache[server]

    print(f"域名 {server} 无法检测, ip为 {ip}, 查询内容为 {output}")
    nation_cache[server] = ("未知", "cn", 0)
    return nation_cache[server]


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


# 重命名代理并创建代理组信息
def rename_proxies(proxies, nation_cache):
    nation_counter = defaultdict(int)
    new_proxies = []
    proxy_groups = []

    for proxy in proxies:
        server = proxy.get("server")
        if server:
            nation, iso_code, _ = nation_cache.get(server, ("未知", "cn", 0))
            nation_counter[nation] += 1
            new_name = f"{nation}-{nation_counter[nation]}"
            proxy["name"] = new_name
            nation_cache[server] = (nation, iso_code, nation_counter[nation])
        new_proxies.append(proxy)

    # 创建分区代理组信息
    for nation, count in nation_counter.items():
        # 通过 nation 找到对应的 iso_code
        iso_code = "cn"
        for _, (n, i, _) in nation_cache.items():
            if n == nation:
                iso_code = i
                break

        group = {
            "interval": 300,
            "timeout": 1500,
            "url": "https://www.google.com/generate_204",
            "lazy": True,
            "max-failed-times": 3,
            "type": "url-test",
            # "type": "url-test",
            "type": "load-balance",
            # "strategy": "consistent-hashing",
            "strategy": "round-robin",
            "include-all-providers": False,
            "hidden": False,
            "include-all-proxies": True,
            "filter": f"(?i){nation}|{iso_code}|{iso_code.lower()}",
            "proxies": ["COMPATIBLE"],
            # "proxies": [f"{nation}-{i}" for i in range(1, count + 1)],
            "name": f"{nation}分区: {count}个",
            # "icon": f"https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/{iso_code}.png"
            "icon": f"https://fastly.jsdelivr.net/gh/clash-verge-rev/clash-verge-rev.github.io@main/docs/assets/icons/flags/{iso_code.lower()}.svg",
        }
        print(group["name"])
        proxy_groups.append(group)

    # 创建手动选择代理组
    all_proxy_names = [proxy["name"] for proxy in new_proxies]
    select_group = {
        "type": "select",
        "include-all": True,
        "name": f"手动选择: {len(all_proxy_names)}个",
        "icon": "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Available.png",
    }
    proxy_groups.insert(0, select_group)

    # 创建自动选择代理组(国外)
    overseas_group_name = [
        item
        for item in all_proxy_names
        if not any(keyword in item for keyword in ["中国", "香港"])
    ]
    auto_select_group_exp = {
        "interval": 300,
        "timeout": 1500,
        "url": "https://www.google.com/generate_204",
        "lazy": True,
        "max-failed-times": 3,
        "type": "url-test",
        "include-all-providers": True,
        "hidden": True,
        "proxies": overseas_group_name,
        "name": f"自动选择(国外): {len(overseas_group_name)}个",
        "icon": "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Auto.png",
    }
    proxy_groups.insert(0, auto_select_group_exp)

    # 创建自动选择代理组(国内)
    domestic_group_name = [
        item
        for item in all_proxy_names
        if any(keyword in item for keyword in ["中国", "香港"])
    ]
    auto_select_group_exp = {
        "interval": 300,
        "timeout": 1500,
        "url": "https://www.google.com/generate_204",
        "lazy": True,
        "max-failed-times": 3,
        "type": "url-test",
        "include-all-providers": True,
        "hidden": True,
        "proxies": domestic_group_name,
        "name": f"自动选择(国内): {len(domestic_group_name)}个",
        "icon": "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Auto.png",
    }
    proxy_groups.insert(0, auto_select_group_exp)

    # 创建自动选择代理组
    auto_select_group = {
        "interval": 300,
        "timeout": 1500,
        "url": "https://www.google.com/generate_204",
        "lazy": True,
        "max-failed-times": 3,
        "type": "url-test",
        "include-all-providers": True,
        "hidden": False,
        "include-all": True,
        "name": f"自动选择: {len(all_proxy_names)}个",
        "icon": "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Auto.png",
    }
    proxy_groups.insert(0, auto_select_group)

    # 创建默认代理组
    default_group = {
        "type": "select",
        "name": "默认代理",
        "proxies": [item["name"] for item in proxy_groups],
        "icon": "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Final.png",
    }
    proxy_groups.insert(0, default_group)

    return new_proxies, proxy_groups


# 将新的 proxies 和 proxy-groups 替换到现有的 YAML 文件中
def replace_yaml_sections(template_path, new_proxies, new_proxy_groups, output_path):
    with open(template_path, "r") as file:
        yaml_content = yaml.safe_load(file)

    # 替换 proxies 和 proxy-groups 部分
    yaml_content["proxies"] = new_proxies
    yaml_content["proxy-groups"] = new_proxy_groups

    # 保存更新后的内容
    with open(output_path, "w") as file:
        yaml.dump(yaml_content, file, allow_unicode=True)

    print(f"文件 {output_path} 已成功更新.")


def main():
    url = "https://raw.githubusercontent.com/dongchengjie/airport/main/subs/merged/tested_within.yaml"
    yaml_content = fetch_yaml(url)
    proxies = parse_yaml(yaml_content)

    domains, ips = collect_servers(proxies)
    nation_cache = fetch_all_nations(domains, ips)

    renamed_proxies, proxy_groups = rename_proxies(proxies, nation_cache)

    # 替换并保存到现有的配置文件
    replace_yaml_sections(
        "template.yaml", renamed_proxies, proxy_groups, "finalConfig.yaml"
    )

    url = "https://mirror.ghproxy.com/https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/speednodes.yaml"
    yaml_content = fetch_yaml(url)
    proxies = parse_yaml(yaml_content)

    domains, ips = collect_servers(proxies)
    nation_cache = fetch_all_nations(domains, ips)

    renamed_proxies, proxy_groups = rename_proxies(proxies, nation_cache)

    # 替换并保存到现有的配置文件
    replace_yaml_sections(
        "template.yaml", renamed_proxies, proxy_groups, "finalConfig1.yaml"
    )


if __name__ == "__main__":
    main()
