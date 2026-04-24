# BUDGET_ASSISTANT_DEMO

## 目标

把预算 / 业财分析助手演示成一个可重复、可讲解、可复盘的闭环，而不是只展示代码。

适用对象：

- 内部评审
- 给领导做能力演示
- 给客户做方案展示
- 新同事快速理解项目边界

---

## 一分钟结论

当前 Demo 能稳定展示 3 类能力：

1. 单轮预算分析
2. 多轮数据 follow-up
3. 基于上轮分析结果生成正式经营说明

建议固定使用同一组演示话术，避免现场即兴发挥把演示引到尚未覆盖的问题上。

---

## 演示前准备

在项目根目录执行：

```bash
python scripts/smoke_budget_demo.py
```

看到 `预算助手 Demo 冒烟通过` 再开始正式演示。

这个脚本默认使用 `TestClient(main.app)`，不依赖额外启动服务，适合演示前快速自检。

如果需要通过 HTTP 服务演示，再额外启动：

```bash
uvicorn main:app --reload
```

---

## 推荐演示路径

### 场景 1：部门超预算

请求：

```json
{"user_id":"u1","source":"web","message":"本月哪些部门超预算？"}
```

讲解重点：

- 系统会识别为 `data.analyze`
- 返回可读 `answer`
- 返回 `table` artifact
- 返回 `chart` artifact
- `debug.raw_sql` 非空，说明查询链路可追溯
- `task_context` 中会留下 follow-up 所需的轻量状态

适合讲的结论：

- 不只是回答一句话，而是返回了可消费的结构化结果
- 后续可以被前端、IM、报告组件直接复用

### 场景 2：继续按预算科目展开

请求：

```json
{"session_id":"sess_budget_demo","user_id":"u1","source":"web","message":"按预算科目展开一下"}
```

讲解重点：

- 系统识别为 `data_followup`
- 仍然走 `data.analyze`
- 分析维度切换为 `subject_breakdown`
- 上下文延续依赖的是 session follow-up 状态，不需要用户重讲一遍上下文

适合讲的结论：

- 这不是静态报表问答，而是可以连续追问的数据助手

### 场景 3：生成领导汇报

请求：

```json
{"session_id":"sess_budget_demo","user_id":"u1","source":"web","message":"写成给领导看的经营分析说明"}
```

讲解重点：

- 系统切换到 `content.generate`
- 利用了上一轮 `latest_structured_result`
- 返回正式文本和 `text` artifact
- 输出包含 `领导您好`

适合讲的结论：

- 从“分析”到“表达”是一条链路
- 可以直接进入汇报、周报、经营分析说明等落地场景

---

## 演示时建议展示的字段

建议固定展示这几类结果：

- `answer`
- `artifacts`
- `debug.raw_sql`
- `task_context.important_outputs`

其中 `task_context.important_outputs` 只展示轻量字段：

- `latest_output_type`
- `latest_capability_code`
- `followup_ready`

不要把内部重型上下文当成对外契约来讲。

---

## 推荐讲法

可以按下面的顺序讲：

1. 先讲它是统一入口 `POST /api/v1/chat/ask`
2. 再讲它不是单纯聊天，而是编排数据分析和内容生成
3. 展示单轮分析结果
4. 展示 follow-up 维度展开
5. 展示自动生成经营说明
6. 最后强调它已经是“可演示闭环”，不是单点能力堆砌

一句话版本：

“这个 Demo 已经能把预算问题从分析、展开到汇报串成一条闭环，适合继续往客户演示和产品化包装推进。”

---

## 演示边界

当前明确不要讲成下面这些能力：

- 真实金蝶对接
- 多租户
- 权限体系
- 前端产品化完成
- 通用 BI 平台
- 任意预算问题都能覆盖

正确讲法应该是：

- 这是稳定、可测试、可复盘的预算助手最小闭环
- 下一步适合补演示脚本、演示文档、对外包装，而不是继续堆复杂功能

---

## 复盘清单

每次演示结束后，建议复盘以下问题：

- 领导 / 客户最关心的是分析结果，还是汇报文本
- 他们是否更关心真实数据接入，而不是更多问法
- 他们是否理解 artifacts 的价值
- 他们是否接受“先做最小闭环，再接真实系统”的路线

如果现场反馈集中在“怎么演示给别人看”，说明这个 Demo 已经到了该做包装而不是继续堆逻辑的阶段。
