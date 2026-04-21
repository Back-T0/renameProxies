import os

import requests
import yaml

from .config import RESOURCE_DIR, RESOURCE_FILE


def load_resource_config():
    print("加载资源配置文件...")
    with open(RESOURCE_FILE, "r") as file:
        raw_resources = (yaml.safe_load(file) or {}).get("resource", {})

    resource_config = {}
    for output_file, value in raw_resources.items():
        if isinstance(value, str):
            resource_config[output_file] = {
                "url": value,
                "limit_specify_to_visible_locations": None,
                "visible_locations": None,
            }
            continue

        if isinstance(value, dict):
            resource_config[output_file] = {
                "url": value.get("url", ""),
                "limit_specify_to_visible_locations": value.get(
                    "limit_specify_to_visible_locations"
                ),
                "visible_locations": value.get("visible_locations"),
            }
            continue

        print(f"资源配置格式不正确: {output_file}, 已跳过。")
    return resource_config


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
