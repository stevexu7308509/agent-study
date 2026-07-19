# 需要：pip install anthropic
import sys, json

from config import ANTHROPIC_MODEL, create_anthropic_client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

client = create_anthropic_client()

SYSTEM_PROMPTS = {
    "严肃律师": "你是严谨的合约律师。回答要精准、引用法条编号、避免任何主观形容词。",
    "幼儿园老师": "你是温柔的幼儿园老师、要对 5 岁小孩说话。用比喻、口语、少于 80 字。",
    "JSON 机器": "你只回 JSON。schema: {\"answer\": string, \"confidence\": float}",
}
USER_MSG = "请帮我解释什么是租赁合约。"

outputs = {}
for label, system in SYSTEM_PROMPTS.items():
    # Anthropic SDK: system 作为独立参数传入
    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,   # 给足够的 token，思考+文本都够用
        system=system,
        messages=[
            {"role": "user", "content": USER_MSG},
        ],
    )
    # 打印 msg 完整结构（只打印第一个角色，避免刷屏）
    if label == "严肃律师":
        print(f"===== msg 结构（{label}）=====")
        print(msg.model_dump_json(indent=2))

    # content 是列表：[ThinkingBlock, TextBlock, ...] 或只有 [TextBlock]
    # 只取 TextBlock；如果没文本块则取 thinking 内容
    text_blocks = [block for block in msg.content if block.type == "text"]
    if text_blocks:
        outputs[label] = text_blocks[0].text
    else:
        # 如果只有 thinking 没有 text（token 不够时），取 thinking 内容
        outputs[label] = msg.content[0].thinking
    print(f"\n--- [{label}] ---")
    print(outputs[label])

# 验证 JSON 输出
json_output = outputs["JSON 机器"]
assert "{" in json_output and "}" in json_output
print(f"\n✅ 练习 1 通过（Anthropic SDK）")
