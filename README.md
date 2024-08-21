1. 数据库
	- 精简简数据库 `wget https://github.com/Loyalsoldier/geoip/releases/latest/download/Country.mmdb -O Country.mmdb` 
	- 原数据库 `wget https://github.com/Dreamacro/maxmind-geoip/releases/latest/download/Country.mmdb -O Country.mmdb`
	- geosite 域名列表: [https://github.com/v2fly/domain-list-community/tree/master/data](https://github.com/v2fly/domain-list-community/tree/master/data)
	- GeoIP 第三方: https://github.com/MetaCubeX/meta-rules-dat

2. 解析数据库的软件包
	- 下载软件包 `wget https://github.com/maxmind/mmdbinspect/releases/latest -O mmdbinspect.deb`
	- 安装软件包 `sudo dpkg -i mmdbinspect.deb`
	- 使用方法 https://github.com/maxmind/mmdbinspect?tab=readme-ov-file#examples
	  mmdbinspect -db Country.mmdb 8.217.239.116 36.151.195.51


geoip 配置示例: [快捷配置 - 虚空终端 Docs (metacubex.one)](https://wiki.metacubex.one/example/conf/)

配置说明: [策略组配置 - 虚空终端 Docs (metacubex.one)](https://wiki.metacubex.one/config/proxy-groups/)

