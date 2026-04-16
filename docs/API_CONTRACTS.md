# API_CONTRACTS

## 文档目的

本文件定义 enterprise-ai 项目的对外 API 契约，重点描述：

* 请求结构
* 响应结构
* 字段语义
* 稳定性约定
* 示例 payload

本文件的目标不是替代 OpenAPI，而是给开发者、测试人员、agent 一个稳定、清晰的接口语义说明。

---

## 总体原则

### 1. 文本回答始终保留

无论响应多结构化，`answer` 始终存在且为主输出。

### 2. 结构化字段按需出现

不是每次调用都会返回：

* citations
* artifacts
* task_context
* debug

这些字段允许为空或为空列表。

### 3. 协议优先稳定

新增字段优先以向后兼容方式增加，避免删除或重定义已有字段语义。

### 4. API 返回的是“聚合后的最终结果”

step 级别结果属于内部执行结果，最终 API 主要暴露聚合后的结果。

---

## 当前主要接口

### `POST /api/v1/chat/ask`

统一对话入口，支持：

* knowledge.ask
* data.analyze
* content.generate
* 多步编排
* follow-up continuation

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
```

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
  "contract_version": "v1",
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
| contract_version  | string                     | 是  | 响应契约版本，当前固定为 `v1`      |
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
* contract_version

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

### 兼容性说明（v1）

* `ChatAskResponse` 自 v1 起不再包含历史字段 `structured_result`
* 结构化信息已拆分为 `citations` / `artifacts` / `task_context` / `debug`
* 新客户端应基于显式字段消费；旧客户端若依赖 `structured_result` 需升级适配

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
