# ARCHITECTURE

## 总体分层
```text
API Layer
  -> Orchestration Layer
    -> Capability Registry / Handlers
      -> Domain Services
        -> Data / Knowledge / Content

## 关键模块

app/api

提供统一入口，例如 chat.py

app/orchestration

负责：

message preprocessing
intent classification
complexity evaluation
task decomposition
capability mapping
follow-up resolution
follow-up type classification
followup question building
plan execution orchestration
app/data

负责数据语义解析、SQL 构造、安全检查、执行与总结

app/knowledge

负责知识检索、回答生成、citation 组织

app/content

负责说明、摘要、改写、润色等文本输出

app/schemas

负责统一协议与对象模型

执行主链
API 接收用户请求
根据 session_id 读取 context
OrchestrationService.plan() 生成执行计划
execute() 调 registry / handler 执行
结果写回 TaskContext
API 返回统一响应
Follow-up 机制
当前包含
FollowupResolver
FollowupTypeClassifier
FollowupQuestionBuilder
Follow-up 类型
content_refine
content_from_previous_data
content_from_previous_knowledge
data_continue
knowledge_continue
unknown_followup
Context 机制
SessionContext

记录最近消息

TaskContext

记录：

latest_intent
latest_plan_id
last_successful_step_no
important_outputs
当前响应机制

计划升级到 unified response contract，支持：

answer
citations
artifacts
task_context
debug