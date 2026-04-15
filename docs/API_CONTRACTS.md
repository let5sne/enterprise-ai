下面补齐两份你刚才提到、很适合交给 agent 使用的文档，仍然保持 **Markdown 格式**：

1. `API_CONTRACTS.md`
2. `DOMAIN_GLOSSARY.md`

你可以直接放进仓库的 `docs/` 目录。

---

## `API_CONTRACTS.md`

````markdown
# API_CONTRACTS

## 文档目的
本文件定义 enterprise-ai 项目的对外 API 契约，重点描述：
- 请求结构
- 响应结构
- 字段语义
- 稳定性约定
- 示例 payload

本文件的目标不是替代 OpenAPI，而是给开发者、测试人员、agent 一个稳定、清晰的接口语义说明。

---

## 总体原则

### 1. 文本回答始终保留
无论响应多结构化，`answer` 始终存在且为主输出。

### 2. 结构化字段按需出现
不是每次调用都会返回：
- citations
- artifacts
- task_context
- debug

这些字段允许为空或为空列表。

### 3. 协议优先稳定
新增字段优先以向后兼容方式增加，避免删除或重定义已有字段语义。

### 4. API 返回的是“聚合后的最终结果”
step 级别结果属于内部执行结果，最终 API 主要暴露聚合后的结果。

---

## 当前主要接口

### `POST /api/v1/chat/ask`

统一对话入口，支持：
- knowledge.ask
- data.analyze
- content.generate
- 多步编排
- follow-up continuation

---

## 请求模型

### `ChatAskRequest`

