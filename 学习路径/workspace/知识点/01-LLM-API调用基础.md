# 01 - LLM API 调用基础

> **学习日期**: 2026-07  
> **对应代码**: `basics/HelloAgentsLLM.py`, `config/__init__.py`, `basics/compare_response_structures.py`

---

## 1. OpenAI SDK 调用方式

### 1.1 客户端初始化

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-xxx",
    base_url="https://api.deepseek.com",  # 可指向任何兼容 OpenAI 协议的服务
    timeout=60
)
```

**关键点**:
- `base_url` 参数使得可以调用任何兼容 OpenAI 协议的服务（DeepSeek、通义千问、Ollama 本地模型等）
- 不需要为不同服务商换 SDK，统一用 OpenAI SDK

### 1.2 调用 LLM（非流式）

```python
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手"},
        {"role": "user", "content": "你好"}
    ],
    temperature=0,
    stream=False
)

# 取文本
text = response.choices[0].message.content

# 取 token 用量
input_tokens = response.usage.prompt_tokens
output_tokens = response.usage.completion_tokens
total_tokens = response.usage.total_tokens

# 停止原因
finish_reason = response.choices[0].finish_reason
```

### 1.3 调用 LLM（流式）

```python
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=messages,
    temperature=0,
    stream=True  # 开启流式
)

collected_content = []
for chunk in response:
    if not chunk.choices:
        continue
    content = chunk.choices[0].delta.content or ""
    print(content, end="", flush=True)
    collected_content.append(content)

full_text = "".join(collected_content)
```

**流式 vs 非流式对比**:

| 特性 | 非流式 (`stream=False`) | 流式 (`stream=True`) |
|------|------------------------|---------------------|
| 响应方式 | 等全部生成完再返回 | 逐 token 返回 |
| 用户体验 | 需要等待 | 实时看到输出 |
| 编程复杂度 | 简单 | 需要拼接 chunks |
| 适用场景 | 后台处理、批量任务 | 聊天 UI、实时交互 |

---

## 2. Anthropic SDK 调用方式

### 2.1 客户端初始化

```python
from anthropic import Anthropic

client = Anthropic(
    api_key="sk-xxx",
    base_url="https://api.deepseek.com/anthropic"  # 也可走代理
)
```

### 2.2 调用方式

```python
msg = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="你是一个有帮助的助手",  # system prompt 是独立参数！
    messages=[
        {"role": "user", "content": "你好"}
    ]
)

# ⚠️ content 是列表，不是字符串！
# 可能包含: TextBlock, ThinkingBlock 等
for block in msg.content:
    if block.type == "text":
        print(block.text)
    elif block.type == "thinking":
        print(block.thinking)

# 取 token
input_tokens = msg.usage.input_tokens
output_tokens = msg.usage.output_tokens

# 停止原因
stop_reason = msg.stop_reason
```

---

## 3. OpenAI SDK vs Anthropic SDK 关键差异

| 项目 | OpenAI SDK | Anthropic SDK |
|------|-----------|---------------|
| **返回类型** | `ChatCompletion` | `Message` |
| **取文本** | `response.choices[0].message.content` | `msg.content[N].text`（列表，需按 type 过滤） |
| **system prompt** | 放在 `messages` 数组中 | 独立 `system` 参数 |
| **token 用量** | `usage.prompt_tokens` / `completion_tokens` | `usage.input_tokens` / `output_tokens` |
| **停止原因** | `choices[0].finish_reason` | `msg.stop_reason` |
| **content 结构** | 纯字符串 | **列表**（可能含 thinking block） |
| **thinking/推理** | 取决于模型（reasoning_content） | 原生支持 `ThinkingBlock` |

> ⚠️ **最常见的坑**: Anthropic 的 `msg.content` 是列表，不能直接当字符串用！

---

## 4. 封装通用 LLM 客户端

参考 `basics/HelloAgentsLLM.py`：

```python
class HelloAgentsLLM:
    def __init__(self, model=None, apiKey=None, baseUrl=None, timeout=None):
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages, temperature=0) -> str:
        """调用 LLM 并返回响应文本"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        # 处理流式响应...
        return full_text
```

**设计要点**:
- 参数优先级：传入参数 > 环境变量
- 默认使用流式输出，实时反馈
- 配置集中在 `.env` 文件中，不硬编码

---

## 5. 配置管理模式

参考 `config/__init__.py`：

```python
# config/config.py - OpenAI 配置
KEY = "sk-xxx"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"

# config/config_openai.py - Anthropic 配置（走代理）
KEY = "sk-xxx"
BASE_URL = "https://api.deepseek.com/anthropic"
MODEL = "deepseek-v4-flash"

# config/__init__.py - 统一导出 + 工厂函数
from .config import KEY as ANTHROPIC_KEY, ...
from .config_openai import KEY as OPENAI_KEY, ...

def create_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_KEY, base_url=OPENAI_BASE_URL)

def create_anthropic_client():
    from anthropic import Anthropic
    return Anthropic(api_key=ANTHROPIC_KEY, base_url=ANTHROPIC_BASE_URL)
```

**优点**: 统一入口、切换方便、测试时可 mock

---

## 复习要点

1. OpenAI SDK 的 `base_url` 参数是关键——一套 SDK 调所有兼容服务
2. Anthropic SDK 的 `content` 是**列表**，需要处理 `ThinkingBlock`
3. 流式输出适合聊天场景，非流式适合批量处理
4. 配置统一管理在 `config/` 模块，不要散落在各处
