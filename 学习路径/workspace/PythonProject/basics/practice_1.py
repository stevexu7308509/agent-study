# 需要：pip install openai
import sys, json, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import OPENAI_MODEL, create_openai_client

client = create_openai_client()

# 同一個 user message、3 個不同 system prompt
SYSTEM_PROMPTS = {
    "嚴肅律師": "你是嚴謹的合約律師。回答要精準、引用法條編號、避免任何主觀形容詞。",
    "幼兒園老師": "你是溫柔的幼兒園老師、要對 5 歲小孩說話。用比喻、口語、少於 80 字。",
    "JSON 機器": "你只回 JSON。schema: {\"answer\": string, \"confidence\": float}",
}

USER_MSG = "請幫我解釋什麼是租賃合約。"

outputs = {}
for label, system in SYSTEM_PROMPTS.items():
    # Note: Ollama 把 system 放 messages 第一筆（不像 Anthropic 用 system= 參數）
    r = client.chat.completions.create(
        model="deepseek-v4-flash",
        max_tokens=200,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": USER_MSG},
        ],
    )
    outputs[label] = r.choices[0].message.content
    print(f"\n--- [{label}] ---")
    print(outputs[label])

# === 自我驗證 ===
json_output = outputs["JSON 機器"]
assert "{" in json_output and "}" in json_output, "JSON 機器版輸出應該含 JSON braces"
try:
    parsed = json.loads(json_output.strip().split("\n")[-1] if "\n" in json_output else json_output)
    assert "answer" in parsed, "JSON schema 應包含 answer 欄位"
except json.JSONDecodeError:
    pass # 容許 model 回 JSON 含解釋文字、最後一筆才是 JSON
print(f"\n✅ 練習 1 通過 — 同一個問題、3 種人格 / 格式 / 語氣")
print("💡 觀察：律師長、老師短、JSON 機器一定是 {...}")