```json
{
  "session_id": "sess_xxx_optional",
  "user_id": "u1",
  "source": "web",
  "message": "帮我看上个月哪个部门成本最高，并写一段说明"
}
````

### 字段说明

| 字段         | 类型            | 必填 | 说明                                                     |
| ---------- | ------------- | -- | ------------------------------------------------------ |
| session_id | string | null | 否  | 会话 ID。若未提供，服务端可自动生成                                    |
| user_id    | string        | 是  | 用户标识                                                   |
| source     | string        | 是  | 调用来源，如 `web` / `openclaw` / `feishu` / `wecom` / `api` |
| message    | string        | 是  | 用户输入文本                                                 |

### source 允许值

* `web`
* `openclaw`
* `feishu`
* `wecom`
* `api`

---

## 响应模型

### `ChatAskResponse`

```json
{
  "session_id": "sess_abc123",
  "answer": "查询结果显示，最高项为市场部，对应数值为 520000。",
  "capabilities_used": ["data.analyze"],
  "citations": [],
  "artifacts": [],
  "task_context": {
    "task_type": "data_only",
    "status": "completed",
    "summary": "查询结果显示，最高项为市场部，对应数值为 520000。",
    "important_outputs": {
      "latest_output_type": "data",
      "followup_ready": true
    }
  },
  "trace_id": "trace_xyz987",
  "debug": {
    "intent": "data_only",
    "plan_steps": ["data.analyze"],
    "raw_sql": "SELECT department_name AS dimension_name ..."
  }
}
```

---

## 顶层字段说明

| 字段                | 类型                         | 必填 | 说明                        |
| ----------------- | -------------------------- | -- | ------------------------- |
| session_id        | string                     | 是  | 当前会话 ID                   |
| answer            | string                     | 是  | 最终面向用户的回答文本               |
| capabilities_used | list[string]               | 是  | 本次执行中使用到的 capability code |
| citations         | list[CitationItem]         | 是  | 聚合后的引用信息                  |
| artifacts         | list[ArtifactItem]         | 是  | 聚合后的工件信息                  |
| task_context      | TaskContextSnapshot | null | 否  | 当前任务快照                    |
| trace_id          | string                     | 是  | 当前请求追踪 ID                 |
| debug             | ResponseDebugInfo | null   | 否  | 调试信息                      |

---

## 子模型定义

### `CitationItem`

```json
{
  "source_type": "memory_doc",
  "title": "采购审批制度",
  "locator": "section: 审批要求",
  "snippet": "采购审批应按金额分级审批……"
}
```

| 字段          | 类型            | 说明                  |
| ----------- | ------------- | ------------------- |
| source_type | string        | 来源类型，如 `memory_doc` |
| title       | string | null | 来源标题                |
| locator     | string | null | 来源定位信息              |
| snippet     | string | null | 命中片段                |

---

### `ArtifactItem`

```json
{
  "artifact_type": "table",
  "name": "analysis_result",
  "content": [
    {
      "dimension_name": "市场部",
      "metric_value": 520000
    }
  ]
}
```

| 字段            | 类型                            | 说明                                         |
| ------------- | ----------------------------- | ------------------------------------------ |
| artifact_type | string                        | 工件类型，如 `table` / `text` / `chart` / `file` |
| name          | string                        | 工件名称                                       |
| content       | object | list | string | null | 工件内容                                       |

---

### `TaskContextSnapshot`

```json
{
  "task_type": "knowledge_followup",
  "status": "completed",
  "summary": "根据制度说明，审批节点包括……",
  "important_outputs": {
    "latest_output_type": "knowledge",
    "followup_ready": true
  }
}
```

| 字段                | 类型            | 说明                           |
| ----------------- | ------------- | ---------------------------- |
| task_type         | string | null | 当前任务类型，一般等于 execution intent |
| status            | string        | 当前状态，v1 固定为 `completed`      |
| summary           | string | null | 本轮任务摘要                       |
| important_outputs | dict          | 可被后续 follow-up 使用的关键信息快照     |

---

### `ResponseDebugInfo`

```json
{
  "intent": "data_followup",
  "plan_steps": ["data.analyze"],
  "raw_sql": "SELECT ..."
}
```

| 字段         | 类型            | 说明              |
| ---------- | ------------- | --------------- |
| intent     | string | null | 本轮编排识别出的 intent |
| plan_steps | list[string]  | 实际执行的步骤能力代码     |
| raw_sql    | string | null | 若存在数据分析 SQL，则填入 |

---

## 响应稳定性约定

### 稳定字段

以下字段在未来版本中应尽量保持不变：

* session_id
* answer
* capabilities_used
* trace_id

### 可扩展字段

以下字段未来允许扩展内部结构：

* citations
* artifacts
* task_context
* debug

### 向后兼容规则

* 新字段只能追加，不应删除已有字段
* 可选字段应允许旧客户端忽略
* 不应改变已有字段的核心语义

---

## 按能力域的输出约定

### knowledge.ask

推荐输出：

* answer
* citations
* structured_result.answer

### data.analyze

推荐输出：

* answer
* artifacts（table）
* debug.raw_sql
* structured_result（top_item/value/difference 等）

### content.generate

推荐输出：

* answer
* structured_result.content
* 可选 artifacts（text）

---

## 错误语义

### 当前原则

* API 层异常使用标准 HTTP 错误返回
* step 级错误应尽量被包装进 execution result
* 若无法形成有效响应，可返回 4xx / 5xx

### 未来建议

后续可增加统一错误结构，例如：

```json
{
  "error": {
    "code": "invalid_request",
    "message": "message cannot be empty"
  }
}
```

当前版本不是必须。

---

## 示例场景

### 示例 1：知识问答

#### Request

```json
{
  "user_id": "u1",
  "source": "web",
  "message": "采购审批要求是什么"
}
```

#### Response

```json
{
  "session_id": "sess_001",
  "answer": "采购审批应按金额分级审批。",
  "capabilities_used": ["knowledge.ask"],
  "citations": [
    {
      "source_type": "memory_doc",
      "title": "采购审批制度",
      "locator": "section: 审批要求",
      "snippet": "采购审批应按金额分级审批……"
    }
  ],
  "artifacts": [],
  "task_context": {
    "task_type": "knowledge_only",
    "status": "completed",
    "summary": "采购审批应按金额分级审批。",
    "important_outputs": {
      "latest_output_type": "knowledge",
      "followup_ready": true
    }
  },
  "trace_id": "trace_001",
  "debug": {
    "intent": "knowledge_only",
    "plan_steps": ["knowledge.ask"],
    "raw_sql": null
  }
}
```

---

### 示例 2：数据分析

#### Request

```json
{
  "user_id": "u1",
  "source": "web",
  "message": "上个月哪个部门成本最高"
}
```

#### Response

```json
{
  "session_id": "sess_002",
  "answer": "查询结果显示，最高项为市场部，对应数值为 520000。",
  "capabilities_used": ["data.analyze"],
  "citations": [],
  "artifacts": [
    {
      "artifact_type": "table",
      "name": "analysis_result",
      "content": [
        {
          "dimension_name": "市场部",
          "metric_value": 520000
        }
      ]
    }
  ],
  "task_context": {
    "task_type": "data_only",
    "status": "completed",
    "summary": "查询结果显示，最高项为市场部，对应数值为 520000。",
    "important_outputs": {
      "latest_output_type": "data",
      "followup_ready": true
    }
  },
  "trace_id": "trace_002",
  "debug": {
    "intent": "data_only",
    "plan_steps": ["data.analyze"],
    "raw_sql": "SELECT department_name AS dimension_name ..."
  }
}
```

---

### 示例 3：follow-up

#### Request

```json
{
  "session_id": "sess_002",
  "user_id": "u1",
  "source": "web",
  "message": "换成同比"
}
```

#### Response

```json
{
  "session_id": "sess_002",
  "answer": "同比分析结果显示……",
  "capabilities_used": ["data.analyze"],
  "citations": [],
  "artifacts": [],
  "task_context": {
    "task_type": "data_followup",
    "status": "completed",
    "summary": "同比分析结果显示……",
    "important_outputs": {
      "latest_output_type": "data",
      "followup_ready": true
    }
  },
  "trace_id": "trace_003",
  "debug": {
    "intent": "data_followup",
    "plan_steps": ["data.analyze"],
    "raw_sql": "SELECT ..."
  }
}
```

---

## 对 agent 的要求

agent 在修改 API 时必须遵守：

1. 不随意删除已有响应字段
2. 新字段必须向后兼容
3. 每次修改协议必须同步更新：

   * 本文件
   * schema 定义
   * response contract 测试

````

---

## `DOMAIN_GLOSSARY.md`

```markdown
# DOMAIN_GLOSSARY

