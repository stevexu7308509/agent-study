# 需要：pip install anthropic
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import anthropic
from config import create_anthropic_client, ANTHROPIC_MODEL

# Anthropic 2026 Q2 公开计价（每 1M token、USD）— 运行前对照 https://www.anthropic.com/pricing
PRICING = {
    "claude-haiku-4-5":   {"input": 1.00, "output":  5.00},
    "claude-sonnet-4-6":  {"input": 3.00, "output": 15.00},
    "claude-opus-4-8":    {"input": 5.00, "output": 25.00},  # Opus 4.8（2026 年 5 月、Dynamic Workflows）—— 维持 5/25 同价
    "claude-fable-5":     {"input": 10.00, "output": 50.00},  # Fable 5（Mythos-class、2026-06-09 GA；2026-06-12 起暂停、无法使用）约 Opus 4.8 的 2 倍
}
# 创建 Anthropic 客户端
client = create_anthropic_client()

msg = client.messages.create(model=ANTHROPIC_MODEL, max_tokens=200,
                             messages=[{"role": "user", "content": "你好！自我介绍一下。"}])
in_tok, out_tok = msg.usage.input_tokens, msg.usage.output_tokens
rates = PRICING[ANTHROPIC_MODEL]
cost_one = (in_tok * rates["input"] + out_tok * rates["output"]) / 1_000_000

print(f"model: {ANTHROPIC_MODEL}")
print(f"single: input={in_tok} output={out_tok} → ${cost_one:.6f}")
print(f"1000 calls cost across model tiers:")
for name, r in PRICING.items():
    c = (in_tok * r["input"] + out_tok * r["output"]) / 1_000_000 * 1000
    print(f"  {name:<22} ${c:.4f}")

assert cost_one > 0, "Cloud LLM 一定有成本"
print(f"\n✅ 练习 3 通过（Anthropic）— 1000 次 haiku ≈ $0.25、sonnet 4.6 ≈ $0.76、opus 4.8 ≈ $1.27")