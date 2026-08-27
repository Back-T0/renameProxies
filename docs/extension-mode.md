# rename-proxies 详细说明

## 概述

rename-proxies 是一个 Clash 代理节点重命名与分组工具。自动拉取远程订阅、通过 MaxMind GeoIP 查询归属国家、按国家重命名节点并生成分组代理组，最终注入模板输出可用的 Clash 配置文件。

## 使用方式

```bash
python -m rename_proxies
```

## 处理流程

```
订阅源 (resource.yaml)
    │
    ▼
拉取远程 YAML 订阅 ──► 解析 proxies 列表
    │
    ▼
DNS 解析 + MaxMind GeoIP 归属查询（多线程）
    │
    ▼
按国家重命名节点（如 "香港 1"、"日本 3"）
    │
    ▼
构建代理组（排除关键词过滤 → 按地区/协议分组 → 生成组结构）
    │
    ▼
注入 template/template.yaml 模板 ──► 输出到 result/ 目录
```

## 节点命名规则

每个代理节点根据 GeoIP 查询结果重命名，格式为：

```
{国家/地区} {序号}
```

- 序号按同国家节点的出现顺序递增，如 `香港 1`、`香港 2`、`日本 1`
- 无法解析归属的节点标记为 `未知`

## 排除关键词

以下关键词匹配的节点会被排除出分组（基于订阅原始名称）：

| 关键词 | 说明 |
|--------|------|
| `国内` | 国内线路 |
| `官网` / `官網` | 官网推广 |
| `邀请` | 邀请链接 |
| `剩余` | 剩余流量提示 |
| `到期` | 到期时间提示 |
| `訂閱` | 订阅相关 |
| `新年` | 节日活动 |
| `以下` | 分隔标记 |
| `客户端` | 客户端下载 |

## 订阅源配置

在 `resource.yaml` 中配置订阅源，支持 `visible_locations` 和 `protocol_groups` 两个可选字段：

```yaml
resource:
  resource1.yaml:
    url: https://example.com/sub.yaml
    visible_locations: ["香港", "日本"]     # 包含模式：仅保留指定地区
    protocol_groups: [trojan, vmess]        # 包含模式：仅保留指定协议
  resource2.yaml:
    url: https://example.com/sub2.yaml
    visible_locations: ["!美国"]            # 排除模式：保留所有地区，排除美国
    protocol_groups: ["!hysteria2"]         # 排除模式：保留所有协议，排除 hysteria2
  resource3.yaml:
    url: https://example.com/sub3.yaml
    visible_locations: []                   # 空：生成分组但不筛选
    protocol_groups: []                     # 空：生成分组但不筛选
  resource4.yaml:
    url: https://example.com/sub4.yaml
    # 不配置：不生成对应分组，不筛选
```

### 字段含义

| 字段 | 不存在 | 空 `[]` | 包含模式 `[a, b]` | 排除模式 `["!a", "!b"]` |
|------|--------|---------|-------------------|------------------------|
| `protocol_groups` | 不生成"指定协议"组 | 生成组，包含所有协议 | 仅含指定协议 | 排除指定协议 |
| `visible_locations` | 不生成"指定地区"组 | 生成组，包含所有地区 | 仅含指定地区 | 排除指定地区 |

### 筛选逻辑

"指定节点"的内容和最终输出的 `proxies` 列表均受筛选影响：

- 两者都不存在 → 全量
- 一个有值 → 按该条件筛选
- 两者都有值 → 取交集
- 两者都为空 `[]` → 全量（不筛选）

## 代理组结构

### 固定 select 组（始终存在）

#### 默认（select）

顶层入口组，用户在此选择代理策略。

| 属性 | 值 |
|------|----|
| 类型 | `select` |
| 可选项 | 指定协议*(可选)、指定地区*(可选)、指定节点、指定供应、DIRECT |

#### 大模型（select）

专为 AI 服务路由设计的组，匹配 `GEOSITE,google-deepmind` 和 `GEOSITE,category-ai-!cn` 等规则。

| 属性 | 值 |
|------|----|
| 类型 | `select` |
| 可选项 | 指定协议*(可选)、指定地区*(可选)、指定节点、指定供应、DIRECT |

#### 其他（select）

兜底组，用于 MATCH 规则。始终不含"默认"。

