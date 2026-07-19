# 05 - ReAct Agent 模式

> **学习日期**: 2026-07  
> **对应代码**: `basics/react/ReAct.py`, `basics/datawhale/FirstAgentTest.py`

---

## 1. 什么是 ReAct？

**ReAct = Reasoning（推理）+ Acting（行动）**

这是 Agent 最核心的模式。Agent 不是一次性回答问题，而是循环执行：

```
Thought（思考）→ Action（行动）→ Observation（观察）→ Thought → Action → ...
```

直到收集足够信息后输出最终答案。

---

## 2. ReAct 循环架构

```
┌──────────────────────────────────────────┐
│              Agent Loop                    │
│                                           │
│  ┌─────────┐    ┌─────────┐    ┌────────┐│
│  │ Thought │ →  │ Action  │ →  │Observe ││
│  │ (LLM)   │    │ (Tool)  │    │(Result)││
│  └─────────┘    └─────────┘    └────────┘│
│       ↑                              │    │
│       └──────────────────────────────┘    │
│              (反馈到下一轮)                 │
└──────────────────────────────────────────┘
```

---

## 3. ReAct Prompt 模板

```python
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

请严格按照以下格式进行回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`：调用一个可用工具。
- `Finish[最终答案]`：当你认为已经获得最终答案时。

现在，请开始解决以下问题：
Question: {question}
History: {history}
"""
```

**模板中的关键变量**:
| 变量 | 内容 | 作用 |
|------|------|------|
| `{tools}` | 工具列表描述 | 让 LLM 知道有哪些工具可用 |
| `{question}` | 用户问题 | 要解决的目标 |
| `{history}` | 历史记录 | 让 LLM 知道之前做了什么 |

---

## 4. ReAct Agent 核心实现

```python
class ReActAgent:
    def __init__(self, llm_client, tool_executor, max_steps=5):
        self.llm_client = llm_client          # LLM 客户端
        self.tool_executor = tool_executor    # 工具执行器
        self.max_steps = max_steps            # 最大步数（防止死循环）
        self.history = []                     # 对话历史

    def run(self, question: str):
        self.history = []
        current_step = 0
        
        while current_step < self.max_steps:
            current_step += 1
            
            # 1. 构建 Prompt（工具列表 + 问题 + 历史）
            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_desc, question=question, history=history_str
            )
            
            # 2. 调用 LLM 生成 Thought + Action
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)
            
            # 3. 解析输出
            thought, action = self._parse_output(response_text)
            
            # 4. 判断是否结束
            if action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                return final_answer  # 任务完成！
            
            # 5. 执行工具调用
            tool_name, tool_input = self._parse_action(action)
            tool_function = self.tool_executor.getTool(tool_name)
            observation = tool_function(tool_input)
            
            # 6. 记录历史
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")
        
        print("已达到最大步数，流程终止。")
        return None
```

---

## 5. 输出解析（用正则）

LLM 的输出格式是半结构化的自然语言，需要用正则提取：

```python
def _parse_output(self, text: str):
    # 提取 Thought: ... 直到 Action: 之前
    thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
    # 提取 Action: ... 直到文本末尾
    action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
    return thought_match.group(1).strip(), action_match.group(1).strip()

def _parse_action(self, action_text: str):
    # 解析 "Search[深圳福田保税区]" → ("Search", "深圳福田保税区")
    match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
    return (match.group(1), match.group(2)) if match else (None, None)

def _parse_action_input(self, action_text: str):
    # 解析 "Finish[这是一个好地方]" → "这是一个好地方"
    match = re.match(r"\w+\[(.*)\]", action_text, re.DOTALL)
    return match.group(1) if match else ""
```

**为什么用正则而不是 JSON Schema？**
- ReAct 格式是约定俗成的文本格式
- 不需要强制 Function Calling（兼容更多模型）
- 更灵活，LLM 可以在 Thought 中自由表达

---

## 6. Agent 完整执行示例

```
用户提问: "深圳福田保税区在哪里，有什么产业优势？"

--- 第 1 步 ---
🤔 思考: 我需要先搜索深圳福田保税区的位置信息
🎬 行动: Search[深圳福田保税区位置]
👀 观察: 福田保税区位于深圳市福田区南部，毗邻香港...

--- 第 2 步 ---
🤔 思考: 已经知道位置，现在需要了解产业优势
🎬 行动: Search[深圳福田保税区产业优势]
👀 观察: 产业以高新技术、现代物流、跨境电商为主...

--- 第 3 步 ---
🤔 思考: 信息已经足够回答用户问题了
🎬 行动: Finish[福田保税区位于深圳福田区南部...产业优势包括...]
🎉 最终答案: ...
```

---

## 7. 关键设计决策

### max_steps（最大步数）
```python
max_steps = 5  # 防止 LLM 无限循环
```
**为什么需要？** LLM 可能陷入无法完成的任务，一直调用工具但不收敛。设置上限保护。

### history（历史记录）
```python
self.history.append(f"Action: {action}")
self.history.append(f"Observation: {observation}")
```
每轮的 Action 和 Observation 都记录，下一轮全部传给 LLM，让 LLM 知道"之前做了什么、得到什么结果"。

### 截断多余的 Thought-Action
```python
# LLM 有时一次输出多对 Thought-Action，只取第一对
match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:)|\Z)', 
                  llm_output, re.DOTALL)
```
LLM 有时会"抢答"，一次输出好几步。需要截断，一次只执行一步。

---

## 8. ReAct vs Function Calling

| 特性 | ReAct | Function Calling |
|------|-------|-----------------|
| 实现方式 | Prompt 模板 + 正则解析 | API 原生支持 |
| 模型要求 | 任何能遵循格式的模型 | 需要模型支持 FC |
| 灵活性 | 高，可自定义格式 | 受限于 API 规范 |
| 可靠性 | 依赖正则，可能解析失败 | API 保证 JSON 格式 |
| 适用场景 | 教学、老模型、定制需求 | 生产环境首选 |

---

## 复习要点

1. ReAct = Thought → Action → Observation 循环
2. Prompt 模板告诉 LLM 格式规则（工具列表 + 历史 + 格式要求）
3. 正则解析 LLM 输出（因为 LLM 返回的是自然语言+标记，不是 JSON）
4. `max_steps` 防止死循环，`history` 提供上下文
5. 生产环境推荐 Function Calling，ReAct 更适合学习和理解 Agent 原理
