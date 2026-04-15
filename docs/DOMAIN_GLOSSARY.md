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
```

---

### human readable text
面向用户的可读文本。
通常是最终 `answer` 的主要来源。

---

### citation
引用。
知识能力返回的来源说明，用于支持可追溯回答。

通常包含：
- source_type
- title
- locator
- snippet

---

### artifact
工件。
除普通文本外，可被调用端进一步消费的结果对象。

#### 典型 artifact 类型
- `table`
- `text`
- `chart`
- `file`

---

### raw data
原始调试数据。
不直接面向终端用户，主要给：
- 调试
- 开发
- 管理端追踪

#### 例子
- `raw_sql`
- `matched_doc_ids`

---

### session
会话。
一个连续交互上下文的边界。

通过：
- `session_id`

识别。

---

### session context
会话上下文。
记录最近对话消息历史。

通常表现为：
- `SessionContext`

包含：
- recent messages

---

### task context
任务上下文。
记录当前 session 中最近一次任务执行的关键状态与输出。

通常表现为：
- `TaskContext`

包含：
- latest_intent
- latest_plan_id
- last_successful_step_no
- important_outputs

---

### important outputs
任务上下文中保存的关键输出字段。
用于后续 follow-up 继续处理。

典型包括：
- `latest_user_message`
- `latest_summary_text`
- `latest_structured_result`
- `latest_capability_code`
- `latest_output_type`
- `followup_ready`

---

### latest_output_type
上一轮输出所属的能力域类型。

允许值：
- `content`
- `data`
- `knowledge`

---

### followup_ready
布尔值。
表示上一轮结果是否适合被 follow-up 继续利用。

---

### response contract
响应协议。
指最终 API 对外暴露的统一响应结构，而不是内部 step 级结果。

典型字段：
- `answer`
- `citations`
- `artifacts`
- `task_context`
- `debug`

---

### task context snapshot
响应中对任务上下文的轻量化暴露形式。
用于前端 / 调用端了解：
- 这轮任务是什么
- 是否可以继续 follow-up

---

### debug info
调试信息。
在开发或管理场景中用于排查系统行为。

典型包括：
- intent
- plan_steps
- raw_sql

---

## 术语使用规则

### 1. 不要混用 “能力” 和 “模块”
- capability 是执行层标准代码
- module / package 是代码组织结构

### 2. 不要把 intent 和 capability 混为一谈
- intent 是语义归类
- capability 是执行单元

### 3. 不要把 session context 和 task context 混为一谈
- session context 偏消息历史
- task context 偏任务结果与状态

### 4. 不要把 structured result 和 artifact 混为一谈
- structured result 偏内部与程序消费
- artifact 偏调用端展示与下载

### 5. 不要把 follow-up type 和 intent 混为一谈
- follow-up type 是 follow-up 子分类
- intent 是最终计划语义标识

---

## 对 agent 的要求
agent 在开发与测试时，必须遵守：
1. 新概念优先复用本文术语
2. 若引入新术语，必须同步更新本文件
3. 不在不同模块中为同一概念使用多个名称