| 属性 | 值 |
|------|----|
| 类型 | `select` |
| 可选项 | 指定协议*(可选)、指定地区*(可选)、指定节点、指定供应、DIRECT |

#### 指定节点（select）

列出筛选后的节点，支持手动选择单个节点。

| 属性 | 值 |
|------|----|
| 类型 | `select` |
| 可选项 | 筛选后的节点名称 + `COMPATIBLE` |

#### 指定供应（select）

列出所有 proxy-providers 中的节点。

| 属性 | 值 |
|------|----|
| 类型 | `select` |
| 可选项 | `COMPATIBLE`（通过 `include-all-providers: true` 动态加载） |

### 可选 select 组

#### 指定地区（select，可选）

`visible_locations` 存在时生成，列出地区分组名称。

| 属性 | 值 |
|------|----|
| 类型 | `select` |
| 可选项 | 地区分组名 + `COMPATIBLE` |

地区分组（动态生成）：

- **命名格式**：`{节点数} {地区名}`，如 `12 香港`、`8 日本`
- 分组策略根据节点数量自动选择 `url-test`（>20）/ `load-balance`（<=20）
- 所有地区分组默认隐藏（`hidden: true`）

#### 指定协议（select，可选）

`protocol_groups` 存在时生成，列出协议类型分组名称。

| 属性 | 值 |
|------|----|
| 类型 | `select` |
| 可选项 | 协议类型分组名 + `COMPATIBLE` |

协议类型分组（动态生成）：

- **命名格式**：`{节点数} {协议类型}`，如 `12 trojan`、`8 vmess`
- 节点按名称排序（如 `日本 4`、`日本 12`、`香港 1`、`香港 3`）
- 分组策略与地区分组相同
- 所有协议分组默认隐藏（`hidden: true`）

## 分组关系图

```
默认 (select)
├── 指定协议 (select) ──► 协议类型分组（protocol_groups 存在时）
├── 指定地区 (select) ──► 地区分组（visible_locations 存在时）
├── 指定节点 (select) ──► 筛选后的节点
├── 指定供应 (select) ──► proxy-providers
└── DIRECT

大模型 (select)
├── 指定协议（protocol_groups 存在时）
├── 指定地区（visible_locations 存在时）
├── 指定节点
├── 指定供应
└── DIRECT

其他 (select)
├── 指定协议（protocol_groups 存在时）
├── 指定地区（visible_locations 存在时）
├── 指定节点
├── 指定供应
└── DIRECT

12 trojan (url-test / load-balance)  [hidden]（protocol_groups 存在时）
├── 香港 1
├── 日本 4
└── ...

8 vmess (url-test / load-balance)  [hidden]（protocol_groups 存在时）
├── 香港 3
├── 日本 12
└── ...

12 香港 (url-test / load-balance)  [hidden]（visible_locations 存在时）
├── 香港 1
├── 香港 2
└── ...

8 日本 (url-test / load-balance)  [hidden]（visible_locations 存在时）
├── 日本 1
├── 日本 2
└── ...
```

## 模板配置

使用 `template/template.yaml` 作为模板，包含：

- **基础配置**：mixed-port 7897、fake-ip DNS 模式、TUN 模式
- **GeoX 数据源**：使用 MetaCubeX 的 meta-rules-dat
- **DNS 配置**：国内 DNS（223.5.5.5 / doh.pub）+ 国际 DNS（Cloudflare / Google）
- **流量规则**：
  - AI 服务 → 大模型组
  - 国外常用服务（Google、GitHub、Telegram 等）→ 默认组
  - 国内服务 → DIRECT
  - 兜底 → 其他组

## 源文件结构

| 文件 | 职责 |
|------|------|
| `__main__.py` | 程序入口，加载模板与资源配置，启动 pipeline |
| `pipeline.py` | 通用处理流水线（拉取 → 解析 → GeoIP → 重命名 → 输出） |
| `groups.py` | 代理组构建核心逻辑（分组策略、节点过滤、组结构生成） |
| `naming.py` | 节点重命名（GeoIP → 国家名 + 序号） |
| `geoip.py` | DNS 解析 + MaxMind mmdbinspect 国家归属查询 |
| `config.py` | 常量配置（排除关键词、目录路径） |
| `resource_io.py` | 订阅源加载与 YAML 解析 |
| `template_ops.py` | 模板注入（替换 proxies 和 proxy-groups） |
