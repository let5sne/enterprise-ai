# ENGINEERING_RULES

## 总原则
优先保证：
1. 清晰
2. 稳定
3. 可测试
4. 可演进

## 文件组织规则
- orchestration 逻辑放 `app/orchestration/`
- domain service 放各自目录：`app/data/` `app/knowledge/` `app/content/`
- schema 统一放 `app/schemas/`
- 测试统一放 `tests/`

## 代码职责规则
### handler
只做适配，不做核心业务

### service
负责该领域核心业务逻辑

### builder / resolver / classifier
负责单一职责的规则逻辑，不混进 service 主流程

## 命名规则
- `*Service`：领域服务
- `*Handler`：能力执行适配
- `*Resolver`：判定是否进入某分支
- `*Classifier`：分类
- `*Builder`：构造中间产物或输入

## 修改规则
- 优先在既有结构上扩展，不随意推翻已有模块
- 先问：这个逻辑是否应该抽新模块？
- 如果逻辑重复或职责混杂，应优先抽出

## 错误处理规则
- 不静默吞错
- step 级错误要能反馈到 execution result
- API 层错误返回要稳定

## 禁止事项
- 不要把所有逻辑塞进 `service.py`
- 不要让 handler 直接承载复杂业务
- 不要引入未测试的重型依赖
- 不要随意改变既有 response 字段含义

## 提交规则
commit message 推荐格式：
- `feat(...)`
- `refactor(...)`
- `test(...)`
- `fix(...)`

PR 必须包含：
- 变更内容
- 为什么做
- 测试方式