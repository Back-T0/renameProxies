/*
 * ┌─────────────────────────────────────────────────────┐
 * │                       AeraGroup                     │
 * └───────┬─────────────────┬───────────────────┬───────┘
 *         │                 │                   │
 * ┌───────▼───────┐ ┌───────▼──────┐     ┌──────▼───────┐
 * │      Ch       │ │      En      │ ... │    Others    │
 * └─┬─────┬─────┬─┘ └─┬─────┬───┬──┘     └──────────────┘
 *   │ ... │     │     │ ... │   │
 *   ▼     ▼     ▼     ▼     ▼   ▼
 *   Ch1...Ch4 Proxies En1...En4 Proxies
 *
 * ┌─────────────────┐ ┌──────┐   ┌────────────┐
 * │  DefaultGroup   │ │      │   │            ├────►Ch1
 * └─────┬──────────┬┘ │      │   │    Area    ├────►En1
 *       │          │  │      │   │    Group   │      .
 * ┌─────▼────────┐ │  │      ├───►    Test    │      .
 * │    Default   │ │  │      │   │            │      .
 * │    Proxies   │ │  │      │   │            ├────►Others1
 * └───────────┬─┬┘ │  │      │   └────────────┘
 *             │ │  │  │      │   ┌────────────┐
 * ┌─────────┐ │ │  │  │      │   │            ├────►Ch2
 * │AreaGroup◄─┘ │  │  │      │   │            ├────►En2
 * └─────────┘   │  │  │      ├───►    Area    │      .
 *               │  │  │      │   │   Group    │      .
 * ┌─────────────▼┐ │  │      │   │  Fallback  │      .
 * │  SelectGroup ◄─┘  │ Auto │   │            ├────►Others2
 * └───────────┬─┬┘    │ Area │   └────────────┘
 *             │ │     │Group │   ┌────────────┐
 * ┌─────────┐ │ │     │      │   │            ├────►Ch3
 * │AutoGroup│◄┘ │     │      │   │    Area    ├────►En3
 * └─────────┘   │     │      │   │   Group    │      .
 *               │     │      ├───►Consistent  │      .
 *  AllProxies◄──┘     │      │   │            │      .
 *                     │      │   │            ├────►Others3
 *                     │      │   └────────────┘
 *                     │      │   ┌────────────┐
 *                     │      │   │            ├────►Ch4
 *                     │      │   │            ├────►En4
 *                     ├───┘  ├──►    Area    │      .
 *                     │      │   │   Group    │      .
 *                     │      │   │ RoundRobin │      .
 *                     │      │   │            ├────►Others4
 *                     └──────┘   └────────────┘
 */

