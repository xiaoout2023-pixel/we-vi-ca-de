# Tasks

- [x] Task 1: 创建 `clean.bat` 清理脚本
  - [x] SubTask 1.1: 检测并关闭占用端口 8080 的进程
  - [x] SubTask 1.2: 禁用系统代理
  - [x] SubTask 1.3: 输出清理结果

- [x] Task 2: 创建 `src/utils/proxy_utils.py` 代理工具模块
  - [x] SubTask 2.1: 实现检查代理状态函数
  - [x] SubTask 2.2: 实现启用/禁用代理函数
  - [x] SubTask 2.3: 实现检查端口占用函数
  - [x] SubTask 2.4: 实现清理端口函数

- [x] Task 3: 修改 `run.bat` 启动前自查
  - [x] SubTask 3.1: 检查端口 8080 是否被占用
  - [x] SubTask 3.2: 如被占用，提示并调用 clean.bat

- [x] Task 4: 修改 `src/main.py` 完善清理逻辑
  - [x] SubTask 4.1: 启动前检查端口 8080，如被占用则提示
  - [x] SubTask 4.2: 启动前检查代理状态，记录是否是自己开启的
  - [x] SubTask 4.3: 正常退出时关闭 mitmdump 并恢复代理
  - [x] SubTask 4.4: 异常退出时同样清理

# Task Dependencies
- Task 2 无依赖，可并行
- Task 1 无依赖，可并行
- Task 3 依赖 Task 1
- Task 4 依赖 Task 2
