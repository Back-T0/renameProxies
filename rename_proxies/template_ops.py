import yaml


def replace_yaml_sections(template_path, new_proxies, new_proxy_groups, output_path):
    print(f"处理模板: {template_path}...")
    with open(template_path, "r") as file:
        yaml_content = yaml.safe_load(file)
    yaml_content["proxies"] = new_proxies
    yaml_content["proxy-groups"] = new_proxy_groups
    with open(output_path, "w") as file:
        yaml.dump(yaml_content, file, allow_unicode=True)
    print(f"生成成功: {output_path}")