// ─── 规则 ───────────────────────────────────────────────
const rules = [
  // 自定义规则
  "DOMAIN-SUFFIX,v2rayse.com,默认代理",
  "DOMAIN-SUFFIX,limbopro.com,默认代理",
  "DOMAIN-SUFFIX,downloadlynet.ir,DIRECT",
  "DOMAIN-SUFFIX,microsofttranslator.com,默认代理",
  "PROCESS-NAME,WinStore.App.exe,默认代理",
  "DOMAIN-SUFFIX,challenges.cloudflare.com,默认代理",

  // 编程相关
  "DOMAIN-SUFFIX,postman.com,默认代理",
  "PROCESS-NAME,Postman.exe,默认代理",
  "DOMAIN-SUFFIX,mybatis.org,默认代理",
  "DOMAIN-SUFFIX,projectlombok.org,默认代理",
  "DOMAIN-SUFFIX,thymeleaf.org,默认代理",
  "DOMAIN-SUFFIX,flywaydb.org,默认代理",
  "DOMAIN-SUFFIX,red-gate.com,默认代理",
  "DOMAIN-SUFFIX,jquery.com,默认代理",
  "DOMAIN-SUFFIX,claude.ai,OpenAi服务",
  "DOMAIN-SUFFIX,anthropic.com,OpenAi服务",

  // 规则集
  "RULE-SET,BanAD常见广告关键字、广告联盟,广告过滤",

  // subdivision 分组规则集
  "RULE-SET,OpenAi域名列表,OpenAi服务",
  "DOMAIN-SUFFIX,openai.com,OpenAi服务",
  "RULE-SET,Spotify声破天域名列表,Spotify服务",
  "RULE-SET,Microsoft微软域名列表,微软服务",
  "RULE-SET,ProxyMedia国外媒体列表,国外媒体",

  // 单独域名规则集
  "RULE-SET,Tencent腾讯域名列表,DIRECT",
  "RULE-SET,Alibaba阿里域名列表,DIRECT",
  "RULE-SET,Wechat微信域名列表,DIRECT",
  "RULE-SET,Baidu百度域名列表,DIRECT",
  "RULE-SET,Bilibili哔哩哔哩域名列表,DIRECT",
  "RULE-SET,Google谷歌域名列表,默认代理",
  "RULE-SET,Github域名列表,默认代理",
  "RULE-SET,Developer开发者常用域名列表,默认代理",
  "RULE-SET,iCloud域名列表,默认代理",
  "RULE-SET,apple在中国大陆可直连的域名列表,默认代理",
  "RULE-SET,Telegram使用的IP地址列表,默认代理,no-resolve",

  // 百以上规则集
  "RULE-SET,lancidr局域网IP及保留IP地址列表,DIRECT,no-resolve",
  "RULE-SET,private私有网络专用域名列表,DIRECT",
  "RULE-SET,applications需要直连的常见软件列表,DIRECT",
  "RULE-SET,google在中国大陆可直连的域名列表,DIRECT",

  // 其他规则
  "GEOIP,LAN,DIRECT,no-resolve",
  "GEOIP,CN,DIRECT,no-resolve",
  "MATCH,漏网之鱼",
];

// ─── DNS ────────────────────────────────────────────────
const domesticNameservers = [
  "https://dns.alidns.com/dns-query",
  "https://doh.pub/dns-query",
  "https://doh.360.cn/dns-query",
];
const foreignNameservers = [
  "https://1.1.1.1/dns-query",
  "https://1.0.0.1/dns-query",
  "https://208.67.222.222/dns-query",
  "https://208.67.220.220/dns-query",
  "https://194.242.2.2/dns-query",
  "https://194.242.2.3/dns-query",
];

const dnsConfig = {
  dns: true,
  listen: 1053,
  ipv6: true,
  "use-system-hosts": false,
  "cache-algorithm": "arc",
  "enhanced-mode": "fake-ip",
  "fake-ip-range": "198.18.0.1/16",
  "default-nameserver": ["223.5.5.5", "114.114.114.114", "1.1.1.1", "8.8.8.8"],
  nameserver: [...domesticNameservers, ...foreignNameservers],
  "proxy-server-nameserver": [...domesticNameservers, ...foreignNameservers],
  "nameserver-policy": {
    "geosite:private,cn,geolocation-cn": domesticNameservers,
    "geosite:google,youtube,telegram,gfw,geolocation-!cn": foreignNameservers,
  },
  "fake-ip-filter": [
    "+.lan",
    "+.local",
    "+.msftconnecttest.com",
    "+.msftncsi.com",
    "localhost.ptlogin2.qq.com",
    "localhost.sec.qq.com",
    "localhost.work.weixin.qq.com",
  ],
};

// ─── 规则集 Provider ────────────────────────────────────
const BASE_RULE_URL = "https://fastly.jsdelivr.net/gh/Loyalsoldier/clash-rules@release";
const ACL4SSR_URL = "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash";

const ruleAnchor = {
  domain:    { type: "http", format: "yaml", interval: 86400, behavior: "domain" },
  ipcidr:    { type: "http", format: "yaml", interval: 86400, behavior: "ipcidr" },
  classical: { type: "http", format: "yaml", interval: 86400, behavior: "classical" },
};

