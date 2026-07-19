"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   ReAct Agent — 核心主文件                                   ║
║  模式: Reasoning (推理) + Acting (行动) = ReAct                             ║
║  循环: Thought → Action → Observation → Thought → ... → Finish             ║
╚══════════════════════════════════════════════════════════════════════════════╝

=== 学习路线（按顺序阅读）===
1. 先看本文件的 REACT_PROMPT_TEMPLATE — 理解 Agent 怎么"被提示"
2. 看 run() 方法 — 理解主循环
3. 看 _parse_output() / _parse_action() — 理解怎么解析 LLM 输出
4. 最后看文件末尾的 if __name__ == '__main__' — 理解怎么组装运行

=== ReAct 核心概念 ===
Agent 不是一次性回答问题，而是像人一样"边想边做":
  第1步: Thought(思考) "我需要搜索深圳福田保税区的位置"
         Action(行动)  Search["深圳福田保税区位置"]
         Observation(观察) "福田保税区位于深圳市福田区南部..."

  第2步: Thought "位置知道了，还需要了解产业优势"
         Action  Search["深圳福田保税区产业优势"]
         Observation "产业以高新技术、现代物流为主..."

  第N步: Thought "信息够了，可以回答了"
         Action  Finish["福田保税区位於深圳...产业优势包括..."]

=== 为什么叫 ReAct？===
2012 年 Yao 等人发表的论文《ReAct: Synergizing Reasoning and Acting in Language Models》
ReAct = Reasoning(推理) + Acting(行动) 的结合
论文证明: 让 LLM 交替进行"推理"和"行动"，比单独推理或单独行动效果都好

=== Java 类比 ===
这个类相当于 Java 中:
- 一个 Spring Service Bean
- 依赖注入了 LLMClient(相当于 RestTemplate) 和 ToolExecutor(相当于 Service Registry)
- run() 方法是一个 while 循环，类似于:
  while (steps < maxSteps) {
      String llmOutput = llmClient.generate(prompt);
      Action action = parseAction(llmOutput);
      if (action.isFinish()) return action.getAnswer();
      String observation = toolExecutor.execute(action);
      history.add(observation);
  }
"""

import re
from llm_client import HelloAgentsLLM
from tools import ToolExecutor, search

# ===========================================================================
# 第 1 部分: ReAct Prompt 模板 — Agent 的"使用说明书"
# ===========================================================================
# 这是整个 ReAct 模式最关键的部分。
# Prompt 模板教会 LLM 三件事:
#   1. 你有什么工具可用（{tools}）
#   2. 你必须按什么格式输出（Thought: ... Action: ...）
#   3. 什么时候可以结束（Action: Finish[...]）
#
# 类比 Java: 这相当于定义了一个接口契约(Interface):
#   interface AgentResponse {
#       String getThought();  // 必须返回思考过程
#       Action getAction();   // 必须返回下一步行动
#   }
# LLM 不是强类型的，所以用 Prompt 来"约束"它的输出格式，
# 然后用正则去"解析"这种半结构化输出。
# ===========================================================================

REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}
# ⬆ {tools} 会被替换为工具列表，比如:
#   - Search: 一个网页搜索引擎。当你需要回答关于时事...
# LLM 通过读这段描述来决定"什么时候该调用哪个工具"

请严格按照以下格式进行回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`：调用一个可用工具。
- `Finish[最终答案]`：当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用 `Finish[最终答案]` 来输出最终答案。
# ⬆ 注意: 模板里的双花括号 {{{{}}}} 是 Python format() 的转义，实际输出是单花括号
# 比如 Search["..."]、Finish["..."]

现在，请开始解决以下问题：
Question: {question}
History: {history}
# ⬆ History 是之前所有轮次的记录，让 LLM 知道"已经做了什么、得到了什么结果"
# 没有 History 的话，LLM 会像金鱼一样忘记自己刚调用过什么工具
"""


