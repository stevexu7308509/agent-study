# 04 - Tool 工具模式

> **学习日期**: 2026-07  
> **对应代码**: `basics/ToolExecutor.py`, `basics/react/tools.py`, `basics/HelloAgentsLLM.py`

---

## 1. 什么是 Tool（工具）？

在 Agent 架构中，**Tool** 是 Agent 可以调用的外部能力单元。Agent 本身是 LLM（只能生成文本），通过 Tool 可以：
- 🌐 搜索网页
- 📊 查询数据库
- 📧 发送邮件
- 🐍 执行代码
- 🌤️ 查询天气

**本质**: Tool = 一个**函数** + 一段**描述**（让 LLM 知道何时使用它）

---

## 2. ToolExecutor 模式

### 2.1 核心实现

```python
from typing import Dict, Any

class ToolExecutor:
    """
    工具执行器：管理和执行工具。
    这是一个"工具注册中心"，Agent 通过它发现和调用工具。
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        """向工具箱注册一个新工具"""
        if name in self.tools:
            print(f"警告: 工具 '{name}' 已存在，将被覆盖。")
        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")

    def getTool(self, name: str) -> callable:
        """根据名称获取工具的执行函数"""
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """获取所有可用工具的格式化描述（给 LLM 看的）"""
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])
```

### 2.2 设计要点

| 要素 | 说明 |
|------|------|
| **name** | 工具的唯一标识，LLM 用它来指定调用哪个工具 |
| **description** | 工具的功能描述，LLM 用它来决定何时调用 |
| **func** | 实际执行的函数，返回 Observation |
| **getAvailableTools()** | 生成给 LLM 的"菜单"，让 LLM 知道有哪些工具可用 |

---

## 3. 注册工具的两种方式

### 方式一：ToolExecutor 类（Python 风格）

```python
toolExecutor = ToolExecutor()
toolExecutor.registerTool(
    "Search",
    "一个网页搜索引擎。当你需要回答关于时事、事实问题时使用。",
    search_function
)
```

### 方式二：字典直存（更简洁）

```python
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}

# 调用
if tool_name in available_tools:
    observation = available_tools[tool_name](**kwargs)
```

> Python 中函数是一等公民（first-class citizen），可以直接存入字典。Java 需要用到 `Map<String, Function>` + Lambda/Method Reference。

---

## 4. 实战工具示例

### 4.1 SerpApi 网页搜索

```python
from serpapi import SerpApiClient

def search(query: str) -> str:
    """基于 SerpApi 的网页搜索引擎"""
    api_key = os.getenv("SERPAPI_API_KEY")
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "gl": "cn",
        "hl": "zh-cn",
    }
    client = SerpApiClient(params)
    results = client.get_dict()
    
    # 智能解析：优先返回最直接的答案
    if "answer_box" in results:
        return results["answer_box"]["answer"]
    if "knowledge_graph" in results:
        return results["knowledge_graph"]["description"]
    if "organic_results" in results:
        snippets = [f"[{i+1}] {res['title']}\n{res['snippet']}"
                    for i, res in enumerate(results["organic_results"][:3])]
        return "\n\n".join(snippets)
    return "未找到相关信息。"
```

### 4.2 wttr.in 天气查询

```python
import requests

def get_weather(city: str) -> str:
    """调用 wttr.in API 查询天气（免费，不需要 API Key）"""
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    current = data['current_condition'][0]
    weather_desc = current['weatherDesc'][0]['value']
    temp_c = current['temp_C']
    return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"
```

### 4.3 Tavily AI 搜索

```python
from tavily import TavilyClient

def get_attraction(city: str, weather: str) -> str:
    """根据城市和天气，用 Tavily 搜索推荐旅游景点"""
    api_key = os.environ.get("TAVILY_API_KEY")
    tavily = TavilyClient(api_key=api_key)
    
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"
    response = tavily.search(query=query, search_depth="basic", include_answer=True)
    
    if response.get("answer"):
        return response["answer"]  # Tavily 的 AI 总结答案
    
    # 否则返回搜索结果列表
    formatted = [f"- {r['title']}: {r['content']}" 
                 for r in response.get("results", [])]
    return "\n".join(formatted)
```

---

## 5. Tool 描述的重要性

LLM 通过 **description** 来决定是否调用工具，所以描述需要：

```
✅ "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"

❌ "搜索工具"  ← 太简单，LLM 不知道该什么时候用
```

**好的工具描述包含**:
1. 工具能做什么
2. 适合什么场景
3. 参数含义

---

## 6. Tool 调用流程

```
Agent (LLM)
  ↓ Action: Search["今天天气怎么样"]
ToolExecutor
  ↓ getTool("Search")
search() 函数执行
  ↓ 返回结果
Observation: "北京今天晴，25°C"
  ↓
Agent (LLM) 基于 Observation 决定下一步
```

---

## 复习要点

1. Tool = 函数 + 描述，描述决定 LLM 会不会正确使用它
2. Python 函数是一等公民，可以直接存入字典作为工具注册表
3. ToolExecutor 的 `getAvailableTools()` 生成 LLM 的"菜单"
4. 工具函数应有完善的异常处理，返回友好的错误信息而非崩溃
