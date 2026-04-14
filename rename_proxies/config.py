RESOURCE_FILE = "resource.yaml"
RESOURCE_DIR = "resource"
TEMPLATE_DIR = "template"
RESULT_DIR = "result"

# template2.yaml 仅由 renameProxies1.py 使用（扩展脚本代理组 + 合并模板）
SKIP_TEMPLATES_FOR_NATION = frozenset({"template2.yaml"})

EXCLUDE_KEYWORDS = [
    "国内",
    "官网",
    "官網",
    "邀请",
    "剩余",
    "到期",
    "訂閱",
    "新年",
    "以下",
    "客户端",
]

VISIBLE_LOCATIONS = {"香港", "台湾", "日本", "新加坡", "韩国"}

# True: “指定节点/指定分组”仅保留 VISIBLE_LOCATIONS；False: 保持全量。
LIMIT_SPECIFY_TO_VISIBLE_LOCATIONS = True