## 文档目的
统一项目中的核心术语，避免：
- 人与人之间理解不一致
- agent 在不同文件中使用不同叫法
- 功能扩展时语义漂移

---

## 核心术语

### enterprise-ai
项目名称，指当前这个“企业 AI 编排内核 / 能力后端”仓库。

---

### capability
能力。  
系统中一个可被编排与执行的功能单元。

当前典型 capability：
- `knowledge.ask`
- `data.analyze`
- `content.generate`

#### 注意
capability 不是模块目录名，也不是 PR 名称，而是执行层的标准能力代码。

---

### capability handler
能力执行适配器。  
负责把 `PlanStep` 的输入转交给对应 domain service，并把结果包装成统一的 `CapabilityExecutionResult`。

#### 例子
- `KnowledgeAskHandler`
- `DataAnalyzeHandler`
- `ContentGenerateHandler`

---

### domain service
领域服务。  
某一能力域的核心业务逻辑承载者。

#### 例子
- `KnowledgeService`
- `DataService`
- `ContentService`

#### 原则
- handler 负责适配
- service 负责核心业务

---

### orchestration
编排。  
系统从用户输入到执行计划生成，再到能力路由与执行的全过程。

包括：
- 预处理
- intent 识别
- complexity 判断
- 任务拆解
- capability 映射
- follow-up 处理
- 执行计划生成

---

### intent
意图。  
系统对用户输入进行语义归类后的结果，用于决定后续怎么规划。

#### 常见 intent
- `knowledge_only`
- `data_only`
- `content_only`
- `data_plus_content`
- `knowledge_plus_content`
- `content_followup`
- `data_followup`
- `knowledge_followup`

---

### follow-up
追问 / 延续指令。  
同一 session 中，基于上一轮结果继续进行的请求。

#### 例子
- 再正式一点
- 换成同比
- 补充审批节点

---

### follow-up resolver
用于判断：
- 当前输入是否属于 follow-up
- 当前上下文是否具备续接条件

对应模块：
- `FollowupResolver`

---

### follow-up type classifier
用于对 follow-up 进一步分类。

#### 常见分类
- `content_refine`
- `content_from_previous_data`
- `content_from_previous_knowledge`
- `data_continue`
- `knowledge_continue`
- `unknown_followup`

对应模块：
- `FollowupTypeClassifier`

---

### follow-up question builder
用于把不完整的 follow-up 短语补全为可执行的问题输入。

#### 例子
输入：
- “换成同比”

补全后：
- “把‘帮我看上个月哪个部门成本最高’改成同比分析方式重新处理。”

对应模块：
- `FollowupQuestionBuilder`

---

### plan
执行计划。  
编排层生成的一组待执行步骤。

通常表现为：
- `ExecutionPlan`

它包含：
- `plan_id`
- `intent`
- `steps`

---

