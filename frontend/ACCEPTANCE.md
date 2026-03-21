# 验收标准检查清单

## 功能验收

- [ ] 页面布局：左右分栏，侧边栏固定 220px
- [ ] 侧边栏显示会话列表
- [ ] 点击"+新建"创建新会话
- [ ] 点击会话项切换会话
- [ ] 点击×删除会话
- [ ] 输入消息并按 Enter 发送
- [ ] Shift+Enter 换行
- [ ] 消息气泡正确显示（左 AI/右 用户）
- [ ] 蓝色主题配色正确
- [ ] 加载状态显示正确

## API 集成验收

- [ ] 后端服务启动在 http://localhost:8000
- [ ] 前端服务启动在 http://localhost:3000
- [ ] 发送消息成功调用 /api/v1/chat
- [ ] 收到 AI 响应并显示

## 兼容性验收

- [ ] Chrome 浏览器正常工作
- [ ] Edge 浏览器正常工作
- [ ] Firefox 浏览器正常工作
- [ ] 响应式布局在 1920x1080 正常
- [ ] 响应式布局在 1366x768 正常

## 测试验收

- [ ] 所有单元测试通过 (16/16)
- [ ] 构建成功无错误

## 如何启动

### 后端

```bash
cd D:\workplace\qrc\new3
python main.py
# 或
uvicorn main:app --host=0.0.0.0 --port=8000
```

### 前端

```bash
cd D:\workplace\qrc\new3\.claude\worktrees\vue3-frontend\frontend
npm run dev
```

前端将运行在 http://localhost:3000
