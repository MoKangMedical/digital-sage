"""
智者 Digital Sage API
与全球最聪明的 100 个大脑对话。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = Path(__file__).resolve().parents[1]


def _load_local_env() -> None:
    for env_name in (".env.local", ".env"):
        env_path = BASE_DIR / env_name
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_local_env()

from ai_engine.cartoon_avatars import avatar_url, render_cartoon_avatar_svg  # noqa: E402
from ai_engine.demo_story import DEMO_SCENES  # noqa: E402
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
MEDIA_DIR = BASE_DIR / "media"
COURSES_PROXY_BASE = os.getenv(
    "COURSES_PROXY_BASE",
    "https://mokangmedical.github.io/digital-sage-courses",
).rstrip("/")

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


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


async def _proxy_courses_request(path: str, request: Request) -> Response:
    normalized_path = path.lstrip("/")
    target_url = f"{COURSES_PROXY_BASE}/{normalized_path}" if normalized_path else f"{COURSES_PROXY_BASE}/"

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        upstream = await client.request(request.method, target_url)

    passthrough_headers = {}
    for header_name in (
        "content-type",
        "cache-control",
        "etag",
        "last-modified",
        "accept-ranges",
        "content-length",
    ):
        header_value = upstream.headers.get(header_name)
        if header_value:
            passthrough_headers[header_name] = header_value

    content = b"" if request.method == "HEAD" else upstream.content
    return Response(content=content, status_code=upstream.status_code, headers=passthrough_headers)


@app.api_route("/courses", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/courses/{course_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def proxy_courses(request: Request, course_path: str = "") -> Response:
    return await _proxy_courses_request(course_path, request)


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
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not content:
                return _build_fallback_response(profile, fallback_message, topic), "fallback"
            return content, "mimo"
    except Exception:
        return _build_fallback_response(profile, fallback_message, topic), "fallback"


def _build_shell() -> str:
    shell = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Digital Sage | 与全球最聪明的 100 个大脑对话</title>
  <meta name="description" content="Digital Sage 把 100 位商业、科技、科学、医学与思想领域的顶尖人物整理成可对话的认知界面。在线看品牌样片、切换人物、发起真实问题对话。">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="theme-color" content="#0f172a">
  <meta name="apple-mobile-web-app-title" content="Digital Sage">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='18' fill='%230f172a'/%3E%3Ctext x='50%25' y='55%25' text-anchor='middle' font-family='Arial,sans-serif' font-size='24' fill='white'%3EDS%3C/text%3E%3C/svg%3E">
  <link rel="canonical" href="https://www.digitalsage.cloud/">
  <link rel="preload" as="image" href="/media/demo/digital-sage-film-poster.jpg">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Digital Sage">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:title" content="Digital Sage | 与全球最聪明的 100 个大脑对话">
  <meta property="og:description" content="把 100 位顶尖人物整理成可对话的认知界面。先看成片 Demo，再直接发问。">
  <meta property="og:url" content="https://www.digitalsage.cloud/">
  <meta property="og:image" content="https://www.digitalsage.cloud/media/demo/digital-sage-film-poster.jpg">
  <meta property="og:image:alt" content="Digital Sage 首页品牌样片封面">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Digital Sage | 与全球最聪明的 100 个大脑对话">
  <meta name="twitter:description" content="在线切换 100 位智者视角，快速把复杂问题看清一层。">
  <meta name="twitter:image" content="https://www.digitalsage.cloud/media/demo/digital-sage-film-poster.jpg">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "name": "Digital Sage",
        "url": "https://www.digitalsage.cloud/",
        "description": "与全球最聪明的 100 个大脑对话，把复杂问题看清一层。",
        "inLanguage": "zh-CN"
      },
      {
        "@type": "SoftwareApplication",
        "name": "Digital Sage",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "url": "https://www.digitalsage.cloud/",
        "description": "把 100 位商业、科技、科学、医学与思想领域的顶尖人物整理成可对话的认知界面。",
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "USD"
        }
      },
      {
        "@type": "FAQPage",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "这是不是简单的名人角色扮演？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "不是。Digital Sage 优先围绕人物的公开资料、长期立场、判断框架和表达风格来组织回答，用于帮助用户快速比较不同思路。"
            }
          },
          {
            "@type": "Question",
            "name": "我第一次打开应该怎么体验？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "建议先看首页成片 Demo，再点击典型问题入口，一键切到对应智者并把问题填入对话框，立刻感受产品价值。"
            }
          },
          {
            "@type": "Question",
            "name": "它适合哪些高价值场景？",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "适合创业决策、产品方向、战略判断、研究框架梳理和高压情境下的多视角思考。"
            }
          }
        ]
      }
    ]
  }
  </script>
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
    .hero-proof {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }
    .proof-pill {
      display: inline-flex;
      align-items: center;
      min-height: 38px;
      padding: 0 14px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid rgba(17, 24, 39, 0.08);
      color: #243142;
      font-size: 0.9rem;
      box-shadow: 0 10px 30px rgba(17, 24, 39, 0.05);
    }
    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 24px;
    }
    .hero-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 48px;
      padding: 0 18px;
      border-radius: 999px;
      text-decoration: none;
      font-size: 0.96rem;
      transition: transform 180ms ease, background 180ms ease, color 180ms ease;
    }
    .hero-link.primary {
      background: linear-gradient(135deg, #111827, #1d4ed8);
      color: white;
      box-shadow: var(--shadow);
    }
    .hero-link.secondary {
      background: rgba(255, 255, 255, 0.76);
      color: var(--ink);
      border: 1px solid rgba(17, 24, 39, 0.08);
    }
    .hero-link:hover {
      transform: translateY(-1px);
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
    .film-section {
      display: grid;
      grid-template-columns: minmax(280px, 0.72fr) minmax(0, 1.28fr);
      gap: 26px;
      margin: 0 0 28px;
      align-items: center;
    }
    .quickstart {
      display: grid;
      grid-template-columns: minmax(280px, 0.74fr) minmax(0, 1.26fr);
      gap: 22px;
      margin: 0 0 28px;
      align-items: stretch;
    }
    .quickstart-copy {
      display: grid;
      align-content: start;
      gap: 14px;
      padding: 6px 4px 0;
    }
    .quickstart-copy h3 {
      margin: 0;
      font-size: clamp(2rem, 3vw, 3.2rem);
      line-height: 1.02;
      letter-spacing: -0.05em;
    }
    .quickstart-copy p {
      margin: 0;
      color: #465467;
      line-height: 1.8;
      font-size: 1rem;
    }
    .quickstart-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }
    .prompt-card {
      text-align: left;
      border: 1px solid rgba(255, 255, 255, 0.6);
      border-radius: 28px;
      padding: 20px;
      background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(255,255,255,0.62));
      box-shadow: var(--shadow);
      cursor: pointer;
      transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
    }
    .prompt-card:hover {
      transform: translateY(-2px);
      border-color: rgba(29, 78, 216, 0.18);
      box-shadow: 0 26px 60px rgba(17, 24, 39, 0.1);
    }
    .prompt-card small {
      display: block;
      margin-bottom: 10px;
      color: var(--muted);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      font-size: 0.76rem;
    }
    .prompt-card strong {
      display: block;
      margin-bottom: 10px;
      font-size: 1.12rem;
      line-height: 1.35;
      color: var(--ink);
    }
    .prompt-card span {
      display: block;
      color: #465467;
      line-height: 1.75;
      font-size: 0.94rem;
    }
    .film-copy {
      display: grid;
      gap: 14px;
      align-content: start;
      padding: 2px 4px 0;
    }
    .film-copy h3 {
      margin: 0;
      font-size: clamp(2rem, 3vw, 3.4rem);
      line-height: 1.02;
      letter-spacing: -0.05em;
    }
    .film-copy p {
      margin: 0;
      color: #465467;
      line-height: 1.8;
      font-size: 1rem;
    }
    .film-meta {
      display: grid;
      gap: 12px;
      margin-top: 8px;
    }
    .film-stat {
      padding: 14px 0;
      border-top: 1px solid rgba(17, 24, 39, 0.08);
    }
    .film-stat strong {
      display: block;
      margin-bottom: 6px;
      font-size: 0.94rem;
    }
    .film-stat span {
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.7;
    }
    .film-shell {
      border-radius: 34px;
      overflow: hidden;
      background: linear-gradient(135deg, rgba(255,255,255,0.86), rgba(255,255,255,0.58));
      border: 1px solid rgba(255,255,255,0.66);
      box-shadow: var(--shadow);
      padding: 18px;
    }
    .film-screen {
      position: relative;
      overflow: hidden;
      border-radius: 28px;
      background: #08111e;
      aspect-ratio: 16 / 9;
      box-shadow: 0 24px 60px rgba(8, 17, 30, 0.22);
    }
    .film-screen video {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: cover;
      background: #08111e;
    }
    .film-badge {
      position: absolute;
      top: 18px;
      left: 18px;
      z-index: 2;
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 0 12px;
      border-radius: 999px;
      background: rgba(10, 15, 25, 0.58);
      color: white;
      font-size: 0.82rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255,255,255,0.14);
    }
    .film-caption {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      padding: 16px 8px 6px;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .film-caption strong {
      display: block;
      color: var(--ink);
      margin-bottom: 4px;
      font-size: 0.98rem;
    }
    .toolbar {
      display: grid;
      grid-template-columns: minmax(220px, 340px) 1fr;
      gap: 16px;
      margin-bottom: 20px;
    }
    .cinema {
      display: grid;
      grid-template-columns: minmax(280px, 0.76fr) minmax(0, 1.24fr);
      gap: 26px;
      margin: 0 0 28px;
      align-items: stretch;
    }
    .cinema-copy {
      padding: 8px 4px 0;
      display: grid;
      align-content: start;
      gap: 16px;
    }
    .cinema-copy h3 {
      margin: 0;
      font-size: clamp(2rem, 3vw, 3.3rem);
      line-height: 1.02;
      letter-spacing: -0.05em;
    }
    .cinema-copy p {
      margin: 0;
      color: #465467;
      line-height: 1.8;
      font-size: 1rem;
    }
    .cinema-points {
      display: grid;
      gap: 12px;
      margin-top: 8px;
    }
    .cinema-point {
      padding: 14px 0;
      border-top: 1px solid rgba(17, 24, 39, 0.08);
    }
    .cinema-point strong {
      display: block;
      margin-bottom: 6px;
      font-size: 0.95rem;
    }
    .cinema-point span {
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.7;
    }
    .cinema-player {
      position: relative;
      overflow: hidden;
      min-height: 620px;
      border-radius: 36px;
      background:
        radial-gradient(circle at 15% 20%, rgba(255, 255, 255, 0.18), transparent 24%),
        linear-gradient(135deg, #07111d 0%, #0f1e34 52%, #111827 100%);
      color: white;
      box-shadow: 0 28px 90px rgba(7, 17, 29, 0.24);
      --demo-a: #07111d;
      --demo-b: #14253f;
      --demo-c: rgba(96, 165, 250, 0.34);
      --demo-d: rgba(251, 191, 36, 0.14);
      transition: background 400ms ease, transform 400ms ease;
      isolation: isolate;
    }
    .cinema-player::before,
    .cinema-player::after {
      content: "";
      position: absolute;
      inset: -15%;
      pointer-events: none;
      z-index: 0;
    }
    .cinema-player::before {
      background:
        radial-gradient(circle at 22% 25%, var(--demo-c), transparent 22%),
        radial-gradient(circle at 78% 74%, var(--demo-d), transparent 24%);
      filter: blur(34px);
      animation: drift 18s linear infinite;
      opacity: 0.85;
    }
    .cinema-player::after {
      background:
        repeating-linear-gradient(
          180deg,
          rgba(255, 255, 255, 0.055) 0,
          rgba(255, 255, 255, 0.055) 1px,
          transparent 1px,
          transparent 4px
        );
      mix-blend-mode: soft-light;
      opacity: 0.16;
    }
    .cinema-player[data-theme="nightfall"] {
      --demo-a: #06101d;
      --demo-b: #1a2a46;
      --demo-c: rgba(59, 130, 246, 0.32);
      --demo-d: rgba(148, 163, 184, 0.2);
    }
    .cinema-player[data-theme="constellation"] {
      --demo-a: #0a1024;
      --demo-b: #1a1c49;
      --demo-c: rgba(129, 140, 248, 0.32);
      --demo-d: rgba(56, 189, 248, 0.18);
    }
    .cinema-player[data-theme="signal"] {
      --demo-a: #09131f;
      --demo-b: #0f3850;
      --demo-c: rgba(34, 197, 94, 0.24);
      --demo-d: rgba(59, 130, 246, 0.18);
    }
    .cinema-player[data-theme="sunrise"] {
      --demo-a: #2c1930;
      --demo-b: #6d3f5a;
      --demo-c: rgba(244, 114, 182, 0.24);
      --demo-d: rgba(251, 191, 36, 0.18);
    }
    .cinema-player[data-theme="daybreak"] {
      --demo-a: #18273f;
      --demo-b: #325a72;
      --demo-c: rgba(125, 211, 252, 0.28);
      --demo-d: rgba(255, 255, 255, 0.18);
    }
    .player-top,
    .cinema-stage,
    .subtitle-bar,
    .scene-dots {
      position: relative;
      z-index: 1;
    }
    .player-top {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 20px 22px 12px;
    }
    .demo-toggle {
      border: 1px solid rgba(255, 255, 255, 0.14);
      background: rgba(255, 255, 255, 0.08);
      color: white;
      border-radius: 999px;
      min-height: 42px;
      padding: 0 16px;
      font: inherit;
      cursor: pointer;
      transition: background 180ms ease, transform 180ms ease;
    }
    .demo-toggle:hover {
      background: rgba(255, 255, 255, 0.14);
      transform: translateY(-1px);
    }
    .demo-progress {
      flex: 1;
      height: 6px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.12);
      overflow: hidden;
    }
    .demo-progress > span {
      display: block;
      height: 100%;
      width: 0;
      border-radius: inherit;
      background: linear-gradient(90deg, #f8fafc 0%, #93c5fd 60%, #fde68a 100%);
      box-shadow: 0 0 18px rgba(147, 197, 253, 0.65);
    }
    .demo-counter {
      min-width: 88px;
      text-align: right;
      color: rgba(255, 255, 255, 0.76);
      font-size: 0.92rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .cinema-stage {
      padding: 20px 22px 0;
    }
    .cinema-frame {
      display: grid;
      grid-template-columns: minmax(0, 1.02fr) minmax(320px, 0.98fr);
      gap: 18px;
      padding: 22px;
      border-radius: 28px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02)),
        linear-gradient(135deg, rgba(255, 255, 255, 0.09), rgba(255, 255, 255, 0.03));
      border: 1px solid rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(16px);
      min-height: 472px;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
      animation: sceneIn 560ms ease;
    }
    .scene-story {
      display: grid;
      align-content: end;
      gap: 16px;
      padding: 8px 4px 8px 0;
    }
    .scene-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: rgba(255, 255, 255, 0.72);
      font-size: 0.84rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .scene-pill {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .scene-story h4 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 3.8rem);
      line-height: 0.98;
      letter-spacing: -0.06em;
      max-width: 12ch;
    }
    .scene-body {
      margin: 0;
      max-width: 42ch;
      color: rgba(255, 255, 255, 0.8);
      line-height: 1.85;
      font-size: 1rem;
    }
    .scene-quote {
      max-width: 40ch;
      margin-top: 6px;
      padding-left: 18px;
      border-left: 2px solid rgba(255, 255, 255, 0.22);
      color: rgba(255, 255, 255, 0.92);
      line-height: 1.85;
      font-size: 1.02rem;
    }
    .scene-product {
      align-self: end;
    }
    .product-window {
      border-radius: 26px;
      background:
        linear-gradient(180deg, rgba(6, 12, 22, 0.94), rgba(13, 20, 34, 0.92));
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 14px;
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.24);
    }
    .window-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 2px 4px 14px;
    }
    .traffic {
      display: flex;
      gap: 6px;
    }
    .traffic span {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.24);
    }
    .traffic span:nth-child(1) { background: #fb7185; }
    .traffic span:nth-child(2) { background: #fbbf24; }
    .traffic span:nth-child(3) { background: #34d399; }
    .window-label {
      color: rgba(255, 255, 255, 0.56);
      font-size: 0.82rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }
    .expert-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 14px;
    }
    .expert-token {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      min-height: 48px;
      padding: 6px 14px 6px 6px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.1);
      color: rgba(255, 255, 255, 0.92);
      font-size: 0.92rem;
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }
    .expert-token img {
      width: 36px;
      height: 36px;
      border-radius: 14px;
      object-fit: cover;
      background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.44));
      border: 1px solid rgba(255, 255, 255, 0.14);
      flex: 0 0 auto;
    }
    .expert-token span {
      line-height: 1.15;
      white-space: nowrap;
    }
    .demo-dialog {
      display: grid;
      gap: 10px;
      margin-bottom: 12px;
    }
    .mini-bubble {
      padding: 14px 16px;
      border-radius: 20px;
      line-height: 1.7;
      font-size: 0.95rem;
    }
    .mini-bubble.user {
      justify-self: end;
      max-width: 86%;
      background: linear-gradient(135deg, #1d4ed8, #3b82f6);
    }
    .mini-bubble.ai {
      background: rgba(255, 255, 255, 0.08);
      color: rgba(255, 255, 255, 0.88);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .outcome-card {
      border-radius: 22px;
      padding: 16px;
      background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.05));
      border: 1px solid rgba(255,255,255,0.08);
    }
    .outcome-label {
      color: rgba(255, 255, 255, 0.56);
      font-size: 0.78rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 10px;
    }
    .outcome-text {
      font-size: 1.05rem;
      line-height: 1.75;
      color: rgba(255, 255, 255, 0.94);
    }
    .subtitle-bar {
      padding: 16px 22px 6px;
    }
    .subtitle-shell {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: rgba(255, 255, 255, 0.86);
    }
    .subtitle-shell strong {
      color: rgba(255, 255, 255, 0.48);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      font-size: 0.78rem;
      white-space: nowrap;
    }
    .subtitle-shell p {
      margin: 0;
      line-height: 1.7;
      font-size: 0.95rem;
    }
    .scene-dots {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      padding: 14px 22px 22px;
    }
    .scene-dot {
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(255, 255, 255, 0.06);
      color: rgba(255, 255, 255, 0.74);
      border-radius: 999px;
      min-height: 38px;
      padding: 0 12px;
      font: inherit;
      cursor: pointer;
      transition: transform 180ms ease, background 180ms ease, color 180ms ease;
    }
    .scene-dot.active,
    .scene-dot:hover {
      background: rgba(255, 255, 255, 0.14);
      color: white;
      transform: translateY(-1px);
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
      display: grid;
      grid-template-columns: 74px minmax(0, 1fr);
      gap: 14px;
      align-items: center;
    }
    .expert-card:hover,
    .expert-card.active {
      transform: translateY(-1px);
      border-color: rgba(15, 23, 42, 0.18);
      background: white;
    }
    .expert-avatar {
      width: 74px;
      height: 74px;
      border-radius: 24px;
      object-fit: cover;
      background: linear-gradient(180deg, #eef4ff, #ffffff);
      border: 1px solid rgba(15, 23, 42, 0.08);
      box-shadow: 0 14px 34px rgba(17, 24, 39, 0.08);
      overflow: hidden;
    }
    .expert-card-body {
      min-width: 0;
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
    .detail-hero-head {
      display: grid;
      grid-template-columns: 116px minmax(0, 1fr);
      gap: 20px;
      align-items: center;
    }
    .detail-avatar {
      width: 116px;
      height: 116px;
      border-radius: 34px;
      object-fit: cover;
      background: linear-gradient(180deg, #eef4ff, #ffffff);
      border: 1px solid rgba(15, 23, 42, 0.08);
      box-shadow: 0 20px 44px rgba(17, 24, 39, 0.1);
      overflow: hidden;
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
      gap: 16px;
    }
    .chat-title {
      display: flex;
      align-items: center;
      gap: 14px;
      min-width: 0;
    }
    .chat-avatar {
      width: 56px;
      height: 56px;
      border-radius: 18px;
      object-fit: cover;
      background: linear-gradient(180deg, #edf3ff, #ffffff);
      border: 1px solid rgba(15, 23, 42, 0.08);
      box-shadow: 0 14px 30px rgba(17, 24, 39, 0.08);
      flex: 0 0 auto;
      overflow: hidden;
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
    .faq-section {
      margin-top: 28px;
      padding: 30px;
      border-radius: 34px;
      background: linear-gradient(180deg, rgba(255,255,255,0.84), rgba(255,255,255,0.62));
      border: 1px solid rgba(255,255,255,0.68);
      box-shadow: var(--shadow);
    }
    .faq-section h3 {
      margin: 10px 0 0;
      font-size: clamp(2rem, 3vw, 3rem);
      line-height: 1.04;
      letter-spacing: -0.05em;
    }
    .faq-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-top: 20px;
    }
    .faq-item {
      padding: 20px;
      border-radius: 24px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid rgba(17, 24, 39, 0.08);
    }
    .faq-item h4 {
      margin: 0 0 10px;
      font-size: 1rem;
      line-height: 1.5;
    }
    .faq-item p {
      margin: 0;
      color: #465467;
      line-height: 1.8;
      font-size: 0.95rem;
    }
    @keyframes drift {
      0% { transform: translate3d(0, 0, 0) scale(1); }
      50% { transform: translate3d(4%, -3%, 0) scale(1.04); }
      100% { transform: translate3d(0, 0, 0) scale(1); }
    }
    @keyframes sceneIn {
      0% {
        opacity: 0;
        transform: translateY(14px) scale(0.985);
      }
      100% {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }
    @media (max-width: 1120px) {
      .film-section,
      .quickstart,
      .quickstart-grid,
      .cinema,
      .hero-grid,
      .main,
      .detail-grid,
      .faq-grid,
      .toolbar,
      .chat-form,
      .cinema-frame {
        grid-template-columns: 1fr;
      }
      .chat-form {
        grid-template-columns: 1fr;
      }
      .cinema-player {
        min-height: auto;
      }
      .detail-hero-head {
        grid-template-columns: 1fr;
      }
      .scene-story h4 {
        max-width: none;
      }
      .player-top {
        flex-wrap: wrap;
      }
      .expert-card {
        grid-template-columns: 1fr;
      }
      .chat-head,
      .chat-title {
        align-items: flex-start;
      }
      .demo-counter {
        min-width: 0;
        text-align: left;
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
        <span>Production Live · MIMO</span>
      </div>
    </div>

    <section class="hero">
      <div class="hero-grid">
        <div class="hero-copy">
          <h2><span>Thought Interface</span>智者</h2>
          <p>
            把巴菲特、乔布斯、图灵、钟南山、孔子等 100 位人物的公开立场、长期方法论和表达风格，
            整理成一个可对话的判断界面。你不是来玩随机角色扮演，而是来借世界级思路把复杂问题看清一层。
          </p>
          <div class="hero-proof">
            <span class="proof-pill">100 位长期主义智者</span>
            <span class="proof-pill">MIMO 实时生成回答</span>
            <span class="proof-pill">首页自带品牌成片</span>
            <span class="proof-pill">适合创业、产品、战略判断</span>
          </div>
          <div class="hero-actions">
            <a class="hero-link primary" href="#filmDemo">观看成片 Demo</a>
            <a class="hero-link secondary" href="#conversationWorkbench">直接开始对话</a>
          </div>
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
            <div class="tiny">先看成片，再点典型问题，一键切到对应智者开始对话</div>
          </div>
        </div>
      </div>
    </section>

    <section class="quickstart" id="quickStart">
      <div class="quickstart-copy">
        <div class="eyebrow">Quick Start</div>
        <h3>第一次打开，不必先研究。直接带着一个真实问题进入产品。</h3>
        <p>
          下面三条是最容易感受到产品价值的入口。点击后会自动切换到对应人物，
          并把问题填进对话框，适合首访、演示和转发给团队成员试用。
        </p>
      </div>
      <div class="quickstart-grid">
        <button class="prompt-card" type="button" data-prompt-celeb="sam_altman" data-prompt-text="如果我要从 0 到 1 做一个全球化产品，你会先看哪三个变量？">
          <small>创业 / 增长</small>
          <strong>用山姆·奥特曼的视角，看全球化产品从 0 到 1。</strong>
          <span>适合创业者、增长负责人、出海团队先快速试一次真实对话。</span>
        </button>
        <button class="prompt-card" type="button" data-prompt-celeb="buffett" data-prompt-text="现金流只够 6 个月，我应该先守住利润、客户还是团队？">
          <small>经营 / 决策</small>
          <strong>用巴菲特的视角，先拆清企业生死线应该守什么。</strong>
          <span>适合经营压力、融资窗口、裁撤与聚焦等高压判断场景。</span>
        </button>
        <button class="prompt-card" type="button" data-prompt-celeb="peter_drucker" data-prompt-text="如果团队目标很散，明天开始我该先改哪三个管理动作？">
          <small>管理 / 组织</small>
          <strong>用德鲁克的视角，把模糊管理问题收敛成明天就能执行的动作。</strong>
          <span>适合 CEO、产品负责人、项目 owner 做组织收敛和方向统一。</span>
        </button>
      </div>
    </section>

    <section class="film-section" id="filmDemo">
      <div class="film-copy">
        <div class="eyebrow">Cinematic Film</div>
        <h3>这里放的不是占位动画，而是一支已经可以导出的首页成片。</h3>
        <p>
          我们把“深夜独自做关键决定”的故事正式做成 MP4 / WebM 版本，
          加上中文旁白节奏、镜头转场和人物视觉化素材，让首页 demo 本身就能拿去演示、发给投资人、继续剪正式宣传片。
        </p>
        <div class="film-meta">
          <div class="film-stat">
            <strong>导出规格</strong>
            <span>16:9 成片、内嵌字幕、中文旁白、双格式导出，方便网页播放和外部投放。</span>
          </div>
          <div class="film-stat">
            <strong>镜头逻辑</strong>
            <span>夜晚困局、调度智者、收敛行动、发出决定、品牌收束，全部围绕产品真实价值展开。</span>
          </div>
          <div class="film-stat">
            <strong>页面关系</strong>
            <span>上面看成片，下面继续看互动分镜和真人机对话，宣传与体验不再割裂。</span>
          </div>
        </div>
      </div>

      <div class="film-shell">
        <div class="film-screen">
          <div class="film-badge">Exportable Demo Film</div>
          <video controls playsinline autoplay muted loop preload="metadata" poster="/media/demo/digital-sage-film-poster.jpg">
            <source src="/media/demo/digital-sage-film.webm" type="video/webm">
            <source src="/media/demo/digital-sage-film.mp4" type="video/mp4">
          </video>
        </div>
        <div class="film-caption">
          <div>
            <strong>Digital Sage 品牌样片</strong>
            <span>建议静音自动预览，手动开声后可听中文旁白。</span>
          </div>
          <span>MP4 / WebM / Poster 已生成</span>
        </div>
      </div>
    </section>

    <section class="cinema" id="narrativeDemo">
      <div class="cinema-copy">
        <div class="eyebrow">Interactive Storyboard</div>
        <h3>成片下面保留互动分镜，方便你继续改剧情、节奏和产品入镜方式。</h3>
        <p>
          这里保留可暂停、可切场景的导演板版本。你可以把它当做后续迭代脚本，
          继续调整文案、专家组合、冲突强度和每一幕的产品呈现。
        </p>
        <div class="cinema-points">
          <div class="cinema-point">
            <strong>五幕叙事</strong>
            <span>从失眠、求助、比较视角、形成决策，到天亮后的行动，不靠空话撑情绪。</span>
          </div>
          <div class="cinema-point">
            <strong>产品入镜</strong>
            <span>100 位智者目录、切换人物、真实问题、归纳行动板，都直接在画面里出现。</span>
          </div>
          <div class="cinema-point">
            <strong>可播放可暂停</strong>
            <span>它本身就是首页里的可运行 demo，不用额外视频文件，也方便后续继续导出成正式宣传片。</span>
          </div>
        </div>
      </div>

      <div class="cinema-player" id="demoPlayer" data-theme="nightfall">
        <div class="player-top">
          <button class="demo-toggle" id="demoToggle" type="button">暂停 Demo</button>
          <div class="demo-progress" aria-hidden="true"><span id="demoProgress"></span></div>
          <div class="demo-counter" id="demoCounter">01 / 05</div>
        </div>

        <div class="cinema-stage">
          <div class="cinema-frame" id="demoFrame">
            <div class="scene-story">
              <div class="scene-meta">
                <span class="scene-pill" id="demoSceneLabel">Scene 01</span>
                <span id="demoMoment">凌晨 02:13 · 一个人坐在办公室</span>
              </div>
              <h4 id="demoTitle">真正让人失眠的，不是难题，是没有人一起承担判断。</h4>
              <p class="scene-body" id="demoBody"></p>
              <div class="scene-quote" id="demoQuote"></div>
            </div>

            <div class="scene-product">
              <div class="product-window">
                <div class="window-top">
                  <div class="traffic"><span></span><span></span><span></span></div>
                  <div class="window-label">Digital Sage Live Scenario</div>
                </div>
                <div class="expert-strip" id="demoExperts"></div>
                <div class="demo-dialog">
                  <div class="mini-bubble user" id="demoQuestion"></div>
                  <div class="mini-bubble ai" id="demoAnswer"></div>
                </div>
                <div class="outcome-card">
                  <div class="outcome-label" id="demoOutcomeLabel">系统提炼</div>
                  <div class="outcome-text" id="demoOutcome"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="subtitle-bar">
          <div class="subtitle-shell">
            <strong>字幕</strong>
            <p id="demoSubtitle"></p>
          </div>
        </div>

        <div class="scene-dots" id="demoDots"></div>
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
          <div class="detail-hero-head">
            <img class="detail-avatar" id="detailAvatar" alt="人物卡通头像">
            <div>
              <div class="eyebrow" id="detailCategory">人物档案</div>
              <h4 id="detailName">载入中</h4>
              <p id="detailTitle">请稍候，正在加载 100 位智者档案。</p>
            </div>
          </div>
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

        <section class="chat-shell" id="conversationWorkbench">
          <div class="chat-head">
            <div class="chat-title">
              <img class="chat-avatar" id="chatAvatar" alt="聊天头像">
              <div>
                <strong id="chatName">正在连接</strong>
                <div class="tiny">基于公开资料的 AI 模拟回答</div>
              </div>
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

    <section class="faq-section" id="faq">
      <div class="eyebrow">FAQ</div>
      <h3>它不是泛泛聊天工具，而是一个为高价值判断设计的认知界面。</h3>
      <div class="faq-grid">
        <article class="faq-item">
          <h4>这是不是简单的名人角色扮演？</h4>
          <p>不是。Digital Sage 优先围绕人物公开资料、长期立场、判断框架和表达风格来组织回答，重点是帮助你比较不同思路，而不是追求像不像。</p>
        </article>
        <article class="faq-item">
          <h4>第一次体验，最推荐从哪里开始？</h4>
          <p>先看首页成片，再点上面的典型问题入口。它会自动切到对应智者，把问题填进输入框，让你在 1 分钟内感受到产品价值。</p>
        </article>
        <article class="faq-item">
          <h4>它最适合哪些场景？</h4>
          <p>最适合创业决策、产品方向、战略判断、研究框架梳理，以及那些不能只靠情绪和直觉做决定的关键节点。</p>
        </article>
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

    const demoScenes = __DEMO_SCENES_JSON__.map((scene) => ({
      ...scene,
      experts: (scene.experts || []).map((expert) =>
        typeof expert === "string"
          ? { id: expert, name: expert, avatar_url: "" }
          : expert
      ),
      outcomeLabel: scene.outcome_label
    }));

    const demoState = {
      index: 0,
      playing: true,
      sceneDuration: 5600,
      elapsed: 0,
      lastTick: 0,
      frame: null
    };

    const els = {
      heroCount: document.getElementById("heroCount"),
      loadedCount: document.getElementById("loadedCount"),
      filters: document.getElementById("filters"),
      expertList: document.getElementById("expertList"),
      searchInput: document.getElementById("searchInput"),
      detailCategory: document.getElementById("detailCategory"),
      detailAvatar: document.getElementById("detailAvatar"),
      detailName: document.getElementById("detailName"),
      detailTitle: document.getElementById("detailTitle"),
      coreValues: document.getElementById("coreValues"),
      framework: document.getElementById("framework"),
      positions: document.getElementById("positions"),
      chatAvatar: document.getElementById("chatAvatar"),
      chatName: document.getElementById("chatName"),
      chatSource: document.getElementById("chatSource"),
      chatLog: document.getElementById("chatLog"),
      chatForm: document.getElementById("chatForm"),
      messageInput: document.getElementById("messageInput"),
      promptButtons: Array.from(document.querySelectorAll("[data-prompt-celeb]")),
      demoPlayer: document.getElementById("demoPlayer"),
      demoToggle: document.getElementById("demoToggle"),
      demoProgress: document.getElementById("demoProgress"),
      demoCounter: document.getElementById("demoCounter"),
      demoFrame: document.getElementById("demoFrame"),
      demoSceneLabel: document.getElementById("demoSceneLabel"),
      demoMoment: document.getElementById("demoMoment"),
      demoTitle: document.getElementById("demoTitle"),
      demoBody: document.getElementById("demoBody"),
      demoQuote: document.getElementById("demoQuote"),
      demoExperts: document.getElementById("demoExperts"),
      demoQuestion: document.getElementById("demoQuestion"),
      demoAnswer: document.getElementById("demoAnswer"),
      demoOutcomeLabel: document.getElementById("demoOutcomeLabel"),
      demoOutcome: document.getElementById("demoOutcome"),
      demoSubtitle: document.getElementById("demoSubtitle"),
      demoDots: document.getElementById("demoDots")
    };

    function renderDemoDots() {
      els.demoDots.innerHTML = "";
      demoScenes.forEach((scene, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "scene-dot" + (index === demoState.index ? " active" : "");
        button.textContent = scene.label.replace("Scene ", "");
        button.addEventListener("click", () => setDemoScene(index, true));
        els.demoDots.appendChild(button);
      });
    }

    function renderDemoScene(scene) {
      els.demoPlayer.dataset.theme = scene.theme;
      els.demoSceneLabel.textContent = scene.label;
      els.demoMoment.textContent = scene.moment;
      els.demoTitle.textContent = scene.title;
      els.demoBody.textContent = scene.body;
      els.demoQuote.textContent = scene.quote;
      els.demoQuestion.textContent = scene.question;
      els.demoAnswer.textContent = scene.answer;
      els.demoOutcomeLabel.textContent = scene.outcomeLabel;
      els.demoOutcome.textContent = scene.outcome;
      els.demoSubtitle.textContent = scene.subtitle;
      els.demoCounter.textContent = `${String(demoState.index + 1).padStart(2, "0")} / ${String(demoScenes.length).padStart(2, "0")}`;
      els.demoExperts.innerHTML = scene.experts.map((expert) => `
        <span class="expert-token">
          ${expert.avatar_url ? `<img src="${expert.avatar_url}" alt="${expert.name} 卡通头像" loading="lazy">` : ""}
          <span>${expert.name}</span>
        </span>
      `).join("");

      els.demoFrame.style.animation = "none";
      void els.demoFrame.offsetWidth;
      els.demoFrame.style.animation = "sceneIn 560ms ease";
      renderDemoDots();
    }

    function setDemoScene(index, manual = false) {
      demoState.index = (index + demoScenes.length) % demoScenes.length;
      demoState.elapsed = 0;
      renderDemoScene(demoScenes[demoState.index]);
      if (manual && !demoState.playing) {
        els.demoProgress.style.width = "0%";
      }
    }

    function updateDemoProgress(ratio) {
      els.demoProgress.style.width = `${Math.max(0, Math.min(ratio, 1)) * 100}%`;
    }

    function demoTick(timestamp) {
      if (!demoState.lastTick) {
        demoState.lastTick = timestamp;
      }

      const delta = timestamp - demoState.lastTick;
      demoState.lastTick = timestamp;

      if (demoState.playing) {
        demoState.elapsed += delta;
        const ratio = demoState.elapsed / demoState.sceneDuration;
        updateDemoProgress(ratio);
        if (ratio >= 1) {
          setDemoScene(demoState.index + 1);
        }
      }

      demoState.frame = window.requestAnimationFrame(demoTick);
    }

    function toggleDemoPlayback() {
      demoState.playing = !demoState.playing;
      els.demoToggle.textContent = demoState.playing ? "暂停 Demo" : "继续播放";
    }

    function initDemo() {
      renderDemoDots();
      setDemoScene(0);
      els.demoToggle.addEventListener("click", toggleDemoPlayback);
      demoState.frame = window.requestAnimationFrame(demoTick);
    }

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
          <img class="expert-avatar" src="${item.avatar_url}" alt="${item.name} 卡通头像" loading="lazy">
          <div class="expert-card-body">
            <strong>${item.name}</strong>
            <small>${item.name_en} · ${item.title}</small>
            <div class="tags">${item.focus_tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}</div>
          </div>
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
      els.detailAvatar.src = profile.avatar_url;
      els.detailAvatar.alt = `${profile.name} 卡通头像`;
      els.detailName.textContent = profile.name;
      els.detailTitle.textContent = `${profile.title} · ${profile.name_en}`;
      els.chatAvatar.src = profile.avatar_url;
      els.chatAvatar.alt = `${profile.name} 聊天头像`;
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

    async function primeConversation(celebrityId, message) {
      if (!celebrityId) return;
      if (state.activeId !== celebrityId) {
        await selectCelebrity(celebrityId);
      }
      els.messageInput.value = message || "";
      els.messageInput.focus();
      const end = els.messageInput.value.length;
      if (typeof els.messageInput.setSelectionRange === "function") {
        els.messageInput.setSelectionRange(end, end);
      }
      document.getElementById("conversationWorkbench").scrollIntoView({ behavior: "smooth", block: "start" });
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

    els.promptButtons.forEach((button) => {
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          await primeConversation(button.dataset.promptCeleb, button.dataset.promptText || "");
        } finally {
          button.disabled = false;
        }
      });
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

    initDemo();
    bootstrap();
  </script>
</body>
</html>"""
    return shell.replace("__DEMO_SCENES_JSON__", json.dumps(DEMO_SCENES, ensure_ascii=False))


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


@app.get("/api/avatar/{celeb_id}.svg")
async def get_avatar_svg(celeb_id: str) -> Response:
    profile = get_profile(celeb_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    svg = render_cartoon_avatar_svg(celeb_id, profile)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/api/celebrities")
async def list_celebrities() -> list[dict]:
    return [{**item, "avatar_url": avatar_url(item["id"])} for item in get_all_celebrities()]


@app.get("/api/celebrities/{celeb_id}")
async def get_celebrity(celeb_id: str) -> dict:
    profile = get_profile(celeb_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    return {**profile, "avatar_url": avatar_url(celeb_id)}


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
