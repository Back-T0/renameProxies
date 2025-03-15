import os
import yaml
import threading
import requests
import socket
import subprocess
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import base64
import io

RESOURCE_FILE = "resource.yaml"
RESOURCE_DIR = "resource"
TEMPLATE_DIR = "template"
RESULT_DIR = "result"

os.makedirs(RESOURCE_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)


def load_resource_config():
    print("加载资源配置文件...")
    with open(RESOURCE_FILE, "r") as file:
        return yaml.safe_load(file).get("resource", {})


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

    print(f"读取本地 YAML 文件: {filename}...")
    with open(filepath, "r") as file:
        return yaml.safe_load(file)


def parse_yaml(yaml_content):
    print("解析 YAML 文件...")
    return yaml_content.get("proxies", [])


def collect_servers(proxies):
    print("收集代理服务器信息...")
    domains, ips = set(), set()
    for proxy in proxies:
        server = proxy.get("server")
        if server:
            try:
                socket.inet_aton(server)
                ips.add(server)
            except socket.error:
                domains.add(server)
    print(f"发现 {len(domains)} 个域名, {len(ips)} 个 IP 地址.")
    return list(domains), list(ips)


def get_nation_info(server, nation_cache):
    if server in nation_cache:
        return nation_cache[server]
    # print(f"查询 {server} 的国家信息...")
    try:
        ip = server if socket.inet_aton(server) else socket.gethostbyname(server)
    except socket.error:
        nation_cache[server] = ("未知", "cn", 0)
        print(f"无法解析 {server}, 设置为未知.")
        return nation_cache[server]

    result = subprocess.run(
        ["mmdbinspect", "-db", "Country.mmdb", ip], capture_output=True, text=True
    )
    output = yaml.safe_load(result.stdout)
    record = output["record"]
    if output and "record" in output:
        country_info = record.get("country") or record.get("registered_country")
        if country_info:
            nation = country_info["names"].get("zh-CN", "未知")
            iso_code = country_info.get("iso_code", "cn")
            nation_cache[server] = (nation, iso_code, 0)
            print(f"{server} 归属 {nation} ({iso_code})")
            return nation_cache[server]

    nation_cache[server] = ("未知", "cn", 0)
    print(f"无法确定 {server} 的归属国家.")
    return nation_cache[server]


def fetch_all_nations(domains, ips):
    print("获取所有服务器的国家信息...")
    nation_cache, threads = {}, []

    def thread_func(server):
        get_nation_info(server, nation_cache)

    for server in domains + ips:
        t = threading.Thread(target=thread_func, args=(server,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    return nation_cache


def generate_number_image_base64(number: int, image_size=(100, 100), font_size=50):
    # 创建空白图像
    img = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=font_size)

    # 计算文本位置，使其居中
    text = str(number)
    text_size = draw.textbbox((0, 0), text, font=font)  # 获取文本尺寸
    text_width, text_height = text_size[2] - text_size[0], text_size[3] - text_size[1]
    position = ((image_size[0] - text_width) // 2, (image_size[1] - text_height) // 3)

    # 绘制文本
    draw.text(position, text, fill="black", font=font)

    # 将图片保存到内存
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # 转换为 Base64
    base64_str = base64.b64encode(buffer.getvalue()).decode()
    return base64_str


def rename_proxies(proxies, nation_cache):
    print("重命名代理并创建代理组...")
    nation_counter, new_proxies, proxy_groups = defaultdict(int), [], []
    for proxy in proxies:
        server = proxy.get("server")
        if server:
            nation, iso_code, _ = nation_cache.get(server, ("未知", "cn", 0))
            nation_counter[nation] += 1
            proxy["name"] = f"{nation}-{nation_counter[nation]}"
        new_proxies.append(proxy)

    for nation, count in nation_counter.items():
        print(f"创建 {nation} 代理组, 共 {count} 个代理.")
        proxy_groups.append(
            {
                "type": "url-test",
                "name": f"{nation}分区",
                "proxies": [f"{nation}-{i}" for i in range(1, count + 1)],
                "icon": f"data:image/png;base64,{generate_number_image_base64(count)}",
            }
        )

    all_proxy_names = [p["name"] for p in new_proxies]
    proxy_groups.insert(
        0,
        {
            "type": "select",
            "name": f"手动选择",
            "include-all-proxies": True,
            "icon": f"data:image/png;base64,{generate_number_image_base64(len(all_proxy_names))}",
        },
    )
    proxy_groups.insert(
        0,
        {
            "type": "url-test",
            "name": f"自动选择",
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


def replace_yaml_sections(template_path, new_proxies, new_proxy_groups, output_path):
    print(f"处理模板: {template_path}...")
    with open(template_path, "r") as file:
        yaml_content = yaml.safe_load(file)
    yaml_content["proxies"], yaml_content["proxy-groups"] = (
        new_proxies,
        new_proxy_groups,
    )
    with open(output_path, "w") as file:
        yaml.dump(yaml_content, file, allow_unicode=True)
    print(f"生成成功: {output_path}")


def main():
    print("开始处理代理配置...")
    resource_config = load_resource_config()
    templates = [
        os.path.join(TEMPLATE_DIR, t)
        for t in os.listdir(TEMPLATE_DIR)
        if t.endswith(".yaml")
    ]

    for output_file, url in resource_config.items():
        yaml_content = fetch_yaml(url, output_file)
        proxies = parse_yaml(yaml_content)
        domains, ips = collect_servers(proxies)
        nation_cache = fetch_all_nations(domains, ips)
        renamed_proxies, proxy_groups = rename_proxies(proxies, nation_cache)

        for template in templates:
            output_name = os.path.basename(output_file).replace(".yaml", "")
            template_name = os.path.basename(template).replace(".yaml", "")
            result_path = os.path.join(
                RESULT_DIR, f"{output_name}_{template_name}.yaml"
            )
            replace_yaml_sections(template, renamed_proxies, proxy_groups, result_path)
    print("所有代理配置处理完成！")


if __name__ == "__main__":
    main()
