import yaml


class _SingleQuotedStr(str):
    """Marker type for YAML single-quoted scalar output."""


class _SingleQuoteDumper(yaml.SafeDumper):
    pass


def _repr_single_quoted_str(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")


_SingleQuoteDumper.add_representer(_SingleQuotedStr, _repr_single_quoted_str)


def _quote_short_id_values(obj):
    if isinstance(obj, dict):
        converted = {}
        for k, v in obj.items():
            if k == "short-id" and isinstance(v, str):
                converted[k] = _SingleQuotedStr(v)
            else:
                converted[k] = _quote_short_id_values(v)
        return converted
    if isinstance(obj, list):
        return [_quote_short_id_values(item) for item in obj]
    return obj


def replace_yaml_sections(template_path, new_proxies, new_proxy_groups, output_path):
    print(f"处理模板: {template_path}...")
    with open(template_path, "r") as file:
        yaml_content = yaml.safe_load(file)
    yaml_content["proxies"] = new_proxies
    yaml_content["proxy-groups"] = new_proxy_groups
    yaml_content = _quote_short_id_values(yaml_content)
    with open(output_path, "w") as file:
        yaml.dump(
            yaml_content, file, Dumper=_SingleQuoteDumper, allow_unicode=True, sort_keys=False
        )
    print(f"生成成功: {output_path}")
