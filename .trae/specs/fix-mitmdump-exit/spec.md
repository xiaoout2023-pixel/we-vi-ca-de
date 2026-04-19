# Fix mitmdump Immediate Exit Issue

## Why
mitmdump启动后立即退出（退出码0，无任何输出），导致整个视频捕获功能无法工作。虽然之前的spec增加了调试信息，但问题仍未解决。

## What Changes
- 彻底排查mitmdump立即退出的根本原因
- 修复mitm_addon.py的兼容性问题和导入问题
- 确保mitmdump能够正常启动并持续运行
- 添加完整的端到端测试验证

## Impact
- Affected specs: 微信视频捕获解密工具 - 核心功能被阻塞
- Affected code: 
  - `src/capture/mitm_addon.py` - addon文件
  - `src/main.py` - mitmdump启动逻辑
  - `run.bat` - 启动脚本

## ADDED Requirements
### Requirement: mitmdump正常启动和运行
mitmdump进程必须能够正常启动并持续运行，而不是立即退出。

#### Scenario: 成功启动
- **WHEN** 执行`python run.bat`或`python src/main.py`
- **THEN** mitmdump进程持续运行，不退出
- **AND** 端口8080被监听
- **AND** 无错误输出

#### Scenario: addon文件正常加载
- **WHEN** mitmdump加载mitm_addon.py
- **THEN** addon初始化成功
- **AND** 日志显示"VideoCaptureAddon initialized"
- **AND** addon准备好拦截HTTP请求

#### Scenario: 端到端测试通过
- **WHEN** 运行测试脚本验证所有功能
- **THEN** 代理启动成功
- **AND** 能够处理HTTP请求
- **AND** 能够捕获视频数据
- **AND** 进程正常退出时正确清理