// 从 (name, anchor, file) 三元组批量生成 Loyalsoldier 规则集
function makeRuleProviders(entries) {
  return Object.fromEntries(
    entries.map(([name, anchor, file]) => [
      name,
      { ...ruleAnchor[anchor], url: `${BASE_RULE_URL}/${file}`, path: `./rulesets/loyalsoldier/${file.replace(".txt", ".yaml")}` },
    ])
  );
}

const loyalsoldierRules = makeRuleProviders([
  ["reject广告域名列表",           "domain",    "reject.txt"],
  ["iCloud域名列表",              "domain",    "icloud.txt"],
  ["apple在中国大陆可直连的域名列表", "domain",    "apple.txt"],
  ["google在中国大陆可直连的域名列表", "domain",    "google.txt"],
  ["proxy代理域名列表",            "domain",    "proxy.txt"],
  ["direct直连域名列表",           "domain",    "direct.txt"],
  ["private私有网络专用域名列表",    "domain",    "private.txt"],
  ["gfw域名列表",                 "domain",    "gfw.txt"],
  ["tld-not-cn非中国大陆使用的顶级域名列表", "domain", "tld-not-cn.txt"],
  ["Telegram使用的IP地址列表",      "ipcidr",    "telegramcidr.txt"],
  ["cncidr中国大陆IP地址列表",      "ipcidr",    "cncidr.txt"],
  ["lancidr局域网IP及保留IP地址列表",  "ipcidr",    "lancidr.txt"],
  ["applications需要直连的常见软件列表", "classical", "applications.txt"],
]);

function makeAcl4ssrRules(entries) {
  return Object.fromEntries(
    entries.map(([name, file]) => {
      const relPath = file.includes("/") ? `Ruleset/${file}` : file;
      return [
        name,
        { ...ruleAnchor.classical, url: `${ACL4SSR_URL}/Providers/${relPath}.yaml`, path: `./rulesets/ACL4SSR/${relPath}.yaml` },
      ];
    })
  );
}

const acl4ssrRules = makeAcl4ssrRules([
  ["ProxyMedia国外媒体列表", "ProxyMedia"],
  ["BanAD常见广告关键字、广告联盟", "BanAD"],
  ["Microsoft微软域名列表", "Ruleset/Microsoft"],
  ["Spotify声破天域名列表", "Ruleset/Spotify"],
  ["Developer开发者常用域名列表", "Ruleset/Developer"],
  ["Github域名列表", "Ruleset/Github"],
  ["OpenAi域名列表", "Ruleset/OpenAi"],
  ["Tencent腾讯域名列表", "Ruleset/Tencent"],
  ["Baidu百度域名列表", "Ruleset/Baidu"],
  ["Wechat微信域名列表", "Ruleset/Wechat"],
  ["Google谷歌域名列表", "Ruleset/Google"],
  ["Bilibili哔哩哔哩域名列表", "Ruleset/Bilibili"],
  ["Alibaba阿里域名列表", "Ruleset/Alibaba"],
]);

const ruleProviders = { ...loyalsoldierRules, ...acl4ssrRules };

// ─── 自定义 Proxies / Providers ─────────────────────────
const appendProxies = [];
// 示例:
// appendProxies.push({ name: "☁️ CFWarp-1", type: "wireguard", server: "188.114.98.234", port: 1387, ... });

const baseOfProxyProvider = {
  type: "http",
  interval: 3600,
  "health-check": { enable: true, url: "https://www.google.com/generate_204", interval: 300 },
};
const appendProxiesProvider = {};

