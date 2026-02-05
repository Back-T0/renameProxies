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
const PROXY_PROVIDERS = {
    'provider1': {
        type: 'http',
        path: './proxy_provider/p1.yaml',
        url: '替换此处',
        interval: 21600,
        filter: `^(?!.*(?:${EXCLUDE_KEYWORDS.join('|')})).+$`,
        override: {
            'additional-suffix': ' | p1'
        }
    },
    'provider2': {
        type: 'http',
        path: './proxy_provider/p2.yaml',
        url: '替换此处',
        interval: 21600,
        filter: `^(?!.*(?:${EXCLUDE_KEYWORDS.join('|')})).+$`,
        override: {
            'additional-suffix': ' | p2'
        }
    }
}
function main(config, profileName) {
    // 错误处理：检查配置对象和代理列表
    if (!config || typeof config !== 'object') {
        return config
    }

    const proxies = config['proxies']
    if (!proxies || !Array.isArray(proxies)) {
        return config
    }

    // 过滤不需要的节点
    const excludeRegex = new RegExp(EXCLUDE_KEYWORDS.join('|'))
    const filteredProxies = proxies.filter(p => p && p.name && !excludeRegex.test(p.name))

    // 按地点分组：节点名以空格分隔，取第一个词作为地点
    const groups = filteredProxies.reduce((acc, proxy) => {
        if (!proxy || !proxy.name) {
            return acc
        }
        const [location] = proxy.name.split(' ')
        if (!location) {
            return acc
        }
        acc[location] ??= []
        acc[location].push(proxy.name)
        return acc
    }, {})

    // 获取所有代理名称（包括被过滤的）用于 '指定' 代理组
    const allProxies = proxies.filter(p => p && p.name).map(p => p.name)

    // 排序分组并添加节点数量
    const renamedGroups = {}
    const sortedEntries = Object.entries(groups)
        .sort((a, b) => {
            const countDiff = (b[1]?.length || 0) - (a[1]?.length || 0)
            return countDiff !== 0 ? countDiff : (a[0] || '').localeCompare(b[0] || '')
        })

    for (const [location, names] of sortedEntries) {
        if (location && Array.isArray(names)) {
            renamedGroups[`${names.length} ${location}`] = names
        }
    }

    // 创建代理组
    const proxyGroups = Object.entries(renamedGroups).map(([location, names]) => {
        if (!location || !Array.isArray(names)) {
            return null
        }
        const useUrlTest = names.length > 5
        const isHidden = names.length < 30
        return {
            name: location,
            type: useUrlTest ? 'url-test' : 'load-balance',
            strategy: useUrlTest ? undefined : 'round-robin',
            interval: '300',
            proxies: names,
            url: 'https://www.gstatic.com/generate_204',
            lazy: true,
            hidden: isHidden
        }
    }).filter(Boolean)

    // 创建特殊代理组
    const groupNames = Object.keys(renamedGroups)
    const all1 = { name: '指定1', type: 'select', proxies: [...allProxies, 'COMPATIBLE'], icon: 'https://www.clashverge.dev/assets/icons/adjust.svg' }
    const all2 = { name: '指定2', type: 'select', proxies: [...allProxies, 'COMPATIBLE'], icon: 'https://www.clashverge.dev/assets/icons/adjust.svg' }
    const all3 = { name: '指定3', type: 'select', proxies: ['COMPATIBLE'], 'include-all-providers': true, icon: 'https://www.clashverge.dev/assets/icons/adjust.svg' }
    const proxy = { name: '默认', type: 'select', proxies: [...groupNames, '指定1', '指定2', '指定3', 'DIRECT'], icon: 'https://www.clashverge.dev/assets/icons/speed.svg' }
    const largeModel = { name: '大模型', type: 'select', proxies: [...groupNames, '指定1', '指定2', '指定3', 'DIRECT'], icon: 'https://www.clashverge.dev/assets/icons/chatgpt.svg' }
    const match = { name: '其他', type: 'select', proxies: ['默认', '指定1', '指定2', '指定3', 'DIRECT'], icon: 'https://www.clashverge.dev/assets/icons/fish.svg' }

    // 合并代理组，特殊组在前
    const allGroups = [proxy, largeModel, match, all1, all2, all3, ...proxyGroups]

    // 配置规则和数据
    config['geodata-mode'] = true
    config['gepx-url'] = GEO_DATA_URLS
    config['rule-providers'] = RULE_PROVIDERS
    config['proxy-providers'] = PROXY_PROVIDERS
    config['rules'] = RULES
    config['proxy-groups'] = allGroups

    return config
}