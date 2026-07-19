# ===========================================================================
# 第 1-24 行：Agent 系统提示词 (System Prompt)
# 相当于 Java 中定义了一个 String 常量，告诉 LLM 它的角色和行为规则
# Python 中 """...""" 是多行字符串（text block），Java 15+ 可以用 """...""" 类似
# ===========================================================================
AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对Thought-Action
- Action必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束

请开始吧！
"""

# ===========================================================================
# 第 26 行：导入第三方库
# Python: import requests  等价于  Java: import java.net.http.*;
# Python不需要在文件顶部写所有import，可以写在任何位置（但惯例放在顶部）
# requests 是 Python 最流行的 HTTP 客户端库，比标准库 urllib 更简洁
# ===========================================================================
import requests


# ===========================================================================
# 第 29-57 行：get_weather 函数定义
# Python: def func_name(param: type) -> return_type:  声明函数，类型注解是可选的
# Java:   public String getWeather(String city) { ... }
# Python用缩进表示代码块（4个空格），Java用花括号 {}
# ===========================================================================
def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息。
    # Python 的 docstring（文档字符串），放在函数第一行，用三个引号括起来
    # 等价于 Java 的 /** ... */ Javadoc 注释
    """

    # --- 第 34 行：构造 API 请求 URL ---
    # Python 的 f-string（格式化字符串）：f"...{变量名}..."
    # 等价于 Java 的 String.format() 或 "..." + 变量
    # wttr.in 是一个免费天气 API，返回 JSON 格式数据
    url = f"https://wttr.in/{city}?format=j1"

    # --- 第 36-42 行：发送 HTTP 请求并解析 JSON ---
    # Python 的 try/except = Java 的 try/catch
    try:
        # requests.get(url) 发送 GET 请求，等价于 Java HttpClient.send()
        response = requests.get(url)

        # raise_for_status()：如果 HTTP 状态码不是 200，就抛异常
        # 等价于手动写: if (response.getStatusCode() != 200) throw new Exception()
        response.raise_for_status()

        # .json() 把 HTTP 响应体从 JSON 字符串解析成 Python 字典（dict）
        # Python dict = Java Map<String, Object>
        # 等价于 Java: new ObjectMapper().readValue(body, Map.class)
        data = response.json()

        # --- 第 45-47 行：从 JSON 中提取天气数据 ---
        # Python 用方括号 [] 访问字典和列表，类似 Java Map.get() 和 List.get()
        # [0] 取列表第一个元素，['key'] 取字典中 key 对应的值
        current_condition = data['current_condition'][0]   # 取当前天气的第一个记录
        weather_desc = current_condition['weatherDesc'][0]['value']  # 天气描述文字
        temp_c = current_condition['temp_C']               # 当前温度（摄氏度）

        # --- 第 50 行：返回格式化结果 ---
        # return 直接返回值，Python 不需要声明返回值类型在函数签名中
        return f"{city}当前天气：{weather_desc}，气温{temp_c}摄氏度"

    # --- 第 52-54 行：处理网络错误 ---
    # except 异常类型 as 变量名  等价于  Java: catch (RequestException e)
    # requests.exceptions.RequestException 是 requests 库的基异常类
    except requests.exceptions.RequestException as e:
        return f"错误：查询天气时遇到网络问题 - {e}"

    # --- 第 55-57 行：处理数据解析错误 ---
    # 可以同时捕获多个异常类型，用小括号括起来
    # KeyError = 字典中 key 不存在 (Java: NullPointerException/Map.get返回null)
    # IndexError = 列表索引越界 (Java: ArrayIndexOutOfBoundsException)
    except (KeyError, IndexError) as e:
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"


# ===========================================================================
# 第 60-61 行：导入更多模块
# import os：操作系统接口模块，用于读取环境变量（等价于 Java System.getenv()）
# from X import Y：从模块 X 中只导入 Y 这个类/函数（等价于 Java: import X.Y;）
# ===========================================================================
import os
from tavily import TavilyClient


