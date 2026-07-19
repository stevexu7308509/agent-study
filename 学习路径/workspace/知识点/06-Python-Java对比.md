# 06 - Python vs Java 对比（Agent 开发向）

> **学习日期**: 2026-07  
> **对应代码**: `basics/datawhale/FirstAgentTest.py`（超详细对比注释）

---

## 1. 语法速查表

| 概念 | Python | Java |
|------|--------|------|
| 变量声明 | `x = 10` | `int x = 10;` |
| 代码块 | 缩进（4空格） | 花括号 `{}` |
| 创建对象 | `ClassName(args)` | `new ClassName(args)` |
| 构造函数 | `__init__(self)` | `ClassName()` |
| this 引用 | `self`（显式参数） | `this`（隐式可用） |
| 字典/Map | `{"a": 1}` | `Map.of("a", 1)` |
| 列表/List | `[1, 2, 3]` | `List.of(1, 2, 3)` |
| 列表追加 | `list.append(x)` | `list.add(x)` |
| for-each | `for x in list:` | `for (var x : list) {}` |
| 字符串格式化 | `f"hello {name}"` | `"hello " + name` 或 `String.format()` |
| 异常处理 | `try/except` | `try/catch` |
| null | `None` | `null` |
| 打印 | `print("hello")` | `System.out.println("hello");` |
| 类型注解 | `x: int = 10`（可选） | `int x = 10;`（强制） |
| 多行字符串 | `"""..."""` | `"""..."""`（Java 15+）或 `"..." +` |
| 字符串重复 | `"=" * 40` | `"=".repeat(40)` |
| 拼接列表 | `"\n".join(list)` | `String.join("\n", list)` |
| 布尔值 | `True` / `False` | `true` / `false` |
| 空值 | `None` | `null` |

---

## 2. Python Agent 开发的优势

### 2.1 函数是一等公民

```python
# Python: 函数可以直接存入字典
available_tools = {
    "get_weather": get_weather,
    "search": search,
}

# Java: 需要 Function 接口 + Lambda
Map<String, Function<String, String>> tools = Map.of(
    "get_weather", city -> getWeather(city),
    "search", query -> search(query)
);
```

### 2.2 动态类型 + 字典解包

```python
# Python: **kwargs 字典解包，灵活传参
kwargs = {"city": "贵州", "weather": "晴"}
result = available_tools[tool_name](**kwargs)

# Java: 需要反射或者 switch-case 逐个处理
if (toolName.equals("get_attraction")) {
    result = getAttraction(args.get("city"), args.get("weather"));
}
```

### 2.3 丰富的 AI/ML 生态

Python 生态在 AI Agent 开发中的核心库：
- `openai` - OpenAI SDK
- `anthropic` - Anthropic SDK
- `langchain` - Agent 框架
- `tiktoken` - Token 计数
- `requests` - HTTP 客户端

---

## 3. 从 Java 视角看 Python 的关键差异

### 3.1 没有访问修饰符

```python
# Python: 全靠约定
class MyClass:
    def public_method(self):    # 公开方法
        pass
    
    def _internal_method(self): # "请勿外部使用"（约定，实际仍可调用）
        pass
```

Java 有 `public`/`private`/`protected`，Python 靠 `_` 前缀约定。

### 3.2 动态添加属性

```python
# Python: 运行时可以给实例加新属性
obj = MyClass()
obj.new_field = "hello"  # 这在 Java 中是不可能的
```

### 3.3 import 可以写在任何位置

```python
# Python: import 写在中间也行（虽然惯例是在顶部）
def func():
    import requests  # 局部导入
    return requests.get("...")
```

Java 的 `import` 必须在文件顶部。

### 3.4 字典访问的两种方式

```python
data = {"key": "value"}

# 方式1: 直接取，key 不存在抛 KeyError
value = data["key"]

# 方式2: 安全取，key 不存在返回 None（或默认值）
value = data.get("key")           # None
value = data.get("key", "默认值")  # "默认值"
```

Java Map: `map.get("key")` 不存在返回 `null`，类似 Python 的 `.get()`。

### 3.5 异常处理语法

```python
# Python
try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    return f"网络错误: {e}"
except (KeyError, IndexError) as e:
    return f"解析错误: {e}"

# Java 等价
try {
    HttpResponse<String> response = client.send(request, BodyHandlers.ofString());
    ObjectMapper mapper = new ObjectMapper();
    Map<String, Object> data = mapper.readValue(response.body(), Map.class);
} catch (IOException e) {
    return "网络错误: " + e.getMessage();
} catch (JsonProcessingException e) {
    return "解析错误: " + e.getMessage();
}
```

**关键差异**:
- Python: `except`（一个 t）
- Java: `catch`（两个 t）
- Python 可以一次捕获多个异常类型：`except (A, B) as e:`

---

## 4. Agent 开发中常见的 Python 惯用写法

### 4.1 环境变量读取

```python
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件
api_key = os.getenv("API_KEY")        # 读取，不存在返回 None
api_key = os.environ.get("API_KEY")   # 同上
```

### 4.2 列表推导式

```python
# 传统写法
results = []
for res in response["organic_results"][:3]:
    results.append(f"[{i+1}] {res['title']}")

# 列表推导式（Python 惯用写法）
results = [f"[{i+1}] {res['title']}" 
           for i, res in enumerate(response["organic_results"][:3])]
```

### 4.3 f-string 字符串格式化

```python
city = "北京"
weather = "晴"
# 三种写法，f-string 最简洁
msg1 = city + "当前天气：" + weather          # Java 风格
msg2 = "{}当前天气：{}".format(city, weather)  # format 方法
msg3 = f"{city}当前天气：{weather}"            # f-string ✅ 推荐
```

---

## 复习要点

1. Python 不需要 `new` 关键字、不需要声明类型、用缩进代替花括号
2. Python 函数是一等公民，这对 Agent 工具注册非常方便
3. `**kwargs` 字典解包是 Agent 动态调用工具的关键机制
4. Python 用 `_` 前缀约定"私有"，而非强制的访问修饰符
5. 列表推导式和 f-string 是 Python 最常用的语法糖
