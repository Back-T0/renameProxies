# Rename-proxies

基于 GeoIP 的 Clash 代理节点重命名与分组工具。

自动获取远程订阅节点，通过 MaxMind GeoIP 数据库解析每个节点的服务器所在国家/地区，按国家重命名节点（如"香港 1"、"日本 3"），生成分类代理组，并注入到 Clash 配置模板中，输出可直接使用的 Clash 配置文件。

## 功能

- 从 `resource.yaml` 配置的远程订阅链接获取代理节点列表
- 通过 DNS 解析 + `mmdbinspect` 查询 MaxMind `Country.mmdb` 数据库，获取节点所属国家/地区
- 按国家名称 + 序号重命名节点，过滤掉包含排除关键词的无效节点
- 按地区和协议类型动态生成代理组，支持三态配置控制筛选
- 将重命名后的节点和代理组注入 Clash 配置模板，输出到 `result/` 目录
- 支持 CI 自动运行（GitHub Actions 每 2 小时定时执行 + push 触发）

## 安装

### 环境要求

- Python >= 3.11
- [mmdbinspect](https://github.com/maxmind/mmdbinspect)（MMDB 数据库查询工具）
- `Country.mmdb`（MaxMind GeoIP 数据库）

### 安装 mmdbinspect

```bash
wget https://github.com/maxmind/mmdbinspect/releases/latest -O mmdbinspect.deb
sudo dpkg -i mmdbinspect.deb
```

### 下载 GeoIP 数据库

精简版（推荐）：

```bash
wget https://github.com/Loyalsoldier/geoip/releases/latest/download/Country.mmdb -O Country.mmdb
```

原版：

```bash
wget https://github.com/Dreamacro/maxmind-geoip/releases/latest/download/Country.mmdb -O Country.mmdb
```

### 安装 Python 依赖

```bash
pip install requests pyyaml
```

或以可编辑方式安装项目：

```bash
pip install -e .
```

## 使用方法

```bash
# 使用模块方式运行
PYTHONPATH=src python -m rename_proxies
# 或使用安装后的入口命令
rename-proxies
```

## 项目结构

```text
├── pyproject.toml                    # 项目构建配置
├── resource.yaml                     # 订阅源配置
├── src/rename_proxies/
│   ├── __main__.py                   # 程序入口
│   ├── config.py                     # 常量配置（排除关键词、目录路径）
│   ├── geoip.py                      # GeoIP 查询（DNS 解析 + mmdbinspect）
│   ├── groups.py                     # 代理组构建
│   ├── naming.py                     # 节点重命名
│   ├── pipeline.py                   # 核心流水线：获取 → 解析 → 查询 → 重命名 → 输出
│   ├── resource_io.py                # YAML 订阅获取与解析
│   └── template_ops.py              # 配置模板合并
├── template/
│   └── template.yaml                 # Clash 配置模板
├── resource/                         # 下载的订阅文件（gitignored）
├── result/                           # 生成的输出配置（gitignored）
└── clashverge/                       # Clash Verge 参考配置
```

## 配置说明

### 订阅源 (`resource.yaml`)

定义远程订阅链接，支持 `visible_locations` 和 `protocol_groups` 两个可选字段，均采用三态逻辑：

```yaml
resource:
  resource1.yaml:
    url: https://example.com/subscribe
    visible_locations: ["香港", "日本"]  # 有值：仅保留指定地区
    protocol_groups: [trojan, vmess]     # 有值：仅保留指定协议
  resource2.yaml:
    url: https://example.com/sub2.yaml
    visible_locations: []                # 空：生成分组但不筛选
    protocol_groups: []                  # 空：生成分组但不筛选
  resource3.yaml:
    url: https://example.com/sub3.yaml
    # 不配置：不生成对应分组，不筛选
```

### 三态含义

| 字段 | 不存在 | 存在但为空 `[]` | 存在且有值 |
|------|--------|----------------|-----------|
| `protocol_groups` | 不生成"指定协议"组，不筛选协议 | 生成组，包含所有协议，不筛选 | 生成组，仅含指定协议，筛选节点 |
| `visible_locations` | 不生成"指定地区"组，不筛选地区 | 生成组，包含所有地区，不筛选 | 生成组，仅含指定地区，筛选节点 |

当两者都有值时，取交集筛选节点。

### 排除关键词 (`config.py`)

默认过滤包含以下关键词的节点：国内、官网、官網、邀请、剩余、到期、訂閱、新年、以下、客户端

### 代理组结构

三个固定组（默认、大模型、其他）始终存在，基础可选项为指定节点、指定供应、DIRECT。"其他"组始终不含"默认"。

可选组（由 resource.yaml 控制）：
- **指定协议** — 按节点 `type` 字段（trojan、vmess 等）动态生成协议分组
- **指定地区** — 按节点所在地区动态生成地区分组

可选组存在时会插入到三个固定组的 DIRECT 之前。

详细说明见 [docs/extension-mode.md](docs/extension-mode.md)。

## Clash Verge 集成

`clashverge/` 目录包含 Clash Verge 的参考配置：

- `clash-verge-dev-script-backup.js` — Clash Verge 完整备份配置
- `DNS覆写.yaml` — DNS 覆写配置
- `扩展脚本1.js` — Clash Verge JS 扩展脚本，实现与本工具相同的分组逻辑

## GeoIP 数据库资源

- [Loyalsoldier/geoip](https://github.com/Loyalsoldier/geoip) — 精简版 GeoIP 数据库
- [Dreamacro/maxmind-geoip](https://github.com/Dreamacro/maxmind-geoip) — 原版 GeoIP 数据库
- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community/tree/master/data) — geosite 域名列表
- [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) — 第三方 GeoIP 规则

## CI/CD

GitHub Actions 工作流每 2 小时自动运行（也可 push 触发或手动触发），执行以下步骤：

1. 安装 Python 依赖、下载 `Country.mmdb` 和 `mmdbinspect`
2. 运行 `rename-proxies`
3. 自动提交并推送生成的配置变更
