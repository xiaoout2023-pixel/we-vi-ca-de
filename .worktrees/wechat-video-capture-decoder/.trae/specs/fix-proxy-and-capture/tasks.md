# Tasks

- [ ] Task 1: 移除自动代理配置
  - [ ] 修改main.py，移除enable_proxy自动调用
  - [ ] 恢复手动配置代理提示
  - [ ] 更新退出清理逻辑，不再自动恢复代理

- [ ] Task 2: 增强mitm_addon.py日志记录
  - [ ] 记录所有经过代理的请求（不仅是微信）
  - [ ] 输出请求URL、User-Agent、Content-Type
  - [ ] 记录是否识别为微信请求
  - [ ] 记录是否识别为视频请求
  - [ ] 保存详细日志到capture_logs目录

- [ ] Task 3: 添加轮询状态显示窗口
  - [ ] 在main.py添加定期状态输出
  - [ ] 显示已捕获的视频URL数量
  - [ ] 显示已捕获的decode_key数量
  - [ ] 显示最近的捕获记录
  - [ ] 每5秒刷新一次状态

- [ ] Task 4: 验证和测试
  - [ ] 运行测试验证语法正确
  - [ ] 确认日志记录工作正常
  - [ ] 确认状态轮询显示正常

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 2 and Task 3
