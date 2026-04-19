# 清理脚本与代理端口管理

## Why
用户经常遇到端口 8080 被占用、代理未清除的问题，需要自动化工具来清理环境和确保程序启动/结束时正确恢复。

## What Changes
- 新增 `clean.bat` 清理脚本
- 修改 `run.bat` 启动前自动检查和清理
- 修改 `src/main.py` 启动前检查并结束时恢复代理和端口

## Impact
- Affected specs: 微信视频捕获解密工具
- Affected code: `run.bat`, `clean.bat` (new), `src/main.py`, `src/utils/proxy_utils.py` (new)

## ADDED Requirements
### Requirement: 清理脚本
系统应提供 `clean.bat` 脚本，执行以下操作：
- 检测并关闭占用端口 8080 的进程
- 禁用系统代理（恢复到无代理状态）

### Requirement: 启动前自查
`run.bat` 启动前应：
- 检查端口 8080 是否被占用
- 如被占用，提示用户选择：自动清理或手动处理
- 检查系统代理是否已开启
- 如已开启且不是指向 127.0.0.1:8080，提示用户

### Requirement: 结束时清理
程序结束（正常或异常）时应：
- 关闭 mitmdump 进程
- 禁用系统代理（如程序开启的）
- 释放端口 8080

## MODIFIED Requirements
### Requirement: 代理管理
程序应跟踪是否是自己开启的代理，只在是自己开启的情况下才在退出时关闭。