# ===========================================================================
# 第 64-102 行：get_attraction 函数定义
# 功能：根据城市和天气，调用 Tavily 搜索 API 推荐旅游景点
# Tavily 是一个专为 AI Agent 设计的搜索 API
# ===========================================================================
def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """

    # --- 第 70-73 行：获取 API 密钥 ---
    # os.environ.get("KEY") 读取环境变量，等价于 Java: System.getenv("KEY")
    # .get() 方法如果 key 不存在返回 None（而不是抛异常 KeyError）
    # Python 的 None = Java 的 null
    api_key = os.environ.get("TAVILY_API_KEY")

    # Python 的 if not xxx: 检查是否为 None/空字符串/False/0/空集合
    # if not api_key 等价于 Java: if (apiKey == null || apiKey.isEmpty())
    if not api_key:
        return "错误：未配置TAVILY_API_KEY。"

    # --- 第 77 行：初始化 Tavily 客户端 ---
    # Python 创建对象不需要 new 关键字，直接 类名(参数...)
    # 等价于 Java: TavilyClient tavily = new TavilyClient(api_key);
    # 命名参数 api_key=api_key 让代码更清晰，也可以写成 tavily = TavilyClient(api_key)
    tavily = TavilyClient(api_key=api_key)

    # --- 第 80 行：构造搜索查询字符串 ---
    # 又是一个 f-string，花括号 {} 中可以放任意 Python 表达式
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        # --- 第 84 行：调用 Tavily 搜索 API ---
        # search_depth="basic"：搜索深度，basic 快但浅，advanced 深但慢
        # include_answer=True：让 Tavily 返回一个 AI 总结的答案
        response = tavily.search(query=query, search_depth="basic", include_answer=True)

        # --- 第 88-89 行：优先返回 AI 总结答案 ---
        # dict.get("key") 安全取字典值，key 不存在返回 None（不抛异常）
        # response.get("answer") 等价于 Java: response.containsKey("answer") ? response.get("answer") : null
        if response.get("answer"):
            return response["answer"]  # 有 AI 总结答案就直接返回

        # --- 第 92-95 行：格式化搜索结果列表 ---
        # 创建空列表 []，等价于 Java: List<String> formattedResults = new ArrayList<>();
        formatted_results = []

        # Python 的 for 循环：for 变量 in 可迭代对象:
        # 等价于 Java 的 for-each: for (Result result : response.getResults())
        # response.get("results", [])：取 "results" 键，不存在时返回默认值空列表 []
        for result in response.get("results", []):
            # list.append(item) 向列表末尾添加元素
            # 等价于 Java: formattedResults.add("- " + result.getTitle() + ": " + result.getContent());
            formatted_results.append(f"- {result['title']}: {result['content']}")

        # --- 第 96-97 行：无结果处理 ---
        # if not list 检查列表是否为空，空列表在 Python 中被视为 False
        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"

        # --- 第 99 行：拼接结果返回 ---
        # "\n".join(list)：用换行符将列表中的所有字符串拼接成一个字符串
        # 等价于 Java: String.join("\n", formattedResults);
        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    # --- 第 101-102 行：通用异常处理 ---
    # Exception 是所有异常的基类，捕获所有可能的错误
    except Exception as e:
        return f"错误：执行Tavily搜索时出现问题 - {e}"


# ===========================================================================
# 第 106-109 行：工具注册表（Tool Registry）
# Python 的 {} 创建字典（dict），等价于 Java 的 Map<String, Function>
# 关键区别：Python 中函数是一等公民，可以直接作为值存入字典
# Java 中需要 Lambda 表达式或 Method Reference 才能做到类似效果
# ===========================================================================
available_tools = {
    "get_weather": get_weather,        # 直接把函数对象存入字典，不需要 new
    "get_attraction": get_attraction,  # Python 万物皆对象，函数也是对象
}

# ===========================================================================
# 第 111 行：导入 OpenAI 官方 Python SDK
# openai.OpenAI 是官方提供的客户端类，用于调用 OpenAI 兼容的 API
# ===========================================================================
from openai import OpenAI


# ===========================================================================
# 第 114-141 行：OpenAICompatibleClient 类
# Python 的 class 定义，等价于 Java 的类定义
# ===========================================================================
class OpenAICompatibleClient:
    """
    一个用于调用任何兼容OpenAI接口的LLM服务的客户端。
    """

    # --- 第 119-121 行：构造函数（__init__ 方法）---
    # Python 的 __init__ = Java 的构造方法 Constructor
    # self = Java 的 this，但 Python 必须显式写在方法参数第一个位置
    # Python 没有方法重载（overload），一个类只能有一个 __init__
    def __init__(self, model: str, api_key: str, base_url: str):
        # self.model 和 self.client 是实例变量（instance variable）
        # Python 不需要先在类体顶部声明成员变量，直接在 __init__ 里赋值即可
        # 即 Python 是动态添加属性，Java 是静态声明字段
        self.model = model
        # 创建 OpenAI 客户端实例，传入 API 密钥和自定义的 API 地址（base_url）
        # base_url 可以是任何兼容 OpenAI 协议的地址，比如国内的 DeepSeek、通义千问等
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    # --- 第 123-141 行：generate 方法 ---
    # Python 的所有实例方法第一个参数必须是 self（等价于 Java 的 this）
    # Python 没有访问修饰符（public/private/protected），全靠约定：_name 表示"请勿外部使用"
    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用LLM API来生成回应。"""
        print("正在调用大语言模型...")  # print() 等价于 Java: System.out.println()
        try:
            # --- 第 127-130 行：构造消息列表 ---
            # Python 的 list 用方括号 []，等价于 Java 的 ArrayList
            # 列表元素是字典 dict（等价于 Java Map），用花括号 {}，键值对用冒号 :
            # 'role': 'system' 表示这是系统提示词（设定 AI 的行为）
            # 'role': 'user'   表示这是用户输入
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]

            # --- 第 131-135 行：调用 LLM API ---
            # 点号链式调用，每个点访问一个属性或调用一个方法
            # self.client.chat.completions.create(...) 等价于 Java 的 builder 模式
            # model=self.model：使用构造函数中保存的模型 ID
            # messages=messages：传入上面构造的消息列表
            # stream=False：不使用流式输出（等完整结果再返回）
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )

            # --- 第 136 行：提取 AI 回复文本 ---
            # response.choices 是返回的候选回复列表
            # [0] 取第一个（通常只有一个）
            # .message.content 取消息的文本内容
            answer = response.choices[0].message.content

            print("大语言模型响应成功。")
            return answer  # 返回 AI 生成的文本

        # --- 第 139-141 行：异常处理 ---
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误：调用语言模型服务时出错。"


