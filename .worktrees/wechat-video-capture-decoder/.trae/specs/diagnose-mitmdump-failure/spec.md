# 诊断 mitmdump 启动失败问题

## Why
用户运行 `run.bat` 时 mitmdump 启动失败，没有明确的错误信息输出，需要诊断根本原因。

## What Changes
- 增加详细的调试信息输出（Python 路径、addon 路径、命令、退出码）
- 延长等待时间从 2 秒到 5 秒
- 输出更友好的错误提示

## Impact
- Affected specs: 微信视频捕获解密工具
- Affected code: `src/main.py`

## ADDED Requirements
### Requirement: 启动调试
程序启动 mitmdump 时应输出：
- Python 解释器路径
- addon 文件路径
- 项目根目录
- 完整命令行
- 退出码（如果启动失败）
- stdout 和 stderr 的完整输出

#### Scenario: 启动失败有错误信息
- **WHEN** mitmdump 进程退出且退出码非 0
- **THEN** 输出退出码、stdout 和 stderr

#### Scenario: 启动失败无错误信息
- **WHEN** mitmdump 进程退出但没有输出任何错误
- **THEN** 提示可能原因（端口占用、安装问题、证书问题）
