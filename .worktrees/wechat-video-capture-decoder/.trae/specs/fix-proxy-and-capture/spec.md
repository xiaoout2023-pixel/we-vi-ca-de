# Fix Proxy Configuration and Video Playback Issue

## Why
用户反馈设置代理后视频无法播放，且没有捕获日志生成。当前实现违反了原始需求：代理不应影响其他应用和视频播放。

## What Changes
- 移除自动设置系统代理的逻辑，改为提示用户手动配置
- 增强mitm_addon.py的请求日志输出，记录所有经过代理的请求
- 添加轮询窗口显示，实时展示捕获状态
- 明确文档说明：微信内置播放器可能不遵循系统代理，需要配合其他方法

## Impact
- Affected specs: 微信视频捕获解密工具 - 代理配置策略
- Affected code: 
  - `src/main.py` - 移除自动代理配置
  - `src/capture/mitm_addon.py` - 增加请求日志
  - 用户界面提示

## ADDED Requirements
### Requirement: 不干扰视频播放
程序启动mitmdump后，不应自动修改系统代理设置，由用户自行决定是否配置代理。

#### Scenario: 启动不修改代理
- **WHEN** 程序启动
- **THEN** mitmdump正常监听端口
- **AND** 不修改系统代理设置
- **AND** 提示用户如何配置（如果需要）

### Requirement: 捕获日志记录
所有经过mitmdump的请求都应被记录，用于诊断和问题排查。

#### Scenario: 记录请求日志
- **WHEN** 有请求经过mitmdump
- **THEN** 记录请求URL、User-Agent、是否微信、是否视频等信息
- **AND** 保存到capture_logs目录

### Requirement: 轮询状态显示
用户应能实时看到捕获状态和数据轮询窗口。

#### Scenario: 显示捕获状态
- **WHEN** 程序运行中
- **THEN** 定期显示已捕获的视频数量
- **AND** 显示最近的捕获记录
- **AND** 提供实时反馈

## MODIFIED Requirements
### Requirement: 代理配置策略
从自动配置改为手动配置提示，确保不影响视频播放和其他应用。
