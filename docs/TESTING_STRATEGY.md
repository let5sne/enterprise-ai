# TESTING_STRATEGY

## 测试目标
保证：
- 能力正确
- 编排正确
- follow-up 正确
- response contract 稳定

## 测试分层

### 1. 单元测试
针对：
- classifier
- resolver
- builder
- service 内部纯逻辑

### 2. 集成测试
针对：
- orchestration + registry + handler
- 多步 plan 执行
- follow-up continuation

### 3. 响应协议测试
针对：
- API response shape
- citations / artifacts / debug 聚合

## 命名规则
- `test_xxx_behavior`
- `test_xxx_routes_to_yyy`
- `test_xxx_returns_zzz`

## 每次改动最少要补什么测试
### 改 classifier
补分类器单测

### 改 follow-up routing
补 end-to-end 测试

### 改 response schema
补 response contract 测试

### 改 context 写回
补 task/session context 测试

## 回归要求
- 每个新能力至少要有 1 条 happy path
- 每个路由变化至少要有 1 条行为测试
- 关键 follow-up 变更必须补回归测试

## 推荐执行
```bash
python -m pytest -q