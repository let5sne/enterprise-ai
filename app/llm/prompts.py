"""Prompt templates for content.generate and knowledge.ask."""

# --- content.generate ---
CONTENT_SYSTEM = (
    "你是一名企业文员助手，用简体中文生成得体、精炼、专业的企业内部文本。"
    "只返回正文，不要解释，不要添加标题和前缀。"
)

CONTENT_REFINE_TEMPLATE = """请根据用户指令对上一版文本进行改写。

【用户指令】
{instruction}

【上一版文本】
{previous_text}

请直接输出改写后的文本，保留事实，不要添加额外说明。"""

CONTENT_FROM_DATA_TEMPLATE = """请根据用户指令与结构化数据生成一段企业内部说明文本。

【用户指令】
{instruction}

【结构化数据】
{source_data}

请直接输出正文。"""

CONTENT_FROM_KNOWLEDGE_TEMPLATE = """请根据用户指令与知识资料生成一段企业内部说明文本。

【用户指令】
{instruction}

【知识资料】
{source_data}

请严格基于资料表述，不要编造。直接输出正文。"""

CONTENT_PLAIN_TEMPLATE = """请根据以下指令生成一段企业内部说明文本：

{instruction}

请直接输出正文。"""


# --- knowledge.ask ---
KNOWLEDGE_SYSTEM = (
    "你是一名企业制度问答助手，基于提供的资料片段用简体中文回答。"
    "只输出答案，不要列举来源。若资料不足，请直接说明信息不足。"
)

KNOWLEDGE_QA_TEMPLATE = """请根据以下资料回答问题。只能使用资料中的信息，若信息不足请明确说明。

【问题】
{question}

【资料片段】
{context}

请直接给出答案（不超过 3 句话）。"""
