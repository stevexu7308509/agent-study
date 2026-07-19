# 02 - Prompt 工程

> **学习日期**: 2026-07  
> **对应代码**: `basics/practice_1.py`, `basics/practice_2.py`

---

## 1. System Prompt（系统提示词）

### 1.1 概念

System Prompt 是给 LLM 设定的"角色"和"行为规则"，它定义了：
- LLM 的身份/人格
- 回答的格式要求
- 行为约束和边界

### 1.2 OpenAI SDK 方式

```python
messages = [
    {"role": "system", "content": "你是严谨的合约律师。回答要精准..."},
    {"role": "user", "content": "请帮我解释什么是租赁合约。"}
]
response = client.chat.completions.create(model=..., messages=messages)
```

### 1.3 Anthropic SDK 方式

```python
# system 是独立参数，不在 messages 数组里！
msg = client.messages.create(
    model=...,
    system="你是严谨的合约律师。回答要精准...",
    messages=[{"role": "user", "content": "请帮我解释什么是租赁合约。"}]
)
```

---

## 2. 同问题、不同 Persona 实验

同一个用户问题，三种不同的 system prompt：

```python
SYSTEM_PROMPTS = {
    "严肃律师": "你是严谨的合约律师。回答要精准、引用法条编号、避免任何主观形容词。",
    "幼儿园老师": "你是温柔的幼儿园老师、要对 5 岁小孩说话。用比喻、口语、少于 80 字。",
    "JSON 机器": "你只回 JSON。schema: {\"answer\": string, \"confidence\": float}",
}
USER_MSG = "请帮我解释什么是租赁合约。"
```

**观察结果**:
| Persona | 回答特点 |
|---------|---------|
| 严肃律师 | 长文本、引用法条、结构化 |
| 幼儿园老师 | 简短、比喻多、口语化 |
| JSON 机器 | 严格 JSON 格式 |

**核心启示**: System Prompt 决定了大模型的**输出风格、长度、格式、严谨度**。

---

## 3. Few-Shot vs Zero-Shot Prompting

### 3.1 Zero-Shot（零样本）

不提供任何示例，直接让模型推理：

```python
prompt = f"input: {text}\noutput:"
# 模型全靠自己的知识来判断
```

### 3.2 Few-Shot（少样本）

提供 2-3 个示例，让模型模仿：

```python
FEW_SHOT_EXAMPLES = """范例：
input: 这家餐厅的牛排好吃到让我哭出来。
output: 正面

input: 服务生态度很差、我再也不会来了。
output: 负面

input: 这家店位于新北市三重区。
output: 中立
"""

prompt = FEW_SHOT_EXAMPLES + "\n" + f"input: {text}\noutput:"
```

### 3.3 实际对比结果

| 方法 | 正确率 | 特点 |
|------|--------|------|
| Zero-Shot | 较低 | "中立"容易被误判为正面或负面 |
| Few-Shot (3-shot) | 明显提升 | 模型学会了"中立"的判断标准 |

### 3.4 何时用 Few-Shot

- ✅ 分类任务、格式化输出、特定风格
- ✅ 小模型（如本地模型 gemma4）Zero-Shot 差时
- ✅ 边界情况多的任务
- ❌ 大模型（如 Claude）已经很擅长的通用任务
- ❌ 示例过多会增加 token 成本

---

## 4. Prompt 设计关键原则

### 4.1 角色设定
```
"你是X领域的专家，你的回答风格是Y"
```

### 4.2 格式约束
```
"你只回 JSON。schema: {...}"
"回答要少于 80 字"
"用 Markdown 格式回答"
```

### 4.3 思维链引导
```
"请一步步思考...首先分析...然后..."
```

### 4.4 示例驱动
```
"以下是范例：input → output。现在处理新的 input。"
```

---

## 5. DeepSeek 模型的特殊注意

部分 DeepSeek 模型有"思考模式"，会先内部推理再输出：
- 需要在 `max_tokens` 中给思考留空间
- 思考内容可能影响输出质量
- 在 `practice_2.py` 中注释：`# DeepSeek 思考模式需预留 token 给思考+输出`

---

## 复习要点

1. System prompt = 给 LLM "戴上面具"，决定输出风格
2. Anthropic 的 system 是独立参数，OpenAI 放在 messages 里
3. Few-Shot 对小模型提升明显，大模型不一定需要
4. Prompt 设计四要素：角色、格式、思维链、示例
