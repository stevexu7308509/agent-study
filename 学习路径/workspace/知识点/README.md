# Agent 学习知识点索引

> Java 转 Python Agent 开发学习笔记  
> 学习目录: `/Users/zhangluxi/Documents/Ai/Ai学习文档/agent学习/学习路径/workspace/知识点/`  
> 代码目录: `/Users/zhangluxi/Documents/Ai/Ai学习文档/agent学习/学习路径/workspace/PythonProject/`

---

## 📚 知识点列表

| 序号 | 主题 | 文件 | 核心内容 |
|------|------|------|---------|
| 01 | LLM API 调用基础 | [01-LLM-API调用基础.md](01-LLM-API调用基础.md) | OpenAI SDK、Anthropic SDK、流式/非流式、响应结构对比、配置管理 |
| 02 | Prompt 工程 | [02-Prompt工程.md](02-Prompt工程.md) | System Prompt、Persona 设定、Few-Shot vs Zero-Shot、DeepSeek 注意 |
| 03 | 错误处理与重试 | [03-错误处理与重试机制.md](03-错误处理与重试机制.md) | 三种错误类型、指数退避重试、jitter、测试设计 |
| 04 | Tool 工具模式 | [04-Tool工具模式.md](04-Tool工具模式.md) | ToolExecutor、工具注册、SerpApi/Tavily/wttr.in 实战 |
| 05 | ReAct Agent 模式 | [05-ReAct-Agent模式.md](05-ReAct-Agent模式.md) | ReAct 循环、Prompt 模板、输出解析、Agent 主循环 |
| 06 | Python vs Java 对比 | [06-Python-Java对比.md](06-Python-Java对比.md) | 语法速查表、Python 优势、从 Java 视角看差异 |
| 07 | API 成本与延迟 | [07-API成本与延迟测试.md](07-API成本与延迟测试.md) | 延迟测试、Token 计价、成本优化策略 |

---

## 🗺️ 学习路径建议

```
第1-2天: 01 LLM API 调用基础 → 02 Prompt 工程
         理解怎么调 API、怎么写 Prompt

第3天:   06 Python vs Java 对比
         快速补齐 Python 语法差异

第4-5天: 04 Tool 工具模式 → 05 ReAct Agent 模式
         理解 Agent 最核心的 Tool 和 ReAct 循环

第6天:   03 错误处理与重试 → 07 API 成本与延迟
         工程化：重试、成本控制
```

---

## 📂 对应代码结构

```
PythonProject/
├── main.py                    # PyCharm 入口模板
├── .env                       # 环境变量（API Key 等）
├── config/                    # 配置模块
│   ├── __init__.py           # 统一导出 + 工厂函数
│   ├── config.py             # Anthropic 配置
│   └── config_openai.py      # OpenAI 配置
└── basics/                    # 学习练习
    ├── HelloAgentsLLM.py     # LLM 客户端封装（01）
    ├── compare_response_structures.py  # SDK 对比（01）
    ├── practice_1.py         # System Prompt 实验（02）
    ├── practice_1_anthropic.py  # Anthropic 版（02）
    ├── practice_2.py         # Few-Shot vs Zero-Shot（02）
    ├── practice_3.py         # 延迟测试（07）
    ├── practice_3_anthropic.py  # 成本计算（07）
    ├── starter.py            # 错误处理与重试（03）
    ├── ToolExecutor.py       # 工具执行器（04）
    ├── react/                # ReAct Agent（05）
    │   ├── ReAct.py          # Agent 主循环
    │   ├── llm_client.py     # LLM 客户端
    │   └── tools.py          # 工具定义
    └── datawhale/            # 完整 Agent 示例（05+04）
        └── FirstAgentTest.py # 旅行助手 Agent（含 Python vs Java 注释）
```

---

## ⚡ 快速复习卡片

```
🔑 API 调用:   OpenAI(api_key=, base_url=) → .chat.completions.create()
               Anthropic(api_key=, base_url=) → .messages.create(system=)

🎭 Prompt:     System Prompt = 设定角色 + 格式约束
               Few-Shot > Zero-Shot（对小模型）

🔄 ReAct:      Thought → Action → Observation → Thought → ... → Finish

🔧 Tool:       name + description + function → ToolExecutor.registerTool()

🔄 Retry:      指数退避 = base × 2^attempt + jitter
               只重试瞬时故障（网络、限流），不重试永久故障（认证）

💲 Cost:       Haiku(便宜) < Sonnet < Opus < Fable(最强)
               输出价格 ≈ 输入价格的 5 倍
```
