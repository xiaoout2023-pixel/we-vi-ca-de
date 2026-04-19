# Debug Video Capture Not Working

## Why
用户反馈播放了视频但没有捕获到任何内容，日志中也没有捕获动作。需要排查捕获流程为何不工作。

## What Changes
- 检查mitmdump是否正确加载addon
- 验证请求是否经过代理
- 确认日志是否显示所有请求
- 添加诊断工具帮助排查

## Impact
- Affected specs: 微信视频捕获解密工具 - 捕获功能
- Affected code: 
  - `src/capture/mitm_addon.py` - 捕获逻辑
  - `test_capture_debug.py` - 新增诊断工具

## ADDED Requirements
### Requirement: 诊断捕获失败原因
提供诊断工具帮助用户理解为什么没有捕获到视频。

#### Scenario: 诊断请求是否经过代理
- **WHEN** 运行诊断脚本
- **THEN** 检查mitmdump进程是否运行
- **AND** 检查端口8080是否被监听
- **AND** 检查代理是否配置
- **AND** 检查日志文件是否有请求记录
- **AND** 输出诊断报告
