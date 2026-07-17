# Rename-proxies

通过 Mihomo 让 Clash 节点真实出网，按出口国家/地区重命名节点并生成可直接使用的配置。节点实测失败时，工具使用服务器地址的 GeoIP 结果兜底，不会仅因测试超时或连接失败而丢弃节点。

## 工作流程

```text
订阅拉取 -> 节点解析 -> Mihomo 并发实测 -> 出口 IP 国家查询
                                      \-> 失败节点 GeoIP 兜底
                  -> 按测试完成顺序编号 -> 注入模板 -> result/
```

- 单个 Mihomo 进程承载全部节点；多个独立选择器和监听端口支持安全并发测试
- 默认 20 并发、3 秒超时、1 次重试，适合在 GitHub Actions 中批量处理
- 出口 IP 和 GeoIP 查询均有运行时缓存；并发遇到相同键时只发起一次查询
- 最终名称使用 `国家/地区 + 序号`，例如 `日本 1`、`美国 1`
- 编号依据实测完成顺序，最终代理列表仍保持订阅中的原始排列
- 不再支持 `visible_locations` 和 `protocol_groups`

## 环境要求

- Python 3.11+
- [Mihomo](https://github.com/MetaCubeX/mihomo)，命令名默认为 `mihomo`
- [mmdbinspect](https://github.com/maxmind/mmdbinspect)
- MaxMind 格式的 `Country.mmdb`

安装 Python 包：

```bash
pip install -e .
```

Linux 下可下载 GeoIP 依赖：

```bash
wget -q https://github.com/Dreamacro/maxmind-geoip/releases/latest/download/Country.mmdb
wget -q https://github.com/maxmind/mmdbinspect/releases/download/v2.0.0/mmdbinspect_2.0.0_linux_amd64.deb
sudo apt-get install -y ./mmdbinspect_2.0.0_linux_amd64.deb
```

## 配置

`resource.yaml` 包含订阅源、Mihomo 测试参数和国家查询参数：

```yaml
resource:
  output.yaml:
    url: https://example.com/subscription.yaml

mihomo:
  binary: mihomo
  concurrency: 20
  timeout: 3
  retries: 1
  retry_backoff: 0.3
  startup_timeout: 10
  probe_urls:
    - https://api64.ipify.org?format=json
    - https://api.ipify.org?format=json

location:
  timeout: 5
  providers: [ipapi, ipinfo]
```

环境变量：

- `MIHOMO_BIN`：覆盖 Mihomo 可执行文件路径
- `MIHOMO_CONCURRENCY`：覆盖测试并发数
- `IPINFO_TOKEN`：可选的 IPinfo API token

`ipapi` 对应 ipapi.is，`ipinfo` 对应 ipinfo.io。工具按配置顺序尝试服务，并对相同出口 IP 复用查询结果。

## 运行

```bash
python -m rename_proxies
# 或安装后运行
rename-proxies
```

每个订阅与 `template/` 中的每个模板组合生成一个 `result/<订阅>_<模板>.yaml` 文件。模板的 `proxies` 和 `proxy-groups` 会被替换，其他配置保持不变。

## 失败处理

以下情况触发服务器 GeoIP 兜底：Mihomo 节点连接失败、探测超时、探测接口未返回有效 IP，或出口 IP 国家查询失败。Mihomo 本身无法启动时，该订阅的所有节点都会兜底，并在控制台输出明确原因。

若服务器地址也无法解析或 `mmdbinspect`/`Country.mmdb` 不可用，节点会保留并命名为 `未知 N`。

## 测试

```bash
python -m unittest discover -s tests -v
```

GitHub Actions 会安装 Mihomo、GeoIP 数据库和 mmdbinspect，再执行相同的处理流程。
