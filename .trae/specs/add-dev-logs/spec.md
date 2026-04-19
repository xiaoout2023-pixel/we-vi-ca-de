# Add Development Log Display Feature

## Why
用户需要在启动服务后看到所有开发日志，以便分析问题出在哪一步。当前日志不够详细，且没有在控制台完整展示。

## What Changes
- 启动时输出mitmdump完整日志到控制台
- 实时显示捕获的所有请求日志
- 显示详细的错误信息堆栈
- 添加启动过程的分步日志

## Impact
- Affected specs: 微信视频捕获解密工具 - 日志系统
- Affected code: 
  - `src/main.py` - 添加详细日志输出
  - `src/capture/mitm_addon.py` - 增强日志输出

## ADDED Requirements
### Requirement: 启动日志完整输出
程序启动时应输出所有开发相关的日志信息。

#### Scenario: 启动过程日志
- **WHEN** 程序启动
- **THEN** 输出Python路径、mitmdump路径、addon路径
- **AND** 输出完整命令行
- **AND** 输出mitmdump的stdout和stderr
- **AND** 输出端口监听状态

### Requirement: 实时请求日志
所有经过代理的请求都应在控制台显示。

#### Scenario: 实时显示请求
- **WHEN** 有请求经过mitmdump
- **THEN** 在控制台实时显示请求信息
- **AND** 包含URL、方法、状态码、是否微信

### Requirement: 错误日志详细输出
所有错误都应完整输出到控制台。

#### Scenario: 错误详情输出
- **WHEN** 发生错误
- **THEN** 输出完整错误堆栈
- **AND** 输出错误发生位置
- **AND** 输出可能的解决建议
