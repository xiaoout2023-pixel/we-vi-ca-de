# 调整decode_key捕获策略：从finder.weixin.qq.com获取

## Why
之前的捕获策略一直在 `finder.video.qq.com` 和 `channels.weixin.qq.com` 中查找decode_key，但根据参考文章和用户指导，正确的decode_key应该在 `finder.weixin.qq.com` 的API响应中返回。

## What Changes
- 修改 `mitm_addon.py` 中的API拦截逻辑，增加对 `finder.weixin.qq.com` 域名的拦截
- 从该域名的API响应中提取 `decodeKey` 字段
- 保持现有视频URL捕获逻辑不变
- 简化JS注入逻辑（因为PC客户端可能不加载网页JS）

## Impact
- 受影响的文件: `src/capture/mitm_addon.py`
- 影响能力: decode_key捕获成功率

## ADDED Requirements

### Requirement: 拦截finder.weixin.qq.com API响应
系统 SHALL 拦截 `finder.weixin.qq.com` 域名下的所有API响应，并提取decode_key

#### Scenario: 成功捕获decode_key
- **WHEN** mitmproxy拦截到 `finder.weixin.qq.com` 的API响应
- **AND** 响应中包含 `decodeKey` 或 `decode_key` 字段
- **THEN** 提取该字段并保存到 `captured_data.json`

#### Scenario: 输出API响应结构用于调试
- **WHEN** 首次拦截到 `finder.weixin.qq.com` 的API响应
- **THEN** 输出响应的JSON结构（前1000字符）用于分析

## MODIFIED Requirements

### Requirement: 视频捕获域名
**当前**: 只拦截 `finder.video.qq.com/stodownload`
**修改为**: 保持现有逻辑，但增加对 `finder.weixin.qq.com` 的API响应拦截

### Requirement: JS注入策略
**当前**: 尝试注入 `virtual_svg-icons-register.publish*.js` 文件
**修改为**: 保留JS注入逻辑但降低优先级，主要依靠API响应拦截获取decode_key

## REMOVED Requirements
无
