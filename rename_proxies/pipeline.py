import os

from .config import RESULT_DIR
from .geoip import collect_servers, fetch_all_nations
from .resource_io import fetch_yaml, parse_yaml
from .template_ops import replace_yaml_sections


def run_pipeline(resource_config, templates, rename_func):
    """
    通用处理流程：
    拉取订阅 -> 解析节点 -> GeoIP 归属 -> 重命名/分组 -> 写入模板输出。
    """
    for output_file, url in resource_config.items():
        yaml_content = fetch_yaml(url, output_file)
        proxies = parse_yaml(yaml_content)
        domains, ips = collect_servers(proxies)
        nation_cache = fetch_all_nations(domains, ips)
        renamed_proxies, proxy_groups = rename_func(proxies, nation_cache)

        output_name = os.path.basename(output_file).replace(".yaml", "")
        for template in templates:
            template_name = os.path.basename(template).replace(".yaml", "")
            result_path = os.path.join(
                RESULT_DIR, f"{output_name}_{template_name}.yaml"
            )
            replace_yaml_sections(template, renamed_proxies, proxy_groups, result_path)
