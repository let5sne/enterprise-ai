# TASK_BOARD

## 状态定义
- TODO
- DOING
- DONE
- BLOCKED

---

## 当前阶段：统一响应协议

### TASK-001
**标题**：定义统一响应 schema  
**状态**：TODO  
**目标**：扩展 ChatAskResponse / CapabilityExecutionResult / PlanExecutionResult  
**完成定义**：
- 支持 citations
- 支持 artifacts
- 支持 task_context
- 支持 debug

### TASK-002
**标题**：knowledge.ask 输出 citations  
**状态**：TODO  
**目标**：让知识能力 step 级结果包含引用  
**完成定义**：
- step result 含 citations
- API 可透传 citations

### TASK-003
**标题**：data.analyze 输出 artifacts / debug  
**状态**：TODO  
**目标**：让数据能力返回表格 artifact 和 raw_sql  
**完成定义**：
- step result 含 artifacts
- debug 可聚合 raw_sql

### TASK-004
**标题**：PlanExecutionResult 聚合输出  
**状态**：TODO  
**目标**：聚合 citations / artifacts / debug_info  
**完成定义**：
- 多 step 输出可统一聚合

### TASK-005
**标题**：API response contract 测试  
**状态**：TODO  
**目标**：补齐 response contract 自动化测试  
**完成定义**：
- response 顶层字段有测试
- citations / artifacts / task_context 有测试