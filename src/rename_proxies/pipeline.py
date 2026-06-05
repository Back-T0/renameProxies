import os

from .config import RESULT_DIR
from .geoip import collect_servers, fetch_all_nations
from .groups import rename_proxies
from .resource_io import fetch_yaml
from .template_ops import replace_yaml_sections


def run_pipeline(resource_config, templates):
    """
    通用处理流程：
    拉取订阅 -> 解析节点 -> GeoIP 归属 -> 重命名/分组 -> 写入模板输出。
    """
    for output_file, resource_options in resource_config.items():
        url = resource_options.get("url", "")
        if not url:
            print(f"资源 {output_file} 缺少 url，已跳过。")
            continue

        visible_locations = resource_options.get("visible_locations")
        protocol_groups = resource_options.get("protocol_groups")
        yaml_content = fetch_yaml(url, output_file)
        proxies = yaml_content.get("proxies", [])
        domains, ips = collect_servers(proxies)
        nation_cache = fetch_all_nations(domains, ips)
        renamed_proxies, proxy_groups = rename_proxies(
            proxies, nation_cache,
            visible_locations=visible_locations,
            protocol_groups=protocol_groups,
        )

        output_name = os.path.basename(output_file).replace(".yaml", "")
        for template in templates:
            template_name = os.path.basename(template).replace(".yaml", "")
            result_path = os.path.join(
                RESULT_DIR, f"{output_name}_{template_name}.yaml"
            )
            replace_yaml_sections(template, renamed_proxies, proxy_groups, result_path)
