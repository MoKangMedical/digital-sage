"""
智者 Digital Sage API
与全球最聪明的 100 个大脑对话。
"""

from __future__ import annotations

import json
import os
import sys
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.thought_profiles import (  # noqa: E402
    CELEBRITY_PROFILES,
    build_chat_prompt,
    get_all_celebrities,
    get_profile,
)


app = FastAPI(
    title="智者 Digital Sage API",
    description="与全球最聪明的 100 个大脑对话",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MIMO_API_BASE = os.getenv("MIMO_API_BASE", "https://api.xiaomimimo.com/v1")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")


class ChatRequest(BaseModel):
    celebrity_id: str
    message: str
    topic: Optional[str] = "general"


class ChatResponse(BaseModel):
    celebrity_id: str
    celebrity_name: str
    response: str
    source: str
    disclaimer: str = "这是 AI 基于公开资料生成的模拟回答，仅供体验与参考。"


class ExpertAdviceRequest(BaseModel):
    celebrity_id: str
    situation: str
    category: str


def _build_fallback_response(profile: dict, message: str, topic: str) -> str:
    name = profile["name"]
    focus_tags = profile.get("focus_tags", [])
    tag1 = focus_tags[0] if focus_tags else "底层逻辑"
    tag2 = focus_tags[1] if len(focus_tags) > 1 else "关键约束"
    tag3 = focus_tags[2] if len(focus_tags) > 2 else "长期结果"
    framework = profile["judgment_framework"]["decision_framework"]
    positions = list(profile.get("positions", {}).values())[:2]

    topic_openers = {
        "investment": f"如果按{name}的方式看投资，我会先盯住 {tag1}，而不是先被市场情绪带走。",
        "career": f"如果按{name}的方式看职业选择，先别急着选答案，先把 {tag1} 和 {tag2} 想清楚。",
        "general": f"如果按{name}的方式理解这个问题，我会先回到 {tag1} 的底层逻辑，再决定怎么行动。",
    }
    opener = topic_openers.get(topic, topic_openers["general"])

    action_lines = [
        f"第一，先问自己：{framework['step1']}",
        f"第二，再检查：{framework['step2']}",
        f"第三，把资源集中到最能放大 {tag3} 的一两个动作上，不要同时做太多事。",
    ]
    if positions:
        action_lines.append(f"我会特别提醒你：{positions[0]}")
    if len(positions) > 1:
        action_lines.append(f"另外别忽略：{positions[1]}")

    close = (
        f"所以，面对“{message}”这类问题，我不会先追求看起来厉害的答案，"
        f"而是先把真正决定结果的变量找出来，然后围绕它持续迭代。"
    )

    return "\n\n".join([opener, "\n".join(action_lines), close])


async def _call_mimo(profile: dict, prompt: str, fallback_message: str, topic: str) -> tuple[str, str]:
    if not MIMO_API_KEY:
        return _build_fallback_response(profile, fallback_message, topic), "fallback"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{MIMO_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {MIMO_API_KEY}"},
                json={
                    "model": "mimo-v2-pro",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"你是{profile['name']}，{profile['title']}。"
                                "请保持该人物公开形象中的思考方式与表达风格，"
                                "但不要声称自己真的就是本人。"
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800,
                },
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"], "mimo"
    except Exception:
        return _build_fallback_response(profile, fallback_message, topic), "fallback"


def _build_shell() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>智者 Digital Sage</title>
  <style>
    :root {
      --bg: #f3f5f8;
      --ink: #111827;
      --muted: #5f6b7a;
      --line: rgba(17, 24, 39, 0.08);
      --card: rgba(255, 255, 255, 0.72);
      --accent: #0f172a;
      --accent-soft: #dbe7ff;
      --shadow: 0 24px 60px rgba(17, 24, 39, 0.08);
      --radius: 28px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "SF Pro Display", "PingFang SC", "Helvetica Neue", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(123, 176, 255, 0.32), transparent 32%),
        radial-gradient(circle at top right, rgba(255, 210, 150, 0.28), transparent 28%),
        linear-gradient(180deg, #f7f9fc 0%, #eef2f7 48%, #f6f8fb 100%);
      min-height: 100vh;
    }
    .page {
      width: min(1440px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
    }
    .nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 24px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .brand-mark {
      width: 46px;
      height: 46px;
      border-radius: 16px;
      background: linear-gradient(135deg, #101828 0%, #2e4057 100%);
      color: white;
      display: grid;
      place-items: center;
      font-weight: 700;
      box-shadow: var(--shadow);
    }
    .brand h1 {
      margin: 0;
      font-size: 1rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }
    .brand p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 0.94rem;
    }
    .status {
      display: flex;
      gap: 12px;
      color: var(--muted);
      font-size: 0.94rem;
    }
    .hero {
      border-radius: 36px;
      overflow: hidden;
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.58)),
        linear-gradient(125deg, #ffffff 0%, #e8eef8 55%, #d6e3ff 100%);
      box-shadow: var(--shadow);
      border: 1px solid rgba(255, 255, 255, 0.6);
      padding: 42px;
      position: relative;
      margin-bottom: 24px;
    }
    .hero::after {
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(circle at 80% 20%, rgba(15, 23, 42, 0.12), transparent 24%),
        radial-gradient(circle at 70% 75%, rgba(96, 165, 250, 0.12), transparent 18%);
      pointer-events: none;
    }
    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(320px, 420px);
      gap: 28px;
      align-items: end;
      position: relative;
      z-index: 1;
    }
    .hero-copy h2 {
      margin: 0;
      font-size: clamp(3rem, 7vw, 6.4rem);
      line-height: 0.95;
      letter-spacing: -0.05em;
    }
    .hero-copy h2 span {
      display: block;
      color: rgba(17, 24, 39, 0.54);
      font-size: clamp(1rem, 2vw, 1.2rem);
      letter-spacing: 0.34em;
      text-transform: uppercase;
      margin-bottom: 12px;
    }
    .hero-copy p {
      max-width: 700px;
      font-size: 1.08rem;
      line-height: 1.8;
      color: #425063;
      margin: 18px 0 0;
    }
    .hero-stats {
      display: grid;
      gap: 14px;
      padding: 22px;
      backdrop-filter: blur(18px);
      background: rgba(255, 255, 255, 0.58);
      border-radius: 28px;
      border: 1px solid rgba(255, 255, 255, 0.62);
    }
    .stat-label {
      font-size: 0.78rem;
      color: var(--muted);
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .stat-value {
      font-size: 2.3rem;
      line-height: 1;
      letter-spacing: -0.05em;
    }
    .toolbar {
      display: grid;
      grid-template-columns: minmax(220px, 340px) 1fr;
      gap: 16px;
      margin-bottom: 20px;
    }
    .search,
    .filters,
    .panel,
    .chat-shell {
      background: var(--card);
      backdrop-filter: blur(18px);
      border: 1px solid rgba(255, 255, 255, 0.6);
      box-shadow: var(--shadow);
    }
    .search {
      border-radius: 22px;
      padding: 14px 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .search input {
      width: 100%;
      border: none;
      background: transparent;
      outline: none;
      font-size: 1rem;
      color: var(--ink);
    }
    .filters {
      border-radius: 22px;
      padding: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .chip {
      border: none;
      border-radius: 999px;
      padding: 10px 14px;
      background: rgba(15, 23, 42, 0.05);
      color: var(--muted);
      cursor: pointer;
      transition: all 160ms ease;
      font-size: 0.94rem;
    }
    .chip.active,
    .chip:hover {
      background: var(--accent);
      color: white;
      transform: translateY(-1px);
    }
    .main {
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 20px;
    }
    .panel {
      border-radius: 28px;
      padding: 18px;
    }
    .panel h3 {
      margin: 0 0 14px;
      font-size: 0.9rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .expert-list {
      display: grid;
      gap: 10px;
      max-height: 900px;
      overflow: auto;
      padding-right: 4px;
    }
    .expert-card {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.5);
      border-radius: 22px;
      padding: 16px;
      cursor: pointer;
      transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
    }
    .expert-card:hover,
    .expert-card.active {
      transform: translateY(-1px);
      border-color: rgba(15, 23, 42, 0.18);
      background: white;
    }
    .expert-card strong {
      display: block;
      font-size: 1rem;
      margin-bottom: 4px;
    }
    .expert-card small {
      color: var(--muted);
      display: block;
      margin-bottom: 10px;
    }
    .tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .tag {
      font-size: 0.8rem;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.06);
      color: #334155;
    }
    .workspace {
      display: grid;
      gap: 18px;
    }
    .hero-panel {
      padding: 28px;
      border-radius: 30px;
      background: linear-gradient(180deg, rgba(255,255,255,0.85), rgba(255,255,255,0.58));
      border: 1px solid rgba(255,255,255,0.68);
      box-shadow: var(--shadow);
    }
    .eyebrow {
      font-size: 0.8rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .hero-panel h4 {
      margin: 12px 0 8px;
      font-size: clamp(2rem, 4vw, 3.4rem);
      letter-spacing: -0.05em;
    }
    .hero-panel p {
      margin: 0;
      color: #465467;
      line-height: 1.8;
    }
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }
    .detail {
      padding: 18px;
      border-radius: 24px;
      background: rgba(255, 255, 255, 0.62);
      border: 1px solid rgba(255,255,255,0.65);
      box-shadow: var(--shadow);
    }
    .detail h5 {
      margin: 0 0 10px;
      font-size: 0.8rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
    }
    .detail ul {
      margin: 0;
      padding-left: 18px;
      color: #243142;
      line-height: 1.7;
    }
    .chat-shell {
      border-radius: 30px;
      overflow: hidden;
    }
    .chat-head {
      padding: 18px 22px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .chat-log {
      padding: 22px;
      min-height: 320px;
      max-height: 520px;
      overflow: auto;
      display: grid;
      gap: 14px;
      background: rgba(255,255,255,0.48);
    }
    .bubble {
      max-width: 78%;
      padding: 16px 18px;
      border-radius: 22px;
      line-height: 1.75;
      white-space: pre-wrap;
    }
    .bubble.user {
      justify-self: end;
      background: linear-gradient(135deg, #0f172a, #1e293b);
      color: white;
    }
    .bubble.ai {
      justify-self: start;
      background: rgba(255,255,255,0.86);
      color: #17212d;
      border: 1px solid rgba(15, 23, 42, 0.08);
    }
    .chat-form {
      display: grid;
      grid-template-columns: 1fr 140px;
      gap: 12px;
      padding: 18px 22px 22px;
      border-top: 1px solid var(--line);
      background: rgba(255,255,255,0.75);
    }
    textarea {
      resize: vertical;
      min-height: 90px;
      border: 1px solid rgba(15, 23, 42, 0.08);
      border-radius: 20px;
      padding: 14px 16px;
      outline: none;
      font: inherit;
      background: rgba(255,255,255,0.92);
    }
    .submit {
      border: none;
      border-radius: 20px;
      background: linear-gradient(135deg, #111827, #1d4ed8);
      color: white;
      font-size: 1rem;
      cursor: pointer;
      box-shadow: var(--shadow);
    }
    .tiny {
      color: var(--muted);
      font-size: 0.88rem;
    }
    @media (max-width: 1120px) {
      .hero-grid,
      .main,
      .detail-grid,
      .toolbar,
      .chat-form {
        grid-template-columns: 1fr;
      }
      .chat-form {
        grid-template-columns: 1fr;
      }
      .bubble { max-width: 100%; }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="nav">
      <div class="brand">
        <div class="brand-mark">智</div>
        <div>
          <h1>Digital Sage</h1>
          <p>与全球最聪明的 100 个大脑对话</p>
        </div>
      </div>
      <div class="status">
        <span id="loadedCount">载入中</span>
        <span>FastAPI + Vercel Ready</span>
      </div>
    </div>

    <section class="hero">
      <div class="hero-grid">
        <div class="hero-copy">
          <h2><span>Thought Interface</span>智者</h2>
          <p>
            把商业、科学、医学、设计与思想领域的顶尖人物，整理成一个可对话的认知界面。
            这里不是随机角色扮演，而是围绕公开立场、长期方法论和表达风格构建的思想索引。
          </p>
        </div>
        <div class="hero-stats">
          <div>
            <div class="stat-label">人物总数</div>
            <div class="stat-value" id="heroCount">100</div>
          </div>
          <div>
            <div class="stat-label">覆盖领域</div>
            <div class="tiny">商业 / 科技 / 科学 / 医学 / 思想 / 文化 / 治理 / 设计</div>
          </div>
          <div>
            <div class="stat-label">体验方式</div>
            <div class="tiny">搜索人物、查看方法论、直接发起对话</div>
          </div>
        </div>
      </div>
    </section>

    <section class="toolbar">
      <div class="search">
        <span>搜索</span>
        <input id="searchInput" placeholder="输入中文名、英文名或领域关键词">
      </div>
      <div class="filters" id="filters"></div>
    </section>

    <section class="main">
      <aside class="panel">
        <h3>Expert Directory</h3>
        <div class="expert-list" id="expertList"></div>
      </aside>

      <div class="workspace">
        <section class="hero-panel">
          <div class="eyebrow" id="detailCategory">人物档案</div>
          <h4 id="detailName">载入中</h4>
          <p id="detailTitle">请稍候，正在加载 100 位智者档案。</p>
        </section>

        <section class="detail-grid">
          <article class="detail">
            <h5>核心价值</h5>
            <ul id="coreValues"></ul>
          </article>
          <article class="detail">
            <h5>判断框架</h5>
            <ul id="framework"></ul>
          </article>
          <article class="detail">
            <h5>重点立场</h5>
            <ul id="positions"></ul>
          </article>
        </section>

        <section class="chat-shell">
          <div class="chat-head">
            <div>
              <strong id="chatName">正在连接</strong>
              <div class="tiny">基于公开资料的 AI 模拟回答</div>
            </div>
            <div class="tiny" id="chatSource">准备中</div>
          </div>
          <div class="chat-log" id="chatLog"></div>
          <form class="chat-form" id="chatForm">
            <textarea id="messageInput" placeholder="例如：如果我要从 0 到 1 做一个全球化产品，你会先看哪三个变量？"></textarea>
            <button class="submit" type="submit">开始对话</button>
          </form>
        </section>
      </div>
    </section>
  </div>

  <script>
    const categoryLabels = {
      all: "全部",
      business: "商业",
      technology: "科技",
      science: "科学",
      medical: "医学",
      philosophy: "思想",
      culture: "文化",
      policy: "治理",
      design: "设计"
    };

    const state = {
      celebrities: [],
      activeId: null,
      activeCategory: "all",
      search: ""
    };

    const els = {
      heroCount: document.getElementById("heroCount"),
      loadedCount: document.getElementById("loadedCount"),
      filters: document.getElementById("filters"),
      expertList: document.getElementById("expertList"),
      searchInput: document.getElementById("searchInput"),
      detailCategory: document.getElementById("detailCategory"),
      detailName: document.getElementById("detailName"),
      detailTitle: document.getElementById("detailTitle"),
      coreValues: document.getElementById("coreValues"),
      framework: document.getElementById("framework"),
      positions: document.getElementById("positions"),
      chatName: document.getElementById("chatName"),
      chatSource: document.getElementById("chatSource"),
      chatLog: document.getElementById("chatLog"),
      chatForm: document.getElementById("chatForm"),
      messageInput: document.getElementById("messageInput")
    };

    function renderFilters() {
      els.filters.innerHTML = "";
      Object.entries(categoryLabels).forEach(([key, label]) => {
        const button = document.createElement("button");
        button.className = "chip" + (state.activeCategory === key ? " active" : "");
        button.textContent = label;
        button.addEventListener("click", () => {
          state.activeCategory = key;
          renderFilters();
          renderExpertList();
        });
        els.filters.appendChild(button);
      });
    }

    function filteredCelebrities() {
      const term = state.search.trim().toLowerCase();
      return state.celebrities.filter((item) => {
        const categoryOk = state.activeCategory === "all" || item.category === state.activeCategory;
        const searchOk =
          !term ||
          item.name.toLowerCase().includes(term) ||
          item.name_en.toLowerCase().includes(term) ||
          item.title.toLowerCase().includes(term) ||
          item.focus_tags.join(" ").toLowerCase().includes(term);
        return categoryOk && searchOk;
      });
    }

    function renderExpertList() {
      const items = filteredCelebrities();
      els.expertList.innerHTML = "";
      if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "tiny";
        empty.textContent = "没有匹配结果。";
        els.expertList.appendChild(empty);
        return;
      }

      if (!items.some((item) => item.id === state.activeId)) {
        state.activeId = items[0].id;
        selectCelebrity(state.activeId);
      }

      items.forEach((item) => {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "expert-card" + (item.id === state.activeId ? " active" : "");
        card.innerHTML = `
          <strong>${item.name}</strong>
          <small>${item.name_en} · ${item.title}</small>
          <div class="tags">${item.focus_tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}</div>
        `;
        card.addEventListener("click", () => selectCelebrity(item.id));
        els.expertList.appendChild(card);
      });
    }

    function addBubble(role, text) {
      const bubble = document.createElement("div");
      bubble.className = `bubble ${role}`;
      bubble.textContent = text;
      els.chatLog.appendChild(bubble);
      els.chatLog.scrollTop = els.chatLog.scrollHeight;
    }

    async function selectCelebrity(id) {
      state.activeId = id;
      renderExpertList();
      const res = await fetch(`/api/celebrities/${id}`);
      const profile = await res.json();

      els.detailCategory.textContent = profile.category_label;
      els.detailName.textContent = profile.name;
      els.detailTitle.textContent = `${profile.title} · ${profile.name_en}`;
      els.chatName.textContent = `与 ${profile.name} 对话`;
      els.chatSource.textContent = `方法论焦点：${profile.focus_tags.slice(0, 3).join(" / ")}`;

      const renderList = (target, values) => {
        target.innerHTML = "";
        values.forEach((value) => {
          const li = document.createElement("li");
          li.textContent = value;
          target.appendChild(li);
        });
      };

      renderList(els.coreValues, profile.core_values);
      renderList(els.framework, Object.values(profile.judgment_framework.decision_framework));
      renderList(els.positions, Object.values(profile.positions));

      els.chatLog.innerHTML = "";
      addBubble("ai", `已进入 ${profile.name} 的思考界面。你可以直接提问，我会优先沿着 ${profile.focus_tags.slice(0, 3).join("、")} 这条线索回答。`);
    }

    async function bootstrap() {
      const res = await fetch("/api/celebrities");
      state.celebrities = await res.json();
      els.heroCount.textContent = String(state.celebrities.length);
      els.loadedCount.textContent = `${state.celebrities.length} Profiles Loaded`;
      renderFilters();
      renderExpertList();
      if (state.celebrities.length) {
        await selectCelebrity(state.celebrities[0].id);
      }
    }

    els.searchInput.addEventListener("input", (event) => {
      state.search = event.target.value;
      renderExpertList();
    });

    els.chatForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const message = els.messageInput.value.trim();
      if (!message || !state.activeId) return;
      addBubble("user", message);
      els.messageInput.value = "";
      els.chatSource.textContent = "正在生成回答…";

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          celebrity_id: state.activeId,
          message,
          topic: "general"
        })
      });
      const data = await res.json();
      addBubble("ai", data.response + "\\n\\n" + data.disclaimer);
      els.chatSource.textContent = data.source === "mimo" ? "Source: MIMO API" : "Source: Local fallback persona";
    });

    bootstrap();
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return _build_shell()


