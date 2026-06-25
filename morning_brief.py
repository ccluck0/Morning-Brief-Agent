import feedparser
import requests
import os
from datetime import datetime

# ── 1. RSS源 ──────────────────────────────────────────
SOURCES = [
    ("BBC",     "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Reuters", "https://feeds.reuters.com/reuters/topNews"),
    ("Guardian","https://www.theguardian.com/international/rss"),
]

def fetch_headlines():
    items = []
    for name, url in SOURCES:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                title = entry.get("title", "").strip()
                link  = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip()[:200]
                items.append(f"[{name}] {title}\n{summary}\n{link}")
        except Exception as e:
            print(f"Error fetching {name}: {e}")
    return items

# ── 2. 调用LLM做英文摘要 ─────────────────────────────
def build_prompt(items):
    today = datetime.now().strftime("%b %d, %Y")
    raw = "\n---\n".join(items)
    return f"""You are a global affairs editor. Today is {today}.

Below are raw RSS headlines from BBC, Reuters, The Guardian.

{raw}

Your job:
1. Pick the 8 most globally significant DISTINCT stories
2. Group under: 🌍 WORLD / 💼 BUSINESS / 🔬 TECH & SCIENCE
3. For each: write ONE sentence in English (≤25 words), append source link
4. Output format:

📰 Morning Brief — {today}
────────────────────────
🌍 WORLD
• [sentence] — [Source](link)

Output ONLY the brief, no extra talk.
"""

def call_llm(prompt):
    # 使用 DeepSeek API
    api_key = os.environ["DEEPSEEK_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role":"user","content":prompt}],
        "temperature": 0.3,
    }
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        json=payload, headers=headers, timeout=60
    )
    response = requests.post(url, headers=headers, json=payload)
    print("状态码:", response.status_code)  
    print("返回内容:", response.text)  
    return r.json()["choices"][0]["message"]["content"]

# ── 3. 推送（飞书群机器人webhook）────────────────────
def push_to_feishu(text):
    wh = os.environ["FEISHU_WEBHOOK"]
    requests.post(wh, json={"msg_type":"t
    ext","content":{"text":text}})

# ── RUN ───────────────────────────────────────────────
if __name__ == "__main__":
    items = fetch_headlines()
    prompt = build_prompt(items)
    brief = call_llm(prompt)
    print(brief)
    push_to_feishu(brief)
