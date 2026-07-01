import os

import requests
import yaml

from .config import RESOURCE_DIR, RESOURCE_FILE


def load_resource_config():
    print("加载资源配置文件...")
    if not os.path.exists(RESOURCE_FILE):
        raise FileNotFoundError(f"资源配置文件不存在: {RESOURCE_FILE}")
    with open(RESOURCE_FILE, "r") as file:
        raw_resources = (yaml.safe_load(file) or {}).get("resource", {})

    resource_config = {}
    for output_file, value in raw_resources.items():
        if isinstance(value, str):
            resource_config[output_file] = {
                "url": value,
                "visible_locations": None,
                "protocol_groups": None,
            }
            continue

        if isinstance(value, dict):
            # 三态: 字段不存在→None, 存在但为空→[], 存在且有值→[值]
            vl = value.get("visible_locations")
            pg = value.get("protocol_groups")
            resource_config[output_file] = {
                "url": value.get("url", ""),
                "visible_locations": list(vl) if vl is not None else (None if "visible_locations" not in value else []),
                "protocol_groups": list(pg) if pg is not None else (None if "protocol_groups" not in value else []),
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
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"下载失败且本地文件不存在: {filepath}"
            ) from e

    print(f"读取本地 YAML 文件: {filename}...")
    with open(filepath, "r") as file:
        return yaml.safe_load(file)