# ===========================================================================
# 第 144-145 行：导入正则表达式模块和配置文件
# import re：Python 的正则表达式模块（等价于 Java: java.util.regex）
# from config import ...：从同目录下的 config.py 文件导入三个配置变量
#   这种 import 方式只导入指定名称，不会污染命名空间
# ===========================================================================
import re
from config import OPENAI_BASE_URL, OPENAI_MODEL, OPENAI_KEY


# ===========================================================================
# 第 147-151 行：配置部分
# Python 不需要声明变量类型，解释器自动推断（动态类型）
# 这与 Java 的强类型不同：Java 必须先声明类型 String API_KEY = ...;
# ===========================================================================

# 将 config 中导入的变量赋值给本地常量，便于后续使用
# Python 约定：全大写变量名表示"常量"（虽然技术上仍可修改，这是约定而非强制）
API_KEY = OPENAI_KEY        # API 密钥，用于认证
BASE_URL = OPENAI_BASE_URL  # API 服务地址（可以是任何兼容 OpenAI 协议的地址）
MODEL_ID = OPENAI_MODEL     # 模型 ID，比如 "gpt-4", "deepseek-chat" 等

# 设置环境变量 TAVILY_API_KEY
# os.environ 是一个字典，直接赋值即可设置环境变量
# 等价于 Java: System.setProperty() 或在终端 export TAVILY_API_KEY=xxx
# 注意：这是临时的，只在当前进程生效，程序退出后失效
os.environ['TAVILY_API_KEY'] = "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"

# --- 第 153-157 行：创建 LLM 客户端实例 ---
# 调用上面定义的 OpenAICompatibleClient 类，传入三个参数
# Python 创建对象：类名(参数1, 参数2, ...) —— 不需要 new 关键字！
# 等价于 Java: var llm = new OpenAICompatibleClient(MODEL_ID, API_KEY, BASE_URL);
llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)


# ===========================================================================
# 第 160-163 行：初始化用户提示和历史记录
# ===========================================================================

# 用户的问题/请求，这里是一个硬编码的示例请求
user_prompt = "你好，请帮我查询一下今天贵州的天气，然后根据天气推荐一个合适的旅游景点。"

# prompt_history 是一个列表，存储整个对话过程（包括用户请求、模型输出、工具返回）
# 这是 Agent 的"记忆"——每次循环都把完整历史发给 LLM，让 LLM 知道之前发生了什么
# 等价于 Java: List<String> promptHistory = new ArrayList<>();
prompt_history = [f"用户请求: {user_prompt}"]

# print() 打印到终端，end="..." 指定打印后的结束字符，默认是换行 \n
# "=" * 40：Python 中字符串乘以整数表示重复，"=" * 40 = 40 个等号
# 等价于 Java: "=".repeat(40)
print(f"用户输入: {user_prompt}\n" + "=" * 40)


# ===========================================================================
# 第 166-211 行：Agent 主循环（Agent Loop）
# 这是整个 Agent 的核心：反复执行"思考→行动→观察"的循环
# 相当于 Java Agent 框架中的 while (iterations < maxIterations) { ... }
# ===========================================================================

