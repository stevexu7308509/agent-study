# 需要：pip install openai
import sys, time

from openai import OpenAI
from config import create_openai_client, OPENAI_MODEL

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

client = create_openai_client()

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
tps = out_tok_avg / avg_latency if avg_latency > 0 else 0

print(f"model: {OPENAI_MODEL}")
print(f"5 次 latency (sec): min={min(latencies):.2f} max={max(latencies):.2f} mean={avg_latency:.2f}")
print(f"avg output: {out_tok_avg} tokens、约 {tps:.1f} tokens/sec")

# === 自我验证 ===
assert avg_latency > 0, "latency 应 > 0"
assert out_tok_avg > 0, "output token 应 > 0"
print(f"\n✅ 练习 3 通过 — 测试 API 延迟")
