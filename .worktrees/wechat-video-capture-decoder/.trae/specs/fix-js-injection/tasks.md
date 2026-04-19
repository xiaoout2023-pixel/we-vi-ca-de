# Tasks

- [ ] Task 1: 实现按时间戳分离日志文件
  - [ ] 修改logger.py，在创建logger时使用时间戳生成日志文件名
  - [ ] 日志文件名格式：debug_YYYYMMDD_HHMMSS.log
  - [ ] 确保mitm_addon和main.py使用新的日志文件

- [ ] Task 2: 诊断JS注入失败原因
  - [ ] 检查微信是否请求JS文件，输出所有JS请求
  - [ ] 检查响应是否gzip压缩，如果是则解压
  - [ ] 检查实际JS文件中是否包含finderGetCommentDetail函数
  - [ ] 确认当前正则表达式是否匹配实际函数签名

- [ ] Task 3: 增强JS注入调试日志
  - [ ] 输出所有微信JS文件的URL、Content-Type、是否压缩
  - [ ] 如果找到finder相关函数，输出匹配详情
  - [ ] 注入失败时输出原始JS内容（前2000字符）

- [ ] Task 4: 修复JS注入逻辑
  - [ ] 处理gzip压缩的响应
  - [ ] 使用更灵活的正则表达式匹配函数
  - [ ] 确保注入后Content-Length头被移除

- [ ] Task 5: 端到端测试
  - [ ] 清理旧数据
  - [ ] 启动程序
  - [ ] 播放视频
  - [ ] 验证日志按时间戳分文件
  - [ ] 验证看到JS注入日志
  - [ ] 验证捕获到decode_key
