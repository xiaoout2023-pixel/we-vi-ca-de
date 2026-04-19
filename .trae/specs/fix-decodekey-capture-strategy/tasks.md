# Tasks

- [ ] Task 1: 修改mitm_addon.py增加finder.weixin.qq.com拦截
  - [ ] 在response方法中增加对finder.weixin.qq.com域名的检测
  - [ ] 输出该域名的所有API响应结构（用于调试）
  - [ ] 从响应中提取decodeKey字段
  - [ ] 保存到captured_data.json

- [ ] Task 2: 简化JS注入逻辑
  - [ ] 保留JS注入代码但降低优先级
  - [ ] 主要依赖API响应拦截获取decode_key

- [ ] Task 3: 测试端到端流程
  - [ ] 启动程序
  - [ ] 在微信中播放视频
  - [ ] 验证是否拦截到finder.weixin.qq.com的请求
  - [ ] 验证是否捕获到decode_key
  - [ ] 检查captured_data.json内容
