import os

from rename_proxies import (
    RESOURCE_DIR,
    RESULT_DIR,
    TEMPLATE_DIR,
    load_resource_config,
    rename_proxies_with_extension_groups,
    run_pipeline,
)

TEMPLATE2_NAME = "template2.yaml"


def main():
    print("开始处理代理配置（renameProxies1：与 renameProxies 相同流程，代理组为扩展脚本结构）...")
    resource_config = load_resource_config()
    template2 = os.path.join(TEMPLATE_DIR, TEMPLATE2_NAME)
    if not os.path.isfile(template2):
        print(f"未找到模板 {template2}，退出。")
        return

    run_pipeline(resource_config, [template2], rename_proxies_with_extension_groups)
    print("renameProxies1 处理完成！")


if __name__ == "__main__":
    os.makedirs(RESOURCE_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
    main()
