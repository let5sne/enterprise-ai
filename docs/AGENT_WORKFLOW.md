# AGENT_WORKFLOW

## 接任务后的固定顺序
1. 先读 `PROJECT_BRIEF.md`
2. 再读 `ARCHITECTURE.md`
3. 再读 `ENGINEERING_RULES.md`
4. 查看 `TASK_BOARD.md` 当前优先任务
5. 再开始改代码

## 开发前检查
- 当前能力在哪个 domain？
- 当前逻辑属于 service / handler / builder / classifier 哪一层？
- 是否已有相似模式可复用？

## 开发中要求
- 先做最小闭环
- 先写规则，再考虑抽象升级
- 优先兼容现有测试

## 完成任务后必须做
1. 补充或更新测试
2. 运行 pytest
3. 写清楚变更说明
4. 说明是否引入新 schema / 新字段 / 新行为

## 不确定时怎么做
- 优先保守
- 不改变外部接口语义
- 不一次引入过多新概念