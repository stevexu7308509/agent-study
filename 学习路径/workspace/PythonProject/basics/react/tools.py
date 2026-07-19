"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   tools.py — 工具定义与工具执行器                            ║
║  负责两件事:                                                                 ║
║    1. ToolExecutor 类 — 工具注册中心（注册、查找、描述）                     ║
║    2. search() 函数 — 一个基于 SerpApi 的实战搜索工具                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

=== 学习路线 ===
1. 先看 ToolExecutor 类 — 理解"工具注册中心"模式
2. 再看 search() 函数 — 理解一个"工具函数"长什么样
3. 最后看文件末尾的 if __name__ == '__main__' — 理解怎么独立使用

=== 核心概念: 为什么需要 ToolExecutor？===
LLM 本身是"纯文本生成器"，不能:
  - 搜索网页 → 需要搜索工具
  - 查询数据库 → 需要数据库工具
  - 发送邮件   → 需要邮件工具
  - 执行代码   → 需要代码工具

ToolExecutor 就是一个"注册中心"，管理所有这些工具的:
  - 注册 (registerTool):   把一个函数 + 描述加入工具箱
  - 查找 (getTool):        根据名字取出函数
  - 描述 (getAvailableTools): 生成工具菜单给 LLM 看

Java 类比:
  ToolExecutor ≈ Java 的 ServiceLocator / Registry 模式
  registerTool ≈ Map.put(name, ServiceDescriptor)
  getTool ≈ Map.get(name)
  getAvailableTools ≈ 生成 Swagger API 文档
"""

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
# .env 文件内容示例:
#   SERPAPI_API_KEY=your_key_here
#   LLM_MODEL_ID=deepseek-v4-flash
#   LLM_API_KEY=sk-xxx
#   LLM_BASE_URL=https://api.deepseek.com
load_dotenv()

import os
from serpapi import SerpApiClient
from typing import Dict, Any


# ===========================================================================
# 第 1 部分: search() — 一个"工具函数"的标准写法
# ===========================================================================
def search(query: str) -> str:
    """
    一个基于 SerpApi 的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。

    === 什么是 SerpApi？===
    SerpApi 是一个第三方搜索 API 服务，帮你抓取 Google 搜索结果。
    它处理了代理 IP、验证码、反爬等问题，返回结构化的 JSON。
    官网: https://serpapi.com

    === 工具函数的设计规范 ===
    一个"好的工具函数"应该:
      1. 参数简单（字符串或基本类型），LLM 传参才不会出错
      2. 返回值是字符串（因为 LLM 只能读文本）
      3. 完善的异常处理（工具出错不能拖垮整个 Agent）
      4. 返回友好错误信息（让 LLM 知道"出错了，换个方式试试"）

    参数:
        query: 搜索关键词（LLM 决定传什么）
    返回:
        搜索结果字符串（直接给 LLM 看的 Observation）

    Java 类比:
        public String search(String query) {
            // 工具函数的签名很简单: String → String
        }
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        # ---- 读取 API Key ----
        # os.getenv() 安全读取环境变量，不存在返回 None
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误:SERPAPI_API_KEY 未在 .env 文件中配置。"

        # ---- 构造搜索参数 ----
        params = {
            "engine": "google",      # 使用 Google 搜索引擎
            "q": query,              # 搜索关键词
            "api_key": api_key,      # SerpApi 密钥
            "gl": "cn",              # 国家代码: cn = 中国
            "hl": "zh-cn",           # 语言代码: zh-cn = 简体中文
        }

        # ---- 执行搜索 ----
        # SerpApiClient 封装了 HTTP 请求和 JSON 解析
        client = SerpApiClient(params)
        results = client.get_dict()  # 返回 dict，类似 Java Map<String, Object>

        # ---- 智能解析: 优先级从高到低 ----
        # 搜索结果有多种格式，我们要"挑最好的"返回给 LLM

        # 优先级1: answer_box_list（答案列表，比如"北京有哪些景点"）
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])

        # 优先级2: answer_box → answer（直接答案，比如"珠穆朗玛峰多高"）
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]

        # 优先级3: knowledge_graph → description（知识图谱，比如公司/名人信息）
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]

        # 优先级4: organic_results（普通搜索结果，取前3条摘要）
        if "organic_results" in results and results["organic_results"]:
            snippets = [
                f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
                # ⬆ 列表推导式: 等价于 Java stream().map().limit(3).toList()
            ]
            return "\n\n".join(snippets)

        # 什么都没有找到
        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        # 任何异常都捕获，返回友好错误信息
        # 注意: 不要在这里 raise! Agent 调用工具时如果抛异常，
        # Agent 循环就会崩溃。应该返回错误字符串作为 Observation。
        return f"搜索时发生错误: {e}"