### plan step
计划步骤。  
执行计划中的单个步骤，通常绑定一个 capability。

通常表现为：
- `PlanStep`

包含：
- `step_no`
- `capability_code`
- `input_data`
- `input_bindings`

---

### input binding
显式输入绑定。  
用于描述某个步骤如何引用前一步的结果，而不是依赖隐式上下文。

典型场景：
- `data_plus_content`
- `knowledge_plus_content`

含义：
- 第二步的某个输入来自第一步的 `structured_result`

---

### execution
执行。  
指 `ExecutionPlan` 被真正跑起来的过程。

通常由：
- `OrchestrationService.execute()`

负责调度 handler 完成。

---

### capability execution result
单个 capability 执行后的标准结果对象。

通常表现为：
- `CapabilityExecutionResult`

可能包含：
- `human_readable_text`
- `structured_result`
- `citations`
- `artifacts`
- `raw_data`
- `error`

---

### plan execution result
整个计划执行后的总结果对象。

通常表现为：
- `PlanExecutionResult`

它会聚合：
- step results
- summary text
- merged structured result
- citations
- artifacts
- debug info

---

### structured result
结构化结果。  
step 执行后，为后续编排、前端消费、task context 保存的机器可读结果。

#### 例子
```json
{
  "top_item": "市场部",
  "value": 520000
}
````

---

### human readable text

面向用户的可读文本。
通常是最终 `answer` 的主要来源。

---

### citation

引用。
知识能力返回的来源说明，用于支持可追溯回答。

通常包含：

* source_type
* title
* locator
* snippet

---

### artifact

工件。
除普通文本外，可被调用端进一步消费的结果对象。

#### 典型 artifact 类型

* `table`
* `text`
* `chart`
* `file`

---

### raw data

原始调试数据。
不直接面向终端用户，主要给：

* 调试
* 开发
* 管理端追踪

#### 例子

* `raw_sql`
* `matched_doc_ids`

---

### session

会话。
一个连续交互上下文的边界。

通过：

* `session_id`

识别。

---

### session context

会话上下文。
记录最近对话消息历史。

通常表现为：

* `SessionContext`

包含：

* recent messages

---

### task context

任务上下文。
记录当前 session 中最近一次任务执行的关键状态与输出。

通常表现为：

* `TaskContext`

包含：

* latest_intent
* latest_plan_id
* last_successful_step_no
* important_outputs

---

### important outputs

任务上下文中保存的关键输出字段。
用于后续 follow-up 继续处理。

典型包括：

* `latest_user_message`
* `latest_summary_text`
* `latest_structured_result`
* `latest_capability_code`
* `latest_output_type`
* `followup_ready`

---

### latest_output_type

上一轮输出所属的能力域类型。

允许值：

* `content`
* `data`
* `knowledge`

---

### followup_ready

布尔值。
表示上一轮结果是否适合被 follow-up 继续利用。

---

### response contract

响应协议。
指最终 API 对外暴露的统一响应结构，而不是内部 step 级结果。

典型字段：

* `answer`
* `citations`
* `artifacts`
* `task_context`
* `debug`

---

### task context snapshot

响应中对任务上下文的轻量化暴露形式。
用于前端 / 调用端了解：

* 这轮任务是什么
* 是否可以继续 follow-up

---

### debug info

调试信息。
在开发或管理场景中用于排查系统行为。

典型包括：

* intent
* plan_steps
* raw_sql

---

## 术语使用规则

### 1. 不要混用 “能力” 和 “模块”

* capability 是执行层标准代码
* module / package 是代码组织结构

### 2. 不要把 intent 和 capability 混为一谈

* intent 是语义归类
* capability 是执行单元

### 3. 不要把 session context 和 task context 混为一谈

* session context 偏消息历史
* task context 偏任务结果与状态

### 4. 不要把 structured result 和 artifact 混为一谈

* structured result 偏内部与程序消费
* artifact 偏调用端展示与下载

### 5. 不要把 follow-up type 和 intent 混为一谈

* follow-up type 是 follow-up 子分类
* intent 是最终计划语义标识

---

## 对 agent 的要求

agent 在开发与测试时，必须遵守：

1. 新概念优先复用本文术语
2. 若引入新术语，必须同步更新本文件
3. 不在不同模块中为同一概念使用多个名称

```

---

如果你愿意，我下一条可以继续把：

# `DECISIONS.md`

也补出来，专门记录这个项目目前已经形成的关键架构决策。
```
