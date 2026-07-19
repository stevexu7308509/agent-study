# 07 - API 成本与延迟测试

> **学习日期**: 2026-07  
> **对应代码**: `basics/practice_3.py`, `basics/practice_3_anthropic.py`

---

## 1. API 延迟测试

### 1.1 测试代码

```python
import time

latencies = []
for _ in range(5):
    t0 = time.time()
    r = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": "你好！自我介绍一下。"}],
    )
    latencies.append(time.time() - t0)

avg_latency = sum(latencies) / len(latencies)
out_tok_avg = r.usage.completion_tokens
tps = out_tok_avg / avg_latency  # tokens per second

print(f"5 次延迟: min={min(latencies):.2f}s max={max(latencies):.2f}s mean={avg_latency:.2f}s")
print(f"平均输出: {out_tok_avg} tokens, 约 {tps:.1f} tokens/sec")
```

### 1.2 为什么要测延迟？

| 指标 | 意义 |
|------|------|
| 平均延迟 | 用户体验感知的等待时间 |
| 最小/最大延迟 | 了解稳定性，最大延迟影响超时设置 |
| tokens/sec | 吞吐量，影响批量任务的总耗时 |
| 首次 token 时间 (TTFT) | 流式场景下用户看到第一个字的时间 |

### 1.3 多次测试的原因

网络波动、服务端负载都会影响延迟。单次测试不具备代表性，至少测 3-5 次取平均。

---

## 2. Token 成本计算

### 2.1 Anthropic 2026 Q2 公开计价

```python
PRICING = {
    "claude-haiku-4-5":   {"input": 1.00, "output":  5.00},
    "claude-sonnet-4-6":  {"input": 3.00, "output": 15.00},
    "claude-opus-4-8":    {"input": 5.00, "output": 25.00},
    "claude-fable-5":     {"input": 10.00, "output": 50.00},
}
# 单位：美元 / 1M token
```

### 2.2 单次调用成本计算

```python
msg = client.messages.create(model=ANTHROPIC_MODEL, max_tokens=200,
                             messages=[{"role": "user", "content": "你好！"}])

in_tok = msg.usage.input_tokens
out_tok = msg.usage.output_tokens
rates = PRICING[ANTHROPIC_MODEL]

# 单次调用成本 = (输入token × 输入单价 + 输出token × 输出单价) / 1,000,000
cost_one = (in_tok * rates["input"] + out_tok * rates["output"]) / 1_000_000
print(f"单次调用: input={in_tok} output={out_tok} → ${cost_one:.6f}")
```

### 2.3 批量调用成本预估

```python
# 估算 1000 次调用的成本
for name, r in PRICING.items():
    cost_1000 = (in_tok * r["input"] + out_tok * r["output"]) / 1_000_000 * 1000
    print(f"  {name:<22} ${cost_1000:.4f}")
```

**大致对比**（单次简单对话）:

| 模型 | 1000 次调用成本 |
|------|----------------|
| Haiku 4.5 | ~$0.25 |
| Sonnet 4.6 | ~$0.76 |
| Opus 4.8 | ~$1.27 |
| Fable 5 | ~$2.50 |

---

## 3. 成本优化策略

### 3.1 模型选择

```
简单任务（分类、提取） → Haiku（便宜）
中等任务（总结、翻译） → Sonnet（平衡）
复杂任务（推理、Agent）→ Opus/Fable（能力强）
```

### 3.2 减少输入 Token

- 精简 system prompt
- 只传递必要的对话历史，不要传全部
- 使用 `max_tokens` 限制输出长度
- 对长文档使用 RAG 而非全量塞入

### 3.3 缓存利用

Anthropic 支持 prompt caching，重复的 system prompt 和长文档可以缓存，减少输入成本。

---

## 4. 测试策略

### 4.1 延迟监控维度

```python
# 应该持续监控的指标
- P50 延迟（中位数）
- P95 延迟（尾部延迟）
- P99 延迟（极端情况）
- 错误率
- Token 消耗速率
```

### 4.2 压力测试

```python
import concurrent.futures

def stress_test(n_requests=100, n_workers=10):
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(single_call) for _ in range(n_requests)]
        results = [f.result() for f in futures]
    # 分析成功率和延迟分布
```

---

## 复习要点

1. 延迟测试要多次执行取平均，排除单次波动
2. Token 成本 = 输入价格 + 输出价格，输出通常贵 5 倍
3. 选择模型是从"便宜→贵"的能力梯度：Haiku < Sonnet < Opus < Fable
4. 减少输入 token 是控制成本的最有效手段
5. 生产环境要持续监控延迟分布（P50/P95/P99）