# range(5) 生成整数序列 0,1,2,3,4（左闭右开，不包含 5）
# 等价于 Java: for (int i = 0; i < 5; i++)
# 最大循环 5 次，防止 LLM 无限循环（安全保护机制）
for i in range(5):
    # --- 第 167 行：打印当前循环次数 ---
    # i + 1 因为 i 从 0 开始，显示时从 1 开始更直观
    print(f"--- 循环 {i + 1} ---\n")

    # =========================================================================
    # 步骤 3.1：构建 Prompt（第 169-170 行）
    # =========================================================================
    # "\n".join(prompt_history)：用换行符拼接历史记录列表中的所有字符串
    # 这样 LLM 就能看到整个对话历史，包括之前的 Thought/Action/Observation
    full_prompt = "\n".join(prompt_history)

    # =========================================================================
    # 步骤 3.2：调用 LLM 生成 Thought 和 Action（第 173-182 行）
    # =========================================================================
    # 调用上面封装好的 generate 方法，传入完整提示词和系统提示词
    llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)

    # --- 第 175-180 行：截断多余的 Thought-Action 对 ---
    # re.search(pattern, string, flags)：在字符串中搜索正则表达式匹配
    # 等价于 Java: Pattern.compile(pattern, flags).matcher(string).find()
    #
    # 正则表达式解释（逐段）：
    # (Thought:.*?Action:.*?)  - 捕获组：匹配第一对完整的 Thought-Action
    #   Thought:   - 字面匹配 "Thought:"
    #   .*?        - 非贪婪匹配任意字符（包括换行）
    #   Action:    - 字面匹配 "Action:"
    #   .*?        - 非贪婪匹配任意字符
    # (?=...)     - 正向前瞻断言：后面跟着...但不消费它
    #   \n\s*      - 换行加可选空白
    #   (?:...)    - 非捕获组：匹配 Thought: 或 Action: 或 Observation:
    #   |          - 或
    #   \Z         - 字符串末尾
    # re.DOTALL    - 让 . 也能匹配换行符 \n
    #
    # 目的：LLM 有时会一次输出多对 Thought-Action，我们只取第一对
    match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)

    # if match: 检查正则是否匹配到了内容
    # Python: re.search 匹配成功返回 Match 对象，失败返回 None
    # Java: Matcher.find() 返回 boolean，.group() 取匹配内容
    if match:
        # match.group(1) 取第一个捕获组的内容（即第一对完整的 Thought-Action）
        # .strip() 去除字符串两端的空白字符（等价于 Java: String.trim()）
        truncated = match.group(1).strip()

        # 如果截断后的内容和原始内容不一样，说明确实有多余内容，需要替换
        if truncated != llm_output.strip():
            llm_output = truncated
            print("已截断多余的 Thought-Action 对")

    # 打印模型输出，并追加到历史记录
    print(f"模型输出:\n{llm_output}\n")
    prompt_history.append(llm_output)  # 把 LLM 的 Thought+Action 加入历史

    # =========================================================================
    # 步骤 3.3：解析 Action 并执行工具调用（第 185-206 行）
    # =========================================================================

    # --- 第 185-191 行：从 LLM 输出中解析 Action ---
    # re.search 返回匹配对象或 None
    action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)

    # 如果没有找到 Action，返回错误 Observation，进入下一轮循环
    if not action_match:
        observation = "错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
        observation_str = f"Observation: {observation}"  # 格式化成 Observation 格式
        print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)  # 错误也加入历史，让 LLM 知道并修正
        continue  # 跳过本次循环剩余代码，开始下一轮循环（等价于 Java 的 continue）

    # .group(1) 取正则第一个捕获组，即 Action: 后面的所有内容
    # .strip() 去掉首尾空白
    action_str = action_match.group(1).strip()

    # --- 第 194-197 行：检查是否为 Finish（任务结束）---
    # .startswith("Finish")：字符串方法，判断是否以 "Finish" 开头
    # 等价于 Java: actionStr.startsWith("Finish")
    if action_str.startswith("Finish"):
        # re.match() 从字符串开头匹配，等价于 Java: Pattern.compile("...").matcher(str).matches()
        # 正则 Finish\[(.*)\]：匹配 Finish[...] ，捕获方括号内的内容
        # .group(1) 取出方括号内的最终答案文本
        final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
        print(f"任务完成，最终答案: {final_answer}")
        break  # 退出 for 循环（等价于 Java 的 break）

    # --- 第 199-201 行：解析工具名称和参数 ---
    # re.search(r"(\w+)\(", action_str)：匹配函数名（字母数字下划线+左括号）
    # 例如 action_str = 'get_weather(city="贵州")'，则 group(1) = 'get_weather'
    tool_name = re.search(r"(\w+)\(", action_str).group(1)

    # re.search(r"\((.*)\)", action_str)：匹配括号内的参数
    # 例如 action_str = 'get_weather(city="贵州")'，则 group(1) = 'city="贵州"'
    args_str = re.search(r"\((.*)\)", action_str).group(1)

    # re.findall(r'(\w+)="([^"]*)"', args_str)：查找所有 key="value" 格式的参数
    # 返回列表，如 [('city', '贵州')]
    # dict(...) 将 [(key1,value1), (key2,value2)] 转换成字典 {'key1':'value1', 'key2':'value2'}
    # 这个字典可直接用于 **kwargs 解包传给工具函数
    kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

    # --- 第 203-206 行：执行工具函数 ---
    # if tool_name in available_tools：检查工具是否在注册表中
    # Python 的 in 运算符：检查字典中是否有这个 key
    # 等价于 Java: availableTools.containsKey(toolName)
    if tool_name in available_tools:
        # 从字典取出函数，然后调用它
        # **kwargs 是 Python 的字典解包（unpacking）语法
        # **kwargs 将 {'city': '贵州'} 展开为 city="贵州"，作为关键字参数传给函数
        # 等价于: available_tools["get_weather"](city="贵州")
        observation = available_tools[tool_name](**kwargs)
    else:
        # 工具不存在则返回错误信息
        observation = f"错误：未定义的工具 '{tool_name}'"

    # =========================================================================
    # 步骤 3.4：记录观察结果（第 209-211 行）
    # =========================================================================
    # 将工具的返回值格式化成 "Observation: xxx" 的形式
    # LLM 下一轮会看到这个 Observation，基于它决定下一步做什么
    observation_str = f"Observation: {observation}"
    print(f"{observation_str}\n" + "=" * 40)
    prompt_history.append(observation_str)  # 追加到对话历史

