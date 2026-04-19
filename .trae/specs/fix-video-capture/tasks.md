# Tasks

- [ ] Task 1: 修改main.py实现自动代理配置
  - [ ] mitmdump启动成功后，调用enable_proxy()设置系统代理
  - [ ] 保存原始代理设置用于恢复
  - [ ] 输出代理配置成功提示
  - [ ] 更新提示信息说明已自动配置

- [ ] Task 2: 确保mitmdump持续运行
  - [ ] 验证mitmdump不退出
  - [ ] 添加进程状态检查
  - [ ] 如果退出则输出错误日志

- [ ] Task 3: 完善退出清理逻辑
  - [ ] Ctrl+C时先恢复原代理
  - [ ] 然后关闭mitmdump
  - [ ] 输出清理完成提示

- [ ] Task 4: 端到端验证
  - [ ] 运行完整流程测试
  - [ ] 验证代理配置成功
  - [ ] 验证mitmdump运行
  - [ ] 验证捕获功能
  - [ ] 验证退出恢复

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 1, 2, 3