# ===========================================================================
# 第 2 部分: ReActAgent 类 — Agent 的大脑和手脚
# ===========================================================================
class ReActAgent:
    """
    ReAct Agent 的核心实现。

    职责:
    1. 管理对话历史 (self.history)
    2. 调用 LLM 生成 Thought + Action
    3. 解析 LLM 输出（正则提取）
    4. 执行工具调用
    5. 控制循环终止

    这个类的设计类似 Java 的 Template Method 模式:
    - run() 定义了算法骨架（循环 → 思考 → 行动 → 观察）
    - _parse_output() / _parse_action() 是子步骤
    """

    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 8):
        """
        构造函数。

        参数:
            llm_client:    LLM 客户端，负责调用大模型。类比 Java 的 HttpClient/FeignClient
            tool_executor: 工具执行器，管理所有可用的工具。类比 Java 的 ServiceLocator
            max_steps:     最大循环步数，防止 LLM 陷入死循环。
                           类比 Java 的: while (steps < MAX_ITERATIONS) { ... }
                           为什么需要? LLM 可能:
                           - 反复调用同一个工具得不到结果
                           - 产生幻觉，以为还需要更多信息
                           - 忘记自己已经收集了足够的信息
                           设置上限 = 兜底保护，生产环境通常设 5~10
        """
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []  # 对话历史列表，每条记录是一个字符串

    # ------------------------------------------------------------------
    # run() — Agent 主循环，整个系统的入口
    # ------------------------------------------------------------------
    def run(self, question: str):
        """
        Agent 主循环 — 反复执行 Think → Act → Observe，直到得到最终答案。

        参数:
            question: 用户的问题（自然语言）
        返回:
            最终答案字符串，如果达到最大步数未完成则返回 None

        === 执行流程图 ===

        初始化 history = []
              ↓
        ┌─ for step in range(max_steps) ─────────────────────┐
        │                                                      │
        │  1. 构建 Prompt（工具列表 + 问题 + 历史）             │
        │                    ↓                                  │
        │  2. 调用 LLM.think() → 返回 "Thought:...Action:..."  │
        │                    ↓                                  │
        │  3. 正则解析 → 提取 thought 和 action                 │
        │                    ↓                                  │
        │  4. action 是 "Finish[...]" ?                        │
        │     ├─ 是 → 提取最终答案，return（循环结束）           │
        │     └─ 否 → 继续往下                                  │
        │                    ↓                                  │
        │  5. 解析工具名和参数 → 调用 tool_executor.getTool()   │
        │                    ↓                                  │
        │  6. 执行工具函数 → 得到 observation                   │
        │                    ↓                                  │
        │  7. 把 Action + Observation 追加到 history            │
        │                    ↓                                  │
        │  回到步骤 1（下一轮 LLM 能看到历史了）                 │
        │                                                      │
        └──────────────────────────────────────────────────────┘
            达到 max_steps → return None（任务失败）
        """
        # 每次 run 都重置历史，避免上次对话污染本次
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")

            # ---- 步骤 1: 构建 Prompt ----
            # getAvailableTools() 返回格式:
            #   "- Search: 一个网页搜索引擎。当..."
            #   "- Calculator: 一个计算器。当..."
            tools_desc = self.tool_executor.getAvailableTools()

            # 把历史记录列表拼接成多行字符串
            # 例如: "Action: Search[深圳]\nObservation: 深圳是..."
            history_str = "\n".join(self.history)

            # format() 替换模板中的 {tools}, {question}, {history}
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_desc,
                question=question,
                history=history_str
            )

            # ---- 步骤 2: 调用 LLM ----
            # messages 是 OpenAI SDK 要求的格式
            # 这里只传一条 user message（prompt 本身已包含 system 级别指令）
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)

            if not response_text:
                print("错误：LLM未能返回有效响应。")
                break

            # ---- 步骤 3: 解析 LLM 输出 ----
            # LLM 输出示例:
            #   "Thought: 我需要搜索深圳福田保税区的信息
            #    Action: Search[深圳福田保税区]"
            thought, action = self._parse_output(response_text)

            if thought:
                print(f"🤔 思考: {thought}")

            if not action:
                # LLM 有时不按格式输出 Action，而是直接给答案
                # 如果响应文本不为空且不是纯空白，就当最终答案处理
                if response_text and len(response_text.strip()) > 10:
                    print(f"🎉 最终答案: {response_text.strip()}")
                    return response_text.strip()
                print("警告：未能解析出有效的Action，流程终止。")
                break

            # ---- 步骤 4: 判断是否为 Finish ----
            # Finish 意味着 Agent 认为已经获得足够信息，可以输出最终答案
            if action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                print(f"🎉 最终答案: {final_answer}")
                return final_answer

            # ---- 步骤 5: 解析并执行工具调用 ----
            # 从 "Search[深圳福田保税区]" 中解析出:
            #   tool_name = "Search"
            #   tool_input = "深圳福田保税区"
            tool_name, tool_input = self._parse_action(action)

            if not tool_name or not tool_input:
                # 解析失败，记录错误观察，让 LLM 下一轮知道格式错了
                self.history.append("Observation: 无效的Action格式，请检查。")
                continue  # 跳过本轮，进入下一轮循环

            print(f"🎬 行动: {tool_name}[{tool_input}]")

            # 从 ToolExecutor 中取出函数并执行
            tool_function = self.tool_executor.getTool(tool_name)
            if tool_function:
                # 调用真实的工具函数（比如 SerpApi 搜索）
                observation = tool_function(tool_input)
            else:
                observation = f"错误：未找到名为 '{tool_name}' 的工具。"

            print(f"👀 观察: {observation}")

            # ---- 步骤 6: 记录历史 ----
            # 把本轮的行动和观察加入历史，下一轮 LLM 能看到
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        # 循环结束还没 return，说明达到最大步数
        print("已达到最大步数，流程终止。")
        return None

    # ------------------------------------------------------------------
    # _parse_output() — 从 LLM 原始输出中提取 Thought 和 Action
    # ------------------------------------------------------------------
    def _parse_output(self, text: str):
        r"""
        用正则表达式从 LLM 输出中提取 Thought 和 Action。

        参数:
            text: LLM 原始输出，例如:
                  "Thought: 需要搜索一下\nAction: Search[深圳]\n"
        返回:
            (thought: str | None, action: str | None)

        === 正则表达式详解 ===

        Thought:\s*(.*?)(?=\nAction:|$)
        ┌──────────┬──────────────────────────────────────┐
        │ Thought: │ 字面匹配 "Thought:"                    │
        │ \s*      │ 匹配冒号后的可选空白                    │
        │ (.*?)    │ 捕获组1: 非贪婪匹配任意字符(含换行)      │
        │ (?=...)  │ 正向前瞻: 匹配到但不消费，作为"边界"     │
        │ \nAction:│ 前瞻内容: 换行+Action: (遇到Action停止) │
        │ |        │ 或                                    │
        │ $        │ 前瞻内容: 文本末尾(没有Action也停止)    │
        └──────────┴──────────────────────────────────────┘

        Action:\s*(.*?)$
        ┌──────────┬──────────────────────────────────────┐
        │ Action:  │ 字面匹配 "Action:"                    │
        │ \s*      │ 匹配冒号后的可选空白                    │
        │ (.*?)    │ 捕获组1: 非贪婪匹配任意字符             │
        │ $        │ 文本末尾                               │
        └──────────┴──────────────────────────────────────┘

        re.DOTALL: 让 . 也能匹配换行符 \n
        不使用 DOTALL 的话 .*? 遇到换行就停止了

        Java 等价写法:
        Pattern thoughtPattern = Pattern.compile(
            "Thought:\\s*(.*?)(?=\\nAction:|$)", Pattern.DOTALL);
        Matcher m = thoughtPattern.matcher(text);
        */
        """
        # 提取 Thought: 从 "Thought:" 到 "Action:" 之前（或文本末尾）
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)

        # 提取 Action: 从 "Action:" 到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    # ------------------------------------------------------------------
    # _parse_action() — 解析工具调用 Action
    # ------------------------------------------------------------------
    def _parse_action(self, action_text: str):
        r"""
        从 Action 字符串中解析出工具名和输入参数。

        参数:
            action_text: 例如 "Search[深圳福田保税区]"
        返回:
            (tool_name: str | None, tool_input: str | None)

        === 正则表达式详解 ===

        (\w+)\[(.*)\]
        ┌──────────┬────────────────────────────────────────┐
        │ (\w+)    │ 捕获组1: 一个或多个字母/数字/下划线      │
        │          │ 这是工具名 (比如 Search, Calculator)     │
        │ \[       │ 字面匹配左方括号 [                       │
        │ (.*)     │ 捕获组2: 任意字符(贪婪)，这是工具输入     │
        │ \]       │ 字面匹配右方括号 ]                       │
        └──────────┴────────────────────────────────────────┘

        举例:
          "Search[深圳福田]"   → ("Search", "深圳福田")
          "Finish[最终答案]"   → 这里用 _parse_action_input 处理
          "get_weather(city=\"北京\")" → 这里不处理函数调用格式
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)

    # ------------------------------------------------------------------
    # _parse_action_input() — 解析 Finish 中的最终答案
    # ------------------------------------------------------------------
    def _parse_action_input(self, action_text: str):
        r"""
        从 Finish 指令中提取最终答案。

        参数:
            action_text: 例如 "Finish[深圳是一个美丽的城市...]"
        返回:
            方括号内的最终答案字符串

        === 正则表达式 ===
        \w+\[(.*)\]
        - \w+  匹配 "Finish" 或其他动作名
        - \[   左方括号
        - (.*) 捕获组1: 方括号内的全部内容 → 这就是最终答案
        - \]   右方括号
        """
        match = re.match(r"\w+\[(.*)\]", action_text, re.DOTALL)
        return match.group(1) if match else ""


# ===========================================================================
# 第 3 部分: 运行入口 — 把所有组件拼装起来
# ===========================================================================
if __name__ == '__main__':
    """
    完整运行示例 — 展示如何组装 ReAct Agent。

    组装步骤:
      1. 创建 LLM 客户端 (大脑)
      2. 创建 ToolExecutor (工具箱)
      3. 注册工具 (往工具箱里放工具)
      4. 创建 ReActAgent (把大脑和工具箱组合)
      5. 调用 agent.run(question) (启动)

    类比 Java Spring:
      @Autowired
      private LLMClient llmClient;        // 步骤1
      @Autowired
      private ToolExecutor toolExecutor;  // 步骤2
      // 步骤3: @PostConstruct 中注册工具
      @Autowired
      private ReActAgent agent;           // 步骤4
      agent.run(question);               // 步骤5
    """

    # 步骤 1: 创建 LLM 客户端
    # HelloAgentsLLM 从 .env 读取配置: LLM_MODEL_ID, LLM_API_KEY, LLM_BASE_URL
    llm = HelloAgentsLLM()

    # 步骤 2: 创建工具执行器
    tool_executor = ToolExecutor()

    # 步骤 3: 注册工具
    # 工具描述非常重要! LLM 通过描述来决定"什么时候该用这个工具"
    search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.registerTool("Search", search_desc, search)

    # 步骤 4: 创建 Agent
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)

    # 步骤 5: 运行!
    question = "我想在福田保税区买肯德基，便宜点的？"
    agent.run(question)