@app.get("/health")
async def health() -> dict:
    categories = {}
    for profile in CELEBRITY_PROFILES.values():
        categories[profile["category"]] = categories.get(profile["category"], 0) + 1
    return {
        "status": "healthy",
        "service": "智者 Digital Sage",
        "version": "2.0.0",
        "celebrities_loaded": len(CELEBRITY_PROFILES),
        "categories": categories,
    }


@app.get("/api/celebrities")
async def list_celebrities() -> list[dict]:
    return get_all_celebrities()


@app.get("/api/celebrities/{celeb_id}")
async def get_celebrity(celeb_id: str) -> dict:
    profile = get_profile(celeb_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    return profile


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_celebrity(req: ChatRequest) -> ChatResponse:
    profile = get_profile(req.celebrity_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")

    prompt = build_chat_prompt(req.celebrity_id, req.message, req.topic or "general")
    response, source = await _call_mimo(
        profile,
        prompt,
        req.message,
        req.topic or "general",
    )
    return ChatResponse(
        celebrity_id=req.celebrity_id,
        celebrity_name=profile["name"],
        response=response,
        source=source,
    )


@app.post("/api/expert-advice")
async def get_expert_advice(req: ExpertAdviceRequest) -> dict:
    profile = get_profile(req.celebrity_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")

    prompt = (
        f"用户遇到的情况：{req.situation}\n\n"
        f"请以 {profile['name']} 的方式，围绕 {', '.join(profile['focus_tags'][:3])} 进行分析，"
        "给出分步骤的建议、主要风险和一个最重要的下一步行动。"
    )
    response, source = await _call_mimo(
        profile,
        prompt,
        req.situation,
        "career",
    )
    return {
        "celebrity_id": req.celebrity_id,
        "celebrity_name": profile["name"],
        "category": req.category,
        "advice": response,
        "framework_used": profile["judgment_framework"],
        "source": source,
        "disclaimer": "这是 AI 基于公开资料生成的模拟建议，不构成投资、医疗、法律等专业意见。",
    }


@app.get("/api/positions/{celeb_id}")
async def get_positions(celeb_id: str) -> dict:
    profile = get_profile(celeb_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    return {
        "celebrity": profile["name"],
        "positions": profile["positions"],
        "core_values": profile["core_values"],
    }


@app.get("/api/speaking-style/{celeb_id}")
async def get_speaking_style(celeb_id: str) -> dict:
    profile = get_profile(celeb_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    return {
        "celebrity": profile["name"],
        "speaking_style": profile["speaking_style"],
    }


if __name__ == "__main__":
    import uvicorn

    print("智者 Digital Sage 启动中...")
    uvicorn.run(app, host="0.0.0.0", port=8103)