# ===========================================================================
# 第 2 部分: ToolExecutor — 工具注册中心
# ===========================================================================
class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具。

    === 设计模式: Registry Pattern ===

    ToolExecutor 就像一个"工具箱":
      - registerTool()  = 往工具箱里放工具
      - getTool()       = 从工具箱里取工具
      - getAvailableTools() = 列出工具箱里所有工具的"说明书"

    内部数据结构:
      self.tools = {
          "Search": {
              "description": "一个网页搜索引擎...",
              "func": <function search at 0x...>  ← Python 函数是一等公民
          },
          "Calculator": {
              "description": "一个计算器...",
              "func": <function calculate at 0x...>
          }
      }

    === 为什么函数可以作为值存入字典？===
    这是 Python 和 Java 的一个重要差异:
      Python: 函数是一等公民（first-class citizen），可以:
        - 赋值给变量: f = search
        - 存入字典: tools["Search"] = search
        - 作为参数传递: executor.registerTool("S", "desc", search)

      Java: 需要 Function 接口 + Lambda 包装:
        Map<String, Function<String, String>> tools = new HashMap<>();
        tools.put("Search", query -> search(query));
        // 或 tools.put("Search", this::search);

    所以在 Agent 开发中，Python 的"函数即对象"特性让工具注册非常简洁。
    """

    def __init__(self):
        """
        初始化空的工具字典。
        self.tools 的结构:
          {
              "工具名": {
                  "description": "工具描述（给 LLM 看）",
                  "func": <实际执行的函数>
              }
          }
        """
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        """
        向工具箱中注册一个新工具。

        参数:
            name:        工具名称（唯一标识），LLM 通过这个名字来调用
            description: 工具描述，告诉 LLM "什么时候该用这个工具"
            func:        实际执行的函数

        === 工具描述为什么重要？===
        描述是 LLM 决定"什么时候调用哪个工具"的依据。好的描述:
          ✅ "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中
              找不到的信息时，应使用此工具。"
          ❌ "搜索工具"  ← LLM 不知道什么时候该用它

        描述应该包含:
          1. 工具能做什么
          2. 什么场景下使用
          3. 预期输入格式（如果复杂的话）
        """
        if name in self.tools:
            print(f"警告:工具 '{name}' 已存在，将被覆盖。")
            # ⬆ 设计决策: 允许覆盖而非抛异常
            # 原因: Agent 在开发调试时可能会重新注册同名工具

        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")

    def getTool(self, name: str) -> callable:
        """
        根据名称获取一个工具的执行函数。

        参数:
            name: 工具名称
        返回:
            工具函数，如果不存在则返回 None

        注意: 返回 None 而不是抛异常。
        ReActAgent.run() 中会检查 None 并生成友好的错误 Observation，
        让 LLM 知道"这个工具不存在"，而不是让整个循环崩溃。
        """
        return self.tools.get(name, {}).get("func")
        # ⬆ dict.get(key, default) 安全取值，key 不存在返回 default
        # {} 是链式调用的中间默认值: 先取 tools[name]，不存在则 {}.get("func") → None

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。

        === 这个方法是给 LLM 看的 ===
        返回值会被插入到 REACT_PROMPT_TEMPLATE 的 {tools} 位置。

        输出格式:
          - Search: 一个网页搜索引擎。当你需要回答...
          - Calculator: 一个计算器工具。当你需要进行数学计算时...

        LLM 通过读这段文本来了解自己有哪些"超能力"。
        这就是所谓的 "Tool-Augmented LLM"——LLM 的能力不再局限于训练数据。
        """
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])
        # ⬆ 列表推导式 + join: Python 惯用写法
        # Java 等价: tools.entrySet().stream()
        #                .map(e -> "- " + e.getKey() + ": " + e.getValue().getDescription())
        #                .collect(Collectors.joining("\n"))


# ===========================================================================
# 第 3 部分: 独立运行 — 测试工具是否正常工作
# ===========================================================================
if __name__ == '__main__':
    """
    不通过 Agent，直接测试工具是否正常工作。

    这是开发时的好习惯: 先单独测试每个工具，确认 OK 后再接入 Agent。
    """
    # 1. 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 2. 注册搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.registerTool("Search", search_description, search)

    # 3. 查看所有已注册的工具
    print("\n--- 可用的工具 ---")
    print(toolExecutor.getAvailableTools())

    # 4. 模拟 Agent 调用: 查一个实时性问题
    print("\n--- 执行 Action: Search['英伟达最新的GPU型号是什么'] ---")
    tool_name = "Search"
    tool_input = "英伟达最新的GPU型号是什么"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察 (Observation) ---")
        print(observation)
    else:
        print(f"错误:未找到名为 '{tool_name}' 的工具。")
