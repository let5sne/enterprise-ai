# PROJECT_BRIEF

## 项目名称
enterprise-ai

## 一句话目标
构建一个可持续演进的企业 AI 能力后端，支持知识问答、数据分析、内容生成，以及基于上下文的多轮 follow-up 协作。

## 当前定位
这是一个“企业 AI 编排内核”项目，不是单纯聊天机器人，也不是完整前端产品。

## 当前已具备能力
- knowledge.ask
- data.analyze
- content.generate
- data_plus_content
- knowledge_plus_content
- follow-up phase one / phase two
- session / task context
- followup_question_builder

## 当前核心目标
在现有能力基础上，持续增强：
1. 编排正确性
2. follow-up 连续协作能力
3. 响应协议统一性
4. 多端可消费能力

## 当前不做的内容
- 不做复杂 UI
- 不做生产级权限系统
- 不做大规模数据库持久化
- 不做复杂多租户
- 不做重型 agent 框架接入

## 技术栈
- Python
- FastAPI
- Pydantic
- pytest

## 仓库关注重点
- `app/orchestration/`
- `app/data/`
- `app/knowledge/`
- `app/content/`
- `app/api/`
- `app/schemas/`
- `tests/`

## 当前开发原则
优先保证：
- 结构清晰
- 规则稳定
- 可测试
- 可演进