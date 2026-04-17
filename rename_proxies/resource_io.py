import os

import requests
import yaml

from .config import RESOURCE_DIR, RESOURCE_FILE


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
    proxies = yaml_content.get("proxies", [])
    filtered_proxies = []
    removed_names = []

    for proxy in proxies:
        if isinstance(proxy, dict) and "reality-opts" in proxy:
            removed_names.append(proxy.get("name", "<unknown>"))
            continue
        filtered_proxies.append(proxy)

    if removed_names:
        print(f"过滤掉包含 reality-opts 的节点: {', '.join(removed_names)}")

    return filtered_proxies
