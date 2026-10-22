import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import RESULT_DIR
from .geoip import GeoIPResolver
from .groups import build_proxy_groups, filter_proxies
from .location import LocationResolver
from .mihomo import MihomoController, MihomoError
from .naming import apply_completion_names, make_nodes
from .resource_io import fetch_yaml
from .template_ops import replace_yaml_sections


def _apply_geoip_fallback(nodes, resolver, concurrency):
    failed = [node for node in nodes if node.status != "success"]

    def resolve(node):
        location = resolver.lookup(node.server)
        node.country = location.country
        node.country_code = location.country_code
        node.location_source = "geoip"
        return node

    if not failed:
        return
    with ThreadPoolExecutor(max_workers=min(concurrency, len(failed))) as executor:
        futures = [executor.submit(resolve, node) for node in failed]
        for future in as_completed(futures):
            future.result()


def process_proxies(proxies, settings, mihomo_factory=MihomoController):
    proxies = filter_proxies(proxies)
    nodes = make_nodes(proxies)
    if not nodes:
        return [], []

    location_resolver = LocationResolver(settings.location)
    controller = mihomo_factory(settings.mihomo)
    try:
        try:
            controller.start(nodes)
            controller.test_nodes(nodes, location_resolver)
        except MihomoError as exc:
            print(f"Mihomo 无法启动，全部节点转为 GeoIP 兜底: {exc}")
            for order, node in enumerate(nodes, start=1):
                node.status = "failed"
                node.error = str(exc)
                node.completed_order = order
    finally:
        controller.close()

    _apply_geoip_fallback(nodes, GeoIPResolver(), settings.mihomo.concurrency)
    renamed = apply_completion_names(nodes)
    return renamed, build_proxy_groups(renamed)


def run_pipeline(resource_config, templates, settings):
    for output_file, resource_options in resource_config.items():
        url = resource_options.get("url", "")
        if not url:
            print(f"资源 {output_file} 缺少 url，已跳过。")
            continue

        yaml_content = fetch_yaml(url, output_file)
        if not isinstance(yaml_content, dict):
            print(f"{output_file}: 返回内容不是 Clash YAML，已跳过。")
            continue
        proxies = yaml_content.get("proxies") or []
        if not isinstance(proxies, list):
            print(f"{output_file}: proxies 字段格式不正确，已跳过。")
            continue
        print(f"{output_file}: 开始实测 {len(proxies)} 个节点...")
        renamed_proxies, proxy_groups = process_proxies(proxies, settings)

        output_name = os.path.splitext(os.path.basename(output_file))[0]
        for template in templates:
            template_name = os.path.splitext(os.path.basename(template))[0]
            result_path = os.path.join(
                RESULT_DIR, f"{output_name}_{template_name}.yaml"
            )
            replace_yaml_sections(template, renamed_proxies, proxy_groups, result_path)
