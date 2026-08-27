// ==================== 配置 ====================
// null: 不生成该组/不筛选
// []: 生成组，包含全部，不筛选
// ["a", "b"]: 生成组，仅含指定项，筛选节点
// ["!a", "!b"]: 生成组，排除指定项，筛选节点

const VISIBLE_LOCATIONS = null; // 地区筛选，如 ["香港", "日本"] 或 ["!美国"]
const PROTOCOL_GROUPS = null;   // 协议筛选，如 ["trojan", "vmess"] 或 ["!hysteria2"]

// ==================== 工具函数 ====================

function parseFilterList(items) {
  if (!items || items.length === 0) return { include: null, exclude: null };
  const excludes = items.filter((v) => v.startsWith("!")).map((v) => v.slice(1));
  const includes = items.filter((v) => !v.startsWith("!"));
  if (excludes.length > 0 && includes.length === 0)
    return { include: null, exclude: new Set(excludes) };
  if (includes.length > 0)
    return { include: new Set(includes), exclude: null };
  return { include: null, exclude: null };
}

function matchFilter(value, include, exclude) {
  if (include !== null) return include.has(value);
  if (exclude !== null) return !exclude.has(value);
  return true;
}

function extractLocation(name) {
  const parts = (name || "").trim().split(/[ _-]+/);
  return parts[0] || null;
}

function makeDynamicGroups(groupMap, include, exclude) {
  const groups = [];
  const groupNames = [];
  const sorted = Object.entries(groupMap).sort(
    (a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0])
  );
  for (const [key, names] of sorted) {
    if (!matchFilter(key, include, exclude)) continue;
    const groupName = `${names.length} ${key}`;
    groupNames.push(groupName);
    const useUrlTest = names.length > 20;
    groups.push({
      name: groupName,
      type: useUrlTest ? "url-test" : "load-balance",
      strategy: useUrlTest ? undefined : "round-robin",
      interval: useUrlTest ? "180" : "500",
      timeout: useUrlTest ? "300" : "800",
      proxies: names,
      url: "http://www.gstatic.com/generate_204",
      lazy: true,
      hidden: true,
    });
  }
  return { groups, groupNames };
}

// ==================== 主函数 ====================

function main(config) {
  if (!config || typeof config !== "object") return config;

  const proxies = config["proxies"];
  if (!proxies || !Array.isArray(proxies)) return config;

  const hasLocation = VISIBLE_LOCATIONS !== null;
  const hasProtocol = PROTOCOL_GROUPS !== null;

  // 无需操作时直接返回
  if (!hasLocation && !hasProtocol) return config;

  const locFilter = parseFilterList(VISIBLE_LOCATIONS);
  const protoFilter = parseFilterList(PROTOCOL_GROUPS);

  // 第一遍：按地区和协议分组，收集筛选后的节点
  const locationMap = {};
  const protocolMap = {};
  const filteredNames = [];
  const filteredProxies = [];

  for (const proxy of proxies) {
    if (!proxy || !proxy.name) continue;

    const loc = extractLocation(proxy.name);
    const proto = proxy.type;

    if (loc) {
      (locationMap[loc] ??= []).push(proxy.name);
    }
    if (proto) {
      (protocolMap[proto] ??= []).push(proxy.name);
    }

    const locOk = !hasLocation || matchFilter(loc, locFilter.include, locFilter.exclude);
    const protoOk = !hasProtocol || matchFilter(proto, protoFilter.include, protoFilter.exclude);
    if (locOk && protoOk) {
      filteredNames.push(proxy.name);
      filteredProxies.push(proxy);
    }
  }

  // 生成动态分组
  const locResult = hasLocation
    ? makeDynamicGroups(locationMap, locFilter.include, locFilter.exclude)
    : { groups: [], groupNames: [] };
  const protoResult = hasProtocol
    ? makeDynamicGroups(protocolMap, protoFilter.include, protoFilter.exclude)
    : { groups: [], groupNames: [] };

  // 可选 select 组
  const extraGroups = [];
  if (hasLocation) {
    extraGroups.push({
      name: "指定地区",
      type: "select",
      proxies: [...locResult.groupNames, "COMPATIBLE"],
      icon: "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/urltest.png",
    });
  }
  if (hasProtocol) {
    extraGroups.push({
      name: "指定协议",
      type: "select",
      proxies: [...protoResult.groupNames, "COMPATIBLE"],
      icon: "https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/fallback.png",
    });
  }

  // 修改现有固定组：在 DIRECT 之前插入可选组
  const insertNames = [];
  if (hasProtocol) insertNames.push("指定协议");
  if (hasLocation) insertNames.push("指定地区");

  const fixedGroupNames = ["默认", "大模型", "其他"];
  const proxyGroups = config["proxy-groups"] || [];
  for (const group of proxyGroups) {
    if (!fixedGroupNames.includes(group.name)) continue;
    const proxies = group.proxies;
    if (!Array.isArray(proxies)) continue;
    const directIdx = proxies.indexOf("DIRECT");
    if (directIdx !== -1) {
      // 在 DIRECT 之前插入可选组（去重）
      const toInsert = insertNames.filter((n) => !proxies.includes(n));
      proxies.splice(directIdx, 0, ...toInsert);
    }
  }

  // 更新"指定节点"的节点列表（如果存在）
  for (const group of proxyGroups) {
    if (group.name === "指定节点") {
      group.proxies = [...filteredNames, "COMPATIBLE"];
      break;
    }
  }

  // 追加动态分组和可选 select 组
  config["proxy-groups"] = [
    ...proxyGroups,
    ...extraGroups,
    ...locResult.groups,
    ...protoResult.groups,
  ];

  // 筛选 proxies 列表
  config["proxies"] = filteredProxies;

  return config;
}
