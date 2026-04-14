import os

from rename_proxies import (
    RESOURCE_DIR,
    RESULT_DIR,
    SKIP_TEMPLATES_FOR_NATION,
    TEMPLATE_DIR,
    load_resource_config,
    rename_proxies,
    run_pipeline,
)


def main():
    print("开始处理代理配置...")
    resource_config = load_resource_config()
    templates = [
        os.path.join(TEMPLATE_DIR, t)
        for t in os.listdir(TEMPLATE_DIR)
        if t.endswith(".yaml") and t not in SKIP_TEMPLATES_FOR_NATION
    ]
    run_pipeline(resource_config, templates, rename_proxies)
    print("所有代理配置处理完成！")


if __name__ == "__main__":
    os.makedirs(RESOURCE_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
    main()
