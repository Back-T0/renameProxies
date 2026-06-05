import os

from .config import RESOURCE_DIR, RESULT_DIR, TEMPLATE_DIR
from .resource_io import load_resource_config
from .pipeline import run_pipeline


def _load_templates():
    return [
        os.path.join(TEMPLATE_DIR, t)
        for t in os.listdir(TEMPLATE_DIR)
        if t.endswith(".yaml")
    ]


def main():
    os.makedirs(RESOURCE_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)

    print("开始处理代理配置...")
    resource_config = load_resource_config()
    templates = _load_templates()
    if not templates:
        print("未找到可用模板，退出。")
        return
    run_pipeline(resource_config, templates)
    print("所有代理配置处理完成！")


if __name__ == "__main__":
    main()
