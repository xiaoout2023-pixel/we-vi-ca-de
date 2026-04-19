# Tasks

- [ ] Task 1: 创建诊断脚本
  - [ ] 检查mitmdump进程是否运行
  - [ ] 检查端口8080是否被监听
  - [ ] 检查系统代理是否配置
  - [ ] 检查日志文件内容
  - [ ] 检查captured_data.json文件
  - [ ] 输出诊断报告

- [ ] Task 2: 验证addon加载
  - [ ] 运行测试脚本验证mitmdump能加载addon
  - [ ] 确认addon初始化成功
  - [ ] 确认日志输出正常

- [ ] Task 3: 提供用户指导
  - [ ] 明确说明需要配置代理才能捕获
  - [ ] 说明微信内置播放器可能不走系统代理
  - [ ] 提供替代方案（如需要）

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 1
