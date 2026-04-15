# ARCHITECTURE

## 总体分层

```text
API Layer
  -> Orchestration Layer
    -> Capability Registry / Handlers
      -> Domain Services
        -> Data / Knowledge / Content
```

---

## 模块说明

### 1. API Layer（`app/api/`）

负责：

* 对外提供统一接口（如 `/chat/ask`）
* 参数校验
* 调用 orchestration
* 组装最终响应（response contract）

---

### 2. Orchestration Layer（`app/orchestration/`）

系统核心控制层，负责：

* message 预处理
* intent 识别
* complexity 判断
* 任务拆解
* capability 映射
* follow-up 判断与处理
* plan 构建
* plan 执行调度

核心组件：

* `OrchestrationService`
* `FollowupResolver`
* `FollowupTypeClassifier`
* `FollowupQuestionBuilder`

---

### 3. Capability Layer

#### Capability Registry

负责：

* 注册所有 capability
* 根据 capability_code 找到对应 handler

#### Capability Handler

负责：

* 将 PlanStep 输入适配为 domain service 调用
* 返回统一 `CapabilityExecutionResult`

典型 handler：

* KnowledgeAskHandler
* DataAnalyzeHandler
* ContentGenerateHandler

---

### 4. Domain Services（领域服务）

#### `app/knowledge/`

* 文档检索
* 知识问答
* citation 构造

#### `app/data/`

* 语义解析
* SQL 构造
* 数据执行
* 结果分析

#### `app/content/`

* 文本生成
* 改写
* 摘要

---

### 5. Schema Layer（`app/schemas/`）

定义系统统一数据结构：

* 请求模型
* 响应模型
* execution result
* context

---

## 执行流程（主链路）

```text
User Request
  -> API Layer
    -> Orchestration.plan()
      -> ExecutionPlan
    -> Orchestration.execute()
      -> Capability Handlers
      -> Domain Services
      -> CapabilityExecutionResult
    -> PlanExecutionResult
  -> Response Assembly
  -> ChatAskResponse
```

---

## Follow-up 机制

### 核心流程

1. 判断是否为 follow-up
2. 分类 follow-up 类型
3. 构造补全问题
4. 生成新的 plan

### 类型示例

* content_refine
* data_continue
* knowledge_continue

---

## Context 机制

### SessionContext

* 保存对话历史
* 最近消息列表

### TaskContext

* 保存最近任务执行结果
* 用于 follow-up

重要字段：

* latest_user_message
* latest_summary_text
* latest_structured_result
* latest_output_type
* followup_ready

---

## Response Contract（目标状态）

统一输出结构：

* answer
* citations
* artifacts
* task_context
* debug

---

## 设计原则

1. 单一职责（Handler / Service / Builder 分离）
2. 编排与执行分离
3. 显式输入绑定（避免隐式依赖）
4. context 驱动 follow-up
5. 输出结构统一（response contract）

---

## 演进方向

当前：规则驱动编排

未来可能：

* 规则 + 模型混合编排
* 更复杂 workflow
* 更丰富 artifact（chart / file）
* 多端消费能力增强
