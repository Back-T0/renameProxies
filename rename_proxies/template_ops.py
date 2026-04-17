import yaml


def _filter_proxies_without_short_id(proxies):
    filtered = [
        proxy for proxy in proxies if not (isinstance(proxy, dict) and "short-id" in proxy)
    ]
    removed_count = len(proxies) - len(filtered)
    print(f"_filter_proxies_without_short_id: 移除了 {removed_count} 个包含 'short-id' 的代理，剩余 {len(filtered)} 个代理。")
    print("过滤掉的节点名称：", [proxy.get("name", proxy) for proxy in filtered])
    return filtered


def replace_yaml_sections(template_path, new_proxies, new_proxy_groups, output_path):
    print(f"处理模板: {template_path}...")
    with open(template_path, "r") as file:
        yaml_content = yaml.safe_load(file)
    yaml_content["proxies"] = _filter_proxies_without_short_id(new_proxies)
    yaml_content["proxy-groups"] = new_proxy_groups
    with open(output_path, "w") as file:
        yaml.dump(yaml_content, file, allow_unicode=True, sort_keys=False)
    print(f"生成成功: {output_path}")