// ─── 区域定义（数据驱动） ────────────────────────────────
const AREA_DEFINITIONS = [
  { name: "WARP",  regex: /WARP|Warp/,          icon: "https://clash-verge-rev.github.io/assets/icons/warp.svg" },
  { name: "中国",  regex: /CN|China|中国/,         icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/CN.png" },
  { name: "香港",  regex: /HK|hk|Hong Kong|HongKong|hongkong|香港/, icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/HK.png" },
  { name: "澳门",  regex: /MO|Macao|Macau|澳门/,    icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/MO.png" },
  { name: "台湾",  regex: /TW|Taiwan|台湾|新北|彰化/,  icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/TW.png" },
  { name: "日本",  regex: /JP|Japan|日本|川日|东京|大阪|泉日|埼玉|沪日|深日/, icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/JP.png" },
  { name: "韩国",  regex: /KR|Korea|KOR|首尔|韓|韩国/, icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/KR.png" },
  { name: "新加坡", regex: /SG|Singapore|新加坡|坡|狮城/, icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/SG.png" },
  { name: "俄罗斯", regex: /RU|Russia|俄罗斯|莫斯科/,  icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/RU.png" },
  { name: "美国",  regex: /US|United States|美国|波特兰|达拉斯|俄勒冈|凤凰城|费利蒙|硅谷|拉斯维加斯|洛杉矶|圣何塞|圣克拉拉|西雅图|芝加哥/, icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/US.png" },
  { name: "英国",  regex: /UK|GBR|GB|United Kingdom|英国/, icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/UK.png" },
  { name: "法国",  regex: /FR|France|法国|巴黎|里昂/,  icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/FR.png" },
  { name: "加拿大", regex: /CA|加拿大/,             icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/CA.png" },
  { name: "德国",  regex: /DE|Germany|德国/,        icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/DE.png" },
  { name: "澳大利亚", regex: /AU|Australia|澳大利亚/, icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/AU.png" },
  { name: "土耳其", regex: /TR|Turkey|土耳其/,       icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/TR.png" },
];

// 代理组通用配置
const baseOfGroup = {
  interval: 300,
  timeout: 1500,
  url: "https://www.google.com/generate_204",
  lazy: true,
  "max-failed-times": 3,
};

// 程序入口
function main(config) {
  // ── 插入自定义 proxies ──────────────────────────────
  if (config.proxies == null || !Array.isArray(config.proxies)) {
    config.proxies = [...appendProxies];
  } else {
    config.proxies = [...config.proxies, ...appendProxies];
  }

  if (config["proxy-providers"] == null || typeof config["proxy-providers"] !== "object") {
    config["proxy-providers"] = { ...appendProxiesProvider };
  } else {
    config["proxy-providers"] = { ...config["proxy-providers"], ...appendProxiesProvider };
  }

  // ── 空检测 ──────────────────────────────────────────
  const hasCustomProxies = config.proxies.length > 0;
  const hasCustomProviders = Object.keys(config["proxy-providers"]).length > 0;
  if (!hasCustomProxies && !hasCustomProviders) {
    throw new Error("配置文件中未找到任何代理");
  }

  // 剔除多余节点
  const excludeKeywords = ["官网", "暂时", "购买渠道", "IPV6", "国内", "佣金"];
  const proxies = config.proxies
    .filter(p => !excludeKeywords.some(kw => p.name.includes(kw)))
    .map(p => p.name);

  // ── 自动分组 ────────────────────────────────────────
  const baseOfAutoGroup = {
    ...baseOfGroup,
    proxies,
    "include-all-providers": true,
    hidden: true,
  };
  const autoGroup = [
    { ...baseOfAutoGroup, name: "延迟选优",         type: "url-test",      tolerance: 100, icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Auto.png" },
    { ...baseOfAutoGroup, name: "故障转移",         type: "fallback",                       icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Speedtest.png" },
    { ...baseOfAutoGroup, name: "负载均衡(散列)",   type: "load-balance", strategy: "consistent-hashing", icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Round_Robin_Alt.png" },
    { ...baseOfAutoGroup, name: "负载均衡(轮询)",   type: "load-balance", strategy: "round-robin",         icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Round_Robin.png" },
  ];
  const autoGroupList = autoGroup.map(g => g.name);

  // ── 区域分组 ────────────────────────────────────────
  const dividedProxies = [];
  let proxiesCountOfArea = 0;

  const nameFilter = regex => {
    const matched = proxies.filter(e => regex.test(e));
    dividedProxies.push(...matched);
    proxiesCountOfArea = matched.length;
    return matched;
  };
  const unDividedProxies = () => {
    const remaining = proxies.filter(p => !dividedProxies.includes(p));
    proxiesCountOfArea += remaining.length;
    return remaining;
  };

  const baseOfAreaGroup = {
    ...baseOfGroup,
    type: "url-test",
    "include-all-providers": true,
    hidden: true,
  };

  // 先生成前 N-1 个（非"其他"）区域
  const knownAreaGroups = AREA_DEFINITIONS.map(def => ({
    ...baseOfAreaGroup,
    proxies: [...nameFilter(def.regex)],
    name: `${def.name}分区：${proxiesCountOfArea}个`,
    filter: def.regex.source,
    icon: def.icon,
  }));

  // "其他分区"：补充剩余未匹配节点
  const otherAreaGroup = {
    ...baseOfAreaGroup,
    proxies: [...nameFilter(/🇮🇳|🇦🇺|🇹🇷|🇧🇷|🇦🇷|🇻🇳|印度|土耳其|巴西|阿根廷|越南/), ...unDividedProxies()],
    name: `其他分区：${proxiesCountOfArea}个`,
    filter: "🇮🇳|🇦🇺|🇹🇷|🇧🇷|🇦🇷|🇻🇳|印度|土耳其|巴西|阿根廷|越南",
    icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/XD.png",
  };

  const areaGroup = [...knownAreaGroups, otherAreaGroup].filter(g => g.proxies.length > 0);
  const areaList = areaGroup.map(g => g.name);

  // ── 默认代理组 ──────────────────────────────────────
  const nameOfSelect = `节点选择：${proxies.length}个`;
  const defaultGroup = [
    { ...baseOfGroup, name: "默认代理", type: "select", proxies: ["DIRECT", nameOfSelect, ...areaList], icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Proxy.png" },
    { ...baseOfGroup, name: nameOfSelect, type: "select", proxies: [...autoGroupList, ...proxies], "include-all-providers": true, icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Available.png" },
    { ...baseOfGroup, name: "漏网之鱼", type: "select", proxies: ["DIRECT", "默认代理", nameOfSelect, ...areaList], icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Final.png" },
    { ...baseOfGroup, name: "广告过滤", type: "select", proxies: ["REJECT", "REJECT-DROP", "DIRECT"], icon: "https://fastly.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Dark/Reject.png" },
  ];

  // ── Subdivision 代理组 ──────────────────────────────
  const baseOfSubdivisionGroup = {
    ...baseOfGroup,
    type: "select",
    proxies: ["DIRECT", "默认代理", nameOfSelect, ...areaList],
  };
  const subdivisionGroup = [
    { ...baseOfSubdivisionGroup, name: "OpenAi服务",  icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/OpenAI.png" },
    { ...baseOfSubdivisionGroup, name: "Spotify服务", icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/Spotify.png" },
    { ...baseOfSubdivisionGroup, name: "国外媒体",    icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/Streaming.png" },
    { ...baseOfSubdivisionGroup, name: "微软服务",    icon: "https://fastly.jsdelivr.net/gh/Orz-3/mini@master/Color/Microsoft.png" },
  ];

  // ── 覆盖配置 ────────────────────────────────────────
  config["proxy-groups"] = [...defaultGroup, ...subdivisionGroup, ...autoGroup, ...areaGroup];
  config["rule-providers"] = ruleProviders;
  config["rules"] = rules;
  config["dns"] = dnsConfig;

  return config;
}
