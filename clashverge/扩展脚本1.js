// 常量定义
const RULES = [
    'DOMAIN-SUFFIX,time.windows.com,DIRECT',
    'GEOSITE,category-ads-all,REJECT',
    // 'RULE-SET,AdRules,REJECT',
    'GEOIP,telegram,默认,no-resolve',
    'GEOIP,cloudflare,默认,no-resolve',
    'GEOIP,facebook,默认,no-resolve',
    'GEOIP,google,默认,no-resolve',
    'GEOIP,netflix,默认,no-resolve',
    'GEOIP,twitter,默认,no-resolve',

    'GEOSITE,category-ai-!cn,大模型',
    'GEOSITE,spotify,默认',
    'GEOSITE,github,默认',
    'GEOSITE,telegram,默认',
    'GEOSITE,twitter,默认',
    'GEOSITE,google,默认',
    'GEOSITE,wikimedia,默认',
    'GEOSITE,category-social-media-!cn,默认',
    'GEOSITE,category-anticensorship,默认',

    'GEOSITE,category-dev-cn,DIRECT',
    'GEOSITE,bing,DIRECT',
    'GEOSITE,microsoft@cn,DIRECT',
    'GEOSITE,microsoft,DIRECT',
    'GEOSITE,tencent,DIRECT',
    'GEOSITE,baidu,DIRECT',
    'GEOSITE,alibaba,DIRECT',
    'GEOSITE,wps,DIRECT',
    'GEOSITE,zhihu,DIRECT',
    'GEOSITE,jetbrains,默认',
    'GEOSITE,docker,DIRECT',
    'GEOSITE,geolocation-cn,DIRECT',

    'GEOIP,lan,DIRECT,no-resolve',
    'GEOIP,CN,DIRECT,no-resolve',
    'GEOSITE,cn,DIRECT',
    'MATCH,其他'
]
const EXCLUDE_KEYWORDS = ['国内', '官网', '官網', '邀请', '剩余', '到期', '訂閱', '新年']
const GEO_DATA_URLS = [
    { geoip: 'https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip-lite.dat' },
    { geosite: 'https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat' },
    { mmdb: 'https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country-lite.mmdb' },
    { asn: 'https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/GeoLite2-ASN.mmdb' }
]
const RULE_PROVIDERS = {
    AdRules: {
        type: 'http',
        url: 'https://raw.githubusercontent.com/Cats-Team/AdRules/main/adrules_domainset.txt',
        interval: 604800,
        proxy: '默认',
        behavior: 'domain',
        format: 'text'
    }
}
function main(config, profileName) {
    const proxies = config['proxies']
    // 过滤不需要的节点
    const excludeRegex = new RegExp(EXCLUDE_KEYWORDS.join('|'))
    const filteredProxies = proxies.filter(p => !excludeRegex.test(p.name))
    // 按地点分组：节点名以空格分隔，取第一个词作为地点
    const groups = filteredProxies.reduce((acc, proxy) => {
        const [location] = proxy.name.split(' ')
        acc[location] ??= []
        acc[location].push(proxy.name)
        return acc
    }, {})
    const proxyGroups = Object.entries(groups).map(([location, names]) => ({
        name: location,
        // type: 'url-test',
        type: 'load-balance',
        strategy: 'round-robin',
        // strategy: 'consistent-hashing',
        interval: '300',
        proxies: names,
        url: 'https://www.gstatic.com/generate_204',
        lazy: true,
        hidden: true
    }))
    const proxy = { name: '默认', type: 'select', proxies: [...Object.keys(groups), 'DIRECT'] }
    const largeModel = { name: '大模型', type: 'select', proxies: [...Object.keys(groups), 'DIRECT'] }
    const match = { name: '其他', type: 'select', proxies: ['默认', 'DIRECT'] }
    proxyGroups.unshift(match)
    proxyGroups.unshift(largeModel)
    proxyGroups.unshift(proxy)
    config['geodata-mode'] = true
    config['gepx-url'] = GEO_DATA_URLS
    config['rule-providers'] = RULE_PROVIDERS
    config['rules'] = RULES
    config['proxy-groups'] = proxyGroups
    return config
}