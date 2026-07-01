import yaml


class _QuotedString(str):
    """标记需要在 YAML 中强制使用双引号输出的字符串类型。"""
    pass


def _quoted_string_representer(dumper, data):
    """
    自定义 YAML 序列化器。

    当遇到 _QuotedString 类型时，始终以双引号字符串输出，例如：
        short-id: "abc123"
    """
    return dumper.represent_scalar(
        "tag:yaml.org,2002:str",
        data,
        style='"',
    )


# 注册自定义字符串类型的序列化规则
yaml.SafeDumper.add_representer(_QuotedString, _quoted_string_representer)


def _quote_short_id(value):
    """
    递归遍历 dict / list。

    将所有键名为 "short-id" 的字符串值包装为 _QuotedString，
    使其在导出 YAML 时始终保留双引号，其余数据保持不变。
    """
    if isinstance(value, dict):
        return {
            key: (
                _QuotedString(val)
                if key == "short-id" and isinstance(val, str)
                else _quote_short_id(val)
            )
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [_quote_short_id(item) for item in value]

    return value


def replace_yaml_sections(
    template_path,
    new_proxies,
    new_proxy_groups,
    output_path,
):
    """
    根据模板生成新的 YAML 配置文件。

    参数：
        template_path: 模板 YAML 文件路径。
        new_proxies: 新的 proxies 配置。
        new_proxy_groups: 新的 proxy-groups 配置。
        output_path: 输出文件路径。
    """
    print(f"处理模板: {template_path}...")

    # 读取模板配置
    with open(template_path, "r", encoding="utf-8") as file:
        yaml_content = yaml.safe_load(file)

    # 替换指定配置项
    # 对 proxies 中的 short-id 字段进行特殊处理，保证输出时带双引号
    yaml_content["proxies"] = _quote_short_id(new_proxies)
    yaml_content["proxy-groups"] = new_proxy_groups

    # 写入新的 YAML 文件，保持 Unicode 字符及键顺序
    with open(output_path, "w", encoding="utf-8") as file:
        yaml.dump(
            yaml_content,
            file,
            allow_unicode=True,
            Dumper=yaml.SafeDumper,
            sort_keys=False,
        )

    print(f"生成成功: {output_path}")