# ===========================================================================
# 程序执行流程总结（读完代码后再看这里）：
#
# 整个 Agent 循环就像这样一个对话流水线：
#
# 循环 1:
#   模型输出: Thought: 我需要查天气 → Action: get_weather(city="贵州")
#   工具返回: Observation: 贵州当前天气：晴，气温25摄氏度
#
# 循环 2:
#   模型输出: Thought: 天气是晴天，开始搜索景点 → Action: get_attraction(city="贵州", weather="晴")
#   工具返回: Observation: 根据搜索...推荐黄果树瀑布...
#
# 循环 3:
#   模型输出: Thought: 信息足够了 → Action: Finish[贵州今天晴天25度，推荐去黄果树瀑布]
#   触发 break，循环结束
#
# Python vs Java 核心差异速查表：
# ┌─────────────────────┬──────────────────────────┬──────────────────────────────────┐
# │ 概念                 │ Python                    │ Java                              │
# ├─────────────────────┼──────────────────────────┼──────────────────────────────────┤
# │ 变量声明             │ x = 10                    │ int x = 10;                      │
# │ 代码块               │ 缩进（4空格）              │ 花括号 {}                         │
# │ 创建对象             │ ClassName(args)           │ new ClassName(args)               │
# │ 构造函数             │ __init__(self)            │ ClassName()                       │
# │ this 引用            │ self（显式参数）           │ this（隐式可用）                   │
# │ 字典/Map             │ {"a": 1}                  │ Map.of("a", 1)                    │
# │ 列表/List            │ [1, 2, 3]                 │ List.of(1, 2, 3)                  │
# │ 列表追加             │ list.append(x)            │ list.add(x)                       │
# │ for-each 循环        │ for x in list:            │ for (var x : list) {}             │
# │ 字符串格式化         │ f"hello {name}"           │ "hello " + name                   │
# │ 函数是一等公民       │ map["fn"] = my_func       │ map.put("fn", this::myFunc)       │
# │ 异常处理             │ try/except                │ try/catch                         │
# │ null/空              │ None                      │ null                              │
# │ 打印                 │ print("hello")            │ System.out.println("hello");      │
# │ 类型注解（可选）      │ x: int = 10               │ int x = 10;（强制）                │
# │ 多行字符串           │ """..."""                 │ """..."""（Java 15+）              │
# │ 字符串重复           │ "=" * 40                  │ "=".repeat(40)                    │
# │ 拼接列表为字符串      │ "\n".join(list)           │ String.join("\n", list)           │
# │ Python: True/False/None 首字母大写               │ Java: true/false/null 全小写       │
# └─────────────────────┴──────────────────────────┴──────────────────────────────────┘
# ===========================================================================
