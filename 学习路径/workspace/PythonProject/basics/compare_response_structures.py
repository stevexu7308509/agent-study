# 对比 OpenAI SDK vs Anthropic SDK 的 response 结构
import sys
from config import create_openai_client, create_anthropic_client, OPENAI_MODEL, ANTHROPIC_MODEL

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MESSAGE = "你好，用一句话介绍你自己。"

# ============================================
# 1. OpenAI SDK 结构
# ============================================
openai_client = create_openai_client()
r = openai_client.chat.completions.create(
    model=OPENAI_MODEL,
    max_tokens=200,
    messages=[{"role": "user", "content": MESSAGE}],
)

print("=" * 60)
print("OpenAI SDK response 结构")
print("=" * 60)
print(f"type: {type(r).__name__}")                        # ChatCompletion
print(f"model: {r.model}")
print(f"id: {r.id}")
print()
print("【取文本】 r.choices[0].message.content")
print(f"  → {r.choices[0].message.content}")
print()
print("【取 token】")
print(f"  r.usage.prompt_tokens     = {r.usage.prompt_tokens}")
print(f"  r.usage.completion_tokens  = {r.usage.completion_tokens}")
print(f"  r.usage.total_tokens       = {r.usage.total_tokens}")
print()
print("【停止原因】 r.choices[0].finish_reason")
print(f"  → {r.choices[0].finish_reason}")

# ============================================
# 2. Anthropic SDK 结构
# ============================================
anthropic_client = create_anthropic_client()
msg = anthropic_client.messages.create(
    model=ANTHROPIC_MODEL,
    max_tokens=200,
    messages=[{"role": "user", "content": MESSAGE}],
)

print()
print("=" * 60)
print("Anthropic SDK response 结构")
print("=" * 60)
print(f"type: {type(msg).__name__}")                       # Message
print(f"model: {msg.model}")
print(f"id: {msg.id}")
print()
print(f"【content 是列表，每个元素有 type】")
for i, block in enumerate(msg.content):
    print(f"  msg.content[{i}].type = {block.type}")
    if block.type == "text":
        print(f"    .text = {block.text}")
    elif block.type == "thinking":
        print(f"    .thinking = {block.thinking[:80]}...")

print()
print("【取文本】 msg.content[N].text")
text_blocks = [b for b in msg.content if b.type == "text"]
print(f"  → {text_blocks[0].text}")
print()
print("【取 token】")
print(f"  msg.usage.input_tokens  = {msg.usage.input_tokens}")
print(f"  msg.usage.output_tokens = {msg.usage.output_tokens}")
print()
print("【停止原因】 msg.stop_reason")
print(f"  → {msg.stop_reason}")
