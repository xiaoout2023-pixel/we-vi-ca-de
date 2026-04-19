# 强制捕获finder.weixin.qq.com并提取decode_key

## Why
程序必须捕获 `finder.weixin.qq.com` 的API响应并提取decode_key，但目前没有捕获到任何该域名的请求。需要确保mitmproxy能拦截到所有微信请求，包括该域名。

## What Changes
- 修改mitm_addon.py，输出所有微信请求的域名，找出实际请求的域名
- 确保代理配置正确，所有微信流量都经过mitmproxy
- 如果 `finder.weixin.qq.com` 没有被请求，找出实际承载decode_key的域名

## Impact
- 受影响的文件: `src/capture/mitm_addon.py`
- 影响能力: decode_key捕获

## ADDED Requirements

### Requirement: 输出所有微信请求域名
系统 SHALL 输出每个微信请求的完整URL和域名，帮助找出实际的API域名

#### Scenario: 记录所有域名
- **WHEN** mitmproxy拦截到任何微信请求
- **THEN** 输出请求的域名
- **THEN** 统计每个域名出现的次数

### Requirement: 必须捕获到承载decode_key的域名
系统 SHALL 确保捕获到包含decode_key的API响应

#### Scenario: 找到decode_key
- **WHEN** 任何微信API响应中包含 `decodeKey` 或 `decode_key` 字段
- **THEN** 立即输出并保存

## MODIFIED Requirements

### Requirement: 域名拦截策略
**当前**: 只检测特定域名
**修改为**: 记录所有微信请求的域名，找出实际承载decode_key的域名
