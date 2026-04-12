import os

from renameProxies import (
    RESOURCE_DIR,
    RESOURCE_FILE,
    RESULT_DIR,
    TEMPLATE_DIR,
    collect_servers,
    fetch_all_nations,
    fetch_yaml,
    load_resource_config,
    parse_yaml,
    rename_proxies_with_extension_groups,
    replace_yaml_sections,
)

TEMPLATE2_NAME = "template2.yaml"


def main():
    print("开始处理代理配置（renameProxies1：与 renameProxies 相同流程，代理组为扩展脚本结构）...")
    resource_config = load_resource_config()
    template2 = os.path.join(TEMPLATE_DIR, TEMPLATE2_NAME)
    if not os.path.isfile(template2):
        print(f"未找到模板 {template2}，退出。")
        return

    for output_file, url in resource_config.items():
        yaml_content = fetch_yaml(url, output_file)
        proxies = parse_yaml(yaml_content)
        domains, ips = collect_servers(proxies)
        nation_cache = fetch_all_nations(domains, ips)
        renamed_proxies, proxy_groups = rename_proxies_with_extension_groups(
            proxies, nation_cache
        )
        output_name = os.path.basename(output_file).replace(".yaml", "")
        template_name = TEMPLATE2_NAME.replace(".yaml", "")
        result_path = os.path.join(RESULT_DIR, f"{output_name}_{template_name}.yaml")
        replace_yaml_sections(template2, renamed_proxies, proxy_groups, result_path)
    print("renameProxies1 处理完成！")


if __name__ == "__main__":
    os.makedirs(RESOURCE_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
    main()
