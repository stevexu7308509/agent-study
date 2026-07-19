"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              llm_client.py — LLM 客户端封装                                  ║
║  职责: 封装 OpenAI 兼容的 API 调用，对外暴露一个简单的 think() 方法          ║
╚══════════════════════════════════════════════════════════════════════════════╝

=== 学习路线 ===
1. 看 __init__()  — 理解客户端怎么初始化（配置从哪来）
2. 看 think()    — 理解怎么调用 LLM、怎么处理流式响应
3. 看文件末尾    — 理解怎么单独测试这个客户端

=== 为什么需要封装一层？===
直接调用 openai.OpenAI 也可以，但封装的好处:
  1. 统一配置管理（从 .env 读取，不用每次传 api_key）
  2. 统一错误处理（所有调用方不需要重复 try/except）
  3. 方便切换模型（只改一处配置，不侵入业务代码）
  4. 方便 Mock 测试（ReActAgent 依赖的是 HelloAgentsLLM 接口，不是具体的 OpenAI）

Java 类比:
  这层封装类似于:
    @Service
    class LLMService {
        private final RestTemplate restTemplate;
        public String chat(List<Message> messages) { ... }
    }
  而不是每个 Controller 都 new RestTemplate() 然后自己拼 URL。

=== 流式响应 (Streaming) ===
本客户端默认使用 stream=True（流式输出）。
流式输出的好处: 用户可以实时看到 LLM "在打字"，体验更好。
代价: 代码比非流式复杂一点，需要拼接 chunks。

非流式代码只需要一行:
  return response.choices[0].message.content
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

# 加载 .env 文件中的环境变量
# 这是一个重要步骤: Python 不会自动读取 .env，必须显式调用 load_dotenv()
# 之后 os.getenv() 才能读取到 .env 中定义的变量
load_dotenv()


