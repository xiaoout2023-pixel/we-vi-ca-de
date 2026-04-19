# 修复JS注入和日志分文件问题

## Why
1. JS代码注入完全没有触发，播放视频后仍没有捕获到decode_key
2. 日志文件没有按启动时间戳分开，导致调试困难

## What Changes
- 诊断JS注入失败的根本原因（可能是响应为gzip压缩、JS文件路径不同、或函数签名不匹配）
- 实现按启动时间戳分离日志文件
- 增加更详细的调试日志来追踪JS注入过程

## Impact
- 受影响的文件: `src/capture/mitm_addon.py`, `src/utils/logger.py`, `src/main.py`
- 影响能力: JS注入捕获decode_key、日志管理

## ADDED Requirements

### Requirement: 按时间戳分离日志
系统 SHALL 在每次启动时创建独立的日志文件，使用时间戳命名

#### Scenario: 新启动创建新日志文件
- **WHEN** 程序启动
- **THEN** 创建 `capture_logs/debug_YYYYMMDD_HHMMSS.log` 文件
- **THEN** 该次运行的所有日志都写入这个文件

### Requirement: JS注入详细调试
系统 SHALL 输出JS注入的每个检查步骤

#### Scenario: 检查微信JS文件响应
- **WHEN** mitmproxy响应微信的JS文件
- **THEN** 输出URL、Content-Type、是否gzip压缩、文本是否可访问
- **THEN** 如果包含finder相关函数，输出匹配结果

#### Scenario: JS注入失败时输出原因
- **WHEN** 正则表达式无法匹配
- **THEN** 输出原始JS的前2000字符（解码后）

## MODIFIED Requirements

### Requirement: JS注入检测逻辑
**当前**: 只检查 `virtual_svg-icons-register.publish`
**修改为**: 检查所有包含 `virtual_svg` 或 `finder` 的JS文件，以及 `channels.weixin.qq.com` 域名返回的JS

### Requirement: Gzip解压处理
**新增**: 如果响应是gzip压缩，需要先解压再检查/修改
