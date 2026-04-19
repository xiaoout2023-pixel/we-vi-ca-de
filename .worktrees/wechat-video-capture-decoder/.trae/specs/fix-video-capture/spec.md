# Fix Video Capture to Work Properly

## Why
根据用户确认，微信内置播放器是可以被监听的进程。但当前实现没有正确捕获视频，需要按照参考文档的要求，实现完整的系统代理+mitmdump拦截方案。

## What Changes
- 启动mitmdump后自动启用系统代理
- 确保mitmdump持续运行
- 验证捕获流程完整
- 退出时自动恢复原代理设置

## Impact
- Affected specs: 微信视频捕获解密工具 - 捕获功能
- Affected code: 
  - `src/main.py` - 启动流程和代理管理
  - `src/utils/proxy_utils.py` - 代理控制

## ADDED Requirements
### Requirement: 自动启用系统代理
启动mitmdump后自动设置系统代理，使微信流量经过代理。

#### Scenario: 启动后自动配置
- **WHEN** mitmdump启动成功
- **THEN** 自动启用系统代理指向127.0.0.1:8080
- **AND** 记录原始代理设置
- **AND** 输出配置成功提示

### Requirement: 持续运行并捕获
mitmdump必须持续运行，捕获所有经过代理的微信视频请求。

#### Scenario: 成功捕获视频
- **WHEN** 用户在微信中播放视频
- **THEN** mitmdump拦截视频URL
- **AND** 日志显示捕获记录
- **AND** captured_data.json有数据
- **AND** 视频正常播放（代理不影响）

### Requirement: 退出时恢复代理
程序退出时自动恢复原来的代理设置。

#### Scenario: 正常退出
- **WHEN** 用户按Ctrl+C退出
- **THEN** 关闭mitmdump
- **AND** 恢复原始系统代理设置
- **AND** 输出恢复提示

## MODIFIED Requirements
### Requirement: 代理配置策略
改为自动配置系统代理（启动时设置，退出时恢复），确保微信流量经过代理。