class HelloAgentsLLM:
    """
    为本书 "Hello Agents" 定制的 LLM 客户端。

    它用于调用任何兼容 OpenAI 接口的服务（DeepSeek、Ollama、通义千问等），
    并默认使用流式响应。

    === OpenAI 兼容协议 ===
    目前业界大部分模型服务商都兼容 OpenAI 的 API 协议:
      - POST /v1/chat/completions
      - 请求体: {"model": "...", "messages": [...], "stream": true/false}
      - 响应体: ChatCompletion 对象

    所以只需要 openai 这一个 SDK，就能调用几乎所有商业/开源模型。
    关键参数是 base_url:
      - DeepSeek:  https://api.deepseek.com
      - Ollama:    http://localhost:11434/v1
      - 通义千问:   https://dashscope.aliyuncs.com/compatible-mode/v1
      - 任何自部署的 vLLM/Ollama/LM Studio 服务
    """

    def __init__(self, model: str = None, apiKey: str = None,
                 baseUrl: str = None, timeout: int = None):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。

        参数优先级: 传入参数 > 环境变量 > 报错
        这种设计允许:
          - 生产环境: 不传参数，全从 .env 读取
          - 测试环境: 传入 mock 参数，绕过 .env
          - 多模型: 创建多个实例，传不同的 model 参数

        参数:
            model:   模型 ID，如 "deepseek-v4-flash", "gpt-4o"
            apiKey:  API 密钥
            baseUrl: API 服务地址
            timeout: 请求超时秒数，默认 60
        """
        # self.model 用传入的，没有则读环境变量 LLM_MODEL_ID
        self.model = model or os.getenv("LLM_MODEL_ID")

        # 这三个只用局部变量（不需要被外部访问，不存 self）
        # 注意: Python 方法内的变量默认局部，不需要像 Java 那样声明
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        # ⬆ os.getenv("KEY", default): 第二个参数是默认值
        # int() 转换是因为环境变量是字符串，OpenAI 构造函数要 int

        # 三个必须的参数缺一不可
        if not all([self.model, apiKey, baseUrl]):
            # all(): Python 内置函数，所有元素为 True 才返回 True
            # 等价于 Java: model != null && apiKey != null && baseUrl != null
            raise ValueError(
                "模型ID、API密钥和服务地址必须被提供或在.env文件中定义。"
            )

        # 创建 OpenAI 客户端实例
        # 这里用了 openai 库，但 base_url 指向 DeepSeek
        # openai 库本身不关心你在调谁，只要对方兼容 OpenAI 协议
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用大语言模型进行思考，并返回其响应文本。

        这是 Agent 调用 LLM 的唯一入口。
        封装了: API 调用 + 流式处理 + 异常处理。

        参数:
            messages:    消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 随机性控制，0=确定性的，1=随机的。
                         Agent 场景通常用 0（要稳定的输出，不是创意）

        返回:
            LLM 的完整响应文本（字符串），出错返回 None

        === temperature 参数 ===
        temperature = 0: LLM 每次都选概率最高的 token，输出稳定可复现
        temperature = 1: LLM 按概率采样，输出多样有创意
        对于 Agent 来说，我们需要 LLM 严格遵循 ReAct 格式，
        所以 temperature=0 是最佳选择（输出格式不会乱）。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            # ---- 调用 API（流式） ----
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,  # 开启流式输出
            )

            # ---- 处理流式响应 ----
            # 流式响应是一个迭代器（Iterator），每次 yield 一个 chunk
            # 每个 chunk 包含一个 delta（增量），可能是 content 或空
            #
            # chunk 结构示意:
            #   ChatCompletionChunk(
            #       choices=[Choice(delta=ChoiceDelta(content="你"), index=0)],
            #       ...
            #   )
            #   ChatCompletionChunk(
            #       choices=[Choice(delta=ChoiceDelta(content="好"), index=0)],
            #       ...
            #   )
            #   最后一个 chunk: delta.content 为 None 或 ""
            print("✅ 大语言模型响应成功:")
            collected_content = []  # 用列表收集片段（最后再 join，比字符串拼接高效）

            for chunk in response:
                # 有些 chunk 可能没有 choices（比如只有 usage 信息的 chunk）
                if not chunk.choices:
                    continue

                # delta.content 是增量文本，可能为 None
                content = chunk.choices[0].delta.content or ""

                # 实时打印（用户体验）
                print(content, end="", flush=True)
                # flush=True: 立即输出到终端，不等待缓冲区满
                # end="": 不换行（流式输出要连续）

                collected_content.append(content)

            print()  # 流式输出结束后换行
            return "".join(collected_content)
            # ⬆ "".join(list): Python 惯用的列表→字符串方式
            # 为什么不用 s += content? 因为 Python 字符串是不可变的，
            # 每次 += 都会创建新字符串，O(n²) 复杂度。
            # join() 只创建一次，O(n) 复杂度。

        except Exception as e:
            # 通用异常捕获
            # ⚠ 注意: 这里返回 None，而不是 raise！
            # 因为 Agent 还在跑，LLM 调用失败不能拖垮整个循环
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None


# ===========================================================================
# 独立测试 — 验证客户端是否正常工作
# ===========================================================================
if __name__ == '__main__':
    """
    单独测试 LLM 客户端，不依赖 Agent。

    测试步骤:
      1. 创建客户端（读取 .env 配置）
      2. 构造消息
      3. 调用 think()
      4. 打印结果
    """
    try:
        # 创建客户端（不传参数 = 全部从 .env 读取）
        llmClient = HelloAgentsLLM()

        # 构造对话消息
        # system 消息: 设定 AI 的角色
        # user 消息:   具体的问题
        exampleMessages = [
            {"role": "system",
             "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个快速排序算法"}
        ]

        print("--- 调用LLM ---")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print("\n\n--- 完整模型响应 ---")
            print(responseText)

    except ValueError as e:
        # 初始化失败（比如 .env 没配置）
        print(e)
