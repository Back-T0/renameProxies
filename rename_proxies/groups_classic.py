from .naming import apply_nation_names, generate_number_image_base64


def rename_proxies(
    proxies,
    nation_cache,
    limit_specify_to_visible_locations=None,
    visible_locations=None,
):
    print("重命名代理并创建代理组（经典分区 + 手动/自动选择）...")
    new_proxies, _, nation_counter = apply_nation_names(proxies, nation_cache)
    proxy_groups = []
    for nation, count in nation_counter.items():
        print(f"创建 {nation} 代理组, 共 {count} 个代理.")
        proxy_groups.append(
            {
                "type": "url-test",
                "name": f"{nation}分区",
                "proxies": [f"{nation} {i}" for i in range(1, count + 1)],
                "icon": f"data:image/png;base64,{generate_number_image_base64(count)}",
            }
        )

    all_proxy_names = [p["name"] for p in new_proxies]
    proxy_groups.insert(
        0,
        {
            "type": "select",
            "name": "手动选择",
            "include-all-proxies": True,
            "icon": f"data:image/png;base64,{generate_number_image_base64(len(all_proxy_names))}",
        },
    )
    proxy_groups.insert(
        0,
        {
            "type": "url-test",
            "name": "自动选择",
            "include-all-proxies": True,
            "icon": f"data:image/png;base64,{generate_number_image_base64(len(all_proxy_names))}",
            "hidden": True,
        },
    )
    proxy_groups.insert(
        0,
        {
            "type": "select",
            "name": "默认代理",
            "icon": "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Final.png",
            "proxies": [item["name"] for item in proxy_groups],
        },
    )
    return new_proxies, proxy_groups
