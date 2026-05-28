"""
智者 Digital Sage API
与全球最聪明的 100 个大脑对话。
"""

from __future__ import annotations

import json
import os
import sys
from html import escape
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

LLM_API_BASE = (
    os.getenv("DEEPSEEK_API_BASE")
    or os.getenv("LLM_API_BASE")
    or os.getenv("MIMO_API_BASE")
    or "https://api.deepseek.com"
)
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("MIMO_API_KEY") or ""
LLM_PRIMARY_MODEL = os.getenv("DEEPSEEK_MODEL") or os.getenv("LLM_MODEL") or "deepseek-v4-pro"
LLM_FALLBACK_MODEL = os.getenv("DEEPSEEK_FALLBACK_MODEL", "deepseek-chat")
LLM_PROVIDER_LABEL = os.getenv("LLM_PROVIDER_LABEL", "DeepSeek")
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


GROWTH_CAMPAIGN_PACK = {
    "funnel": [
        {
            "stage": "1. 种草认知",
            "goal": "让用户知道这不是普通聊天机器人，而是 100 位智者的判断系统。",
            "channels": ["小红书", "抖音", "数字人短视频"],
            "cta": "先看 15 秒数字人短片，再进入免费文字试用。",
        },
        {
            "stage": "2. 免费试用",
            "goal": "用 1 个真实问题触发对话，证明产品能把复杂问题拆清楚。",
            "channels": ["首页对话区", "课程页", "私域二维码"],
            "cta": "选择一位智者，输入当前最难的一个判断。",
        },
        {
            "stage": "3. 付费通话",
            "goal": "把文本体验升级为 10/20/30/60 分钟语音或视频咨询。",
            "channels": ["订单页", "微信/Stripe/Creem 准备位", "电话桥接"],
            "cta": "预约一次 20 分钟智者分身通话。",
        },
        {
            "stage": "4. 记忆订阅",
            "goal": "沉淀用户长期问题、偏好、复盘记录，形成持续订阅现金流。",
            "channels": ["记忆库", "课程进度", "月度复盘报告"],
            "cta": "订阅 3 位常用智者，建立你的长期判断委员会。",
        },
    ],
    "pricing": [
        {"name": "文字试用", "price": "¥0", "unit": "3 次对话", "best_for": "冷启动获客与首次体验"},
        {"name": "10 分钟语音", "price": "¥19", "unit": "单次", "best_for": "快速拆一个具体问题"},
        {"name": "20 分钟语音", "price": "¥39", "unit": "单次", "best_for": "完整梳理一个经营/职业判断"},
        {"name": "30 分钟视频", "price": "¥69", "unit": "单次", "best_for": "带数字人视频形象的深度咨询"},
        {"name": "60 分钟战略局", "price": "¥129", "unit": "单次", "best_for": "多智者联合分析、形成行动清单"},
        {"name": "记忆订阅", "price": "¥59/月", "unit": "3 位智者", "best_for": "长期复盘、课程进度和个人知识库"},
    ],
    "xiaohongshu": [
        {
            "title": "我让巴菲特、乔布斯、孔子一起帮我拆一个问题",
            "cover": "一个问题，100 位智者怎么回答？",
            "hook": "当你一个人做决定时，最缺的不是鸡汤，而是能把局面拆开的脑力。",
            "body": "Digital Sage 把 100 位智者做成可对话的判断界面。你可以问巴菲特现金流，问乔布斯产品取舍，问孔子关系与秩序，问图灵系统设计。先免费试一次文字对话，再决定是否进入语音/视频通话。",
            "tags": ["#AI工具", "#创业决策", "#知识付费", "#数字人", "#个人成长"],
            "cta": "评论区留下你最想问的智者，我把问题做成下一条案例。",
        },
        {
            "title": "如果你有一个重大决定，先别急着问朋友",
            "cover": "重大决定前，先问 3 个智者",
            "hook": "朋友会安慰你，智者会逼你看清变量。",
            "body": "我用 Digital Sage 做了一个三智者判断法：巴菲特看现金流，德鲁克看组织责任，老子看顺势与边界。一个复杂问题先经过三套思路，再形成行动清单。",
            "tags": ["#决策模型", "#AI分身", "#商业思维", "#打工人成长"],
            "cta": "保存这条，下次卡住时直接用三智者提问法。",
        },
        {
            "title": "100 位智者 × 1000 门课程，我把它做成了一个知识宇宙",
            "cover": "100 位智者的 1000 门课",
            "hook": "不是名人语录合集，而是一套可以听、可以学、可以对话的系统。",
            "body": "每位智者都有 10 门课：总览、三大核心概念、判断框架、案例、工具箱、价值系统、方法论和行动整合。每课都有语音导读，适合通勤时先听，再进入页面学习。",
            "tags": ["#在线课程", "#AI学习", "#知识宇宙", "#终身学习"],
            "cta": "主页可以直接进课程目录，先从巴菲特/孔子/乔布斯开始。",
        },
    ],
    "douyin": [
        {
            "title": "15 秒：凌晨两点的创业者",
            "duration": "15s",
            "hook": "现金流只够 4 个月，你会问谁？",
            "shots": [
                "0-3s：创业者盯着现金流表，字幕：只够 4 个月。",
                "3-7s：屏幕弹出巴菲特、德鲁克、乔布斯三个数字人。",
                "7-12s：三位智者给出不同判断维度：现金流、组织、产品。",
                "12-15s：产品页出现行动清单，CTA：来问你的第一位智者。",
            ],
            "voiceover": "真正让人失眠的不是难题，是没有人一起承担判断。Digital Sage，让 100 位智者陪你把复杂问题看清一层。",
            "cta": "搜索 Digital Sage，免费问一次。",
        },
        {
            "title": "30 秒：同一个问题，三种世界级思路",
            "duration": "30s",
            "hook": "同一个问题，巴菲特、乔布斯、孔子会怎么拆？",
            "shots": [
                "0-5s：用户输入问题：我要不要砍掉一条产品线？",
                "5-13s：巴菲特回答：先看长期现金流和护城河。",
                "13-20s：乔布斯回答：砍到只剩用户真正记得的东西。",
                "20-26s：孔子回答：先正名，明确责任、关系和秩序。",
                "26-30s：系统汇总为 3 条行动建议。",
            ],
            "voiceover": "你不需要一个万能答案，你需要不同大脑帮你看见盲区。Digital Sage，把世界级判断变成一次对话。",
            "cta": "点进主页，选择你的智者。",
        },
        {
            "title": "60 秒：数字人课程入口",
            "duration": "60s",
            "hook": "如果巴菲特有一套 10 节课，会从哪里讲起？",
            "shots": [
                "0-8s：展示 100 位智者宫殿和课程总目录。",
                "8-22s：打开巴菲特课程：总览、价值投资、复利、护城河。",
                "22-36s：播放课程音频导读，字幕同步显示关键句。",
                "36-50s：切到数字人对话：用户问现金流，巴菲特分身回答。",
                "50-60s：展示付费路径：文字试用、语音、视频、记忆订阅。",
            ],
            "voiceover": "课程负责建立框架，对话负责解决当下问题，记忆订阅负责长期复盘。Digital Sage，不只是聊天，是你的智者委员会。",
            "cta": "从一门免费课程开始。",
        },
    ],
    "digital_humans": [
        {
            "sage": "沃伦·巴菲特",
            "avatar_direction": "银发、圆框眼镜、温和但克制的投资家形象，背景为深色书房与财报光幕。",
            "opening": "如果现金流只够六个月，我不会先问增长，我会先问你真正能活下来的核心业务是什么。",
            "use_case": "企业现金流、投资、长期主义、价格与价值。",
        },
        {
            "sage": "史蒂夫·乔布斯",
            "avatar_direction": "黑色高领、极简舞台、产品轮廓线和白色聚光灯。",
            "opening": "别告诉我你能做什么，告诉我用户会记住什么。伟大的产品首先是一次删减。",
            "use_case": "产品定位、品牌、体验设计、发布会式表达。",
        },
        {
            "sage": "孔子",
            "avatar_direction": "温润长者、竹简、礼序空间，避免神化，强调秩序与关系。",
            "opening": "先正名。你真正困住的，可能不是选择，而是责任、角色和关系没有被讲清楚。",
            "use_case": "组织治理、家庭关系、团队伦理、长期修身。",
        },
        {
            "sage": "老子",
            "avatar_direction": "留白山水、慢节奏镜头、浅金线条，表达顺势和边界。",
            "opening": "越用力的地方，越要问是不是逆势。先看水往哪里流，再决定你该不该动。",
            "use_case": "战略取舍、压力管理、顺势而为、反脆弱节奏。",
        },
        {
            "sage": "艾伦·图灵",
            "avatar_direction": "复古计算机、矩阵光点、冷静逻辑感，适合系统问题拆解。",
            "opening": "把情绪先放在一边。我们把问题写成输入、规则、状态和输出。",
            "use_case": "系统设计、AI、自动化、复杂问题建模。",
        },
        {
            "sage": "钟南山",
            "avatar_direction": "医学会议室、证据卡片、稳重正直的公共卫生专家形象。",
            "opening": "先排危险，再看证据。判断不能只看愿望，要看风险和可验证事实。",
            "use_case": "健康决策、风险沟通、公共卫生、循证判断。",
        },
    ],
    "calendar": [
        {"day": "D1", "channel": "小红书", "asset": "产品故事笔记", "topic": "一个重大决定前，先问 3 位智者"},
        {"day": "D2", "channel": "抖音", "asset": "15 秒短视频", "topic": "现金流只够 4 个月，你会问谁？"},
        {"day": "D3", "channel": "小红书", "asset": "课程种草", "topic": "100 位智者 × 1000 门课程"},
        {"day": "D4", "channel": "抖音", "asset": "数字人对话", "topic": "巴菲特、乔布斯、孔子回答同一问题"},
        {"day": "D5", "channel": "小红书", "asset": "案例复盘", "topic": "我用三智者法拆了一次产品取舍"},
        {"day": "D6", "channel": "抖音", "asset": "课程导流", "topic": "如果巴菲特开一套 10 节课"},
        {"day": "D7", "channel": "全渠道", "asset": "直播/社群转化", "topic": "免费帮 10 个用户做一次智者判断"},
    ],
}


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


async def _call_deepseek(profile: dict, prompt: str, fallback_message: str, topic: str) -> tuple[str, str]:
    if not LLM_API_KEY:
        return _build_fallback_response(profile, fallback_message, topic), "fallback"

    model_candidates = [LLM_PRIMARY_MODEL]
    if LLM_FALLBACK_MODEL and LLM_FALLBACK_MODEL not in model_candidates:
        model_candidates.append(LLM_FALLBACK_MODEL)

    system_prompt = (
        f"你是{profile['name']}，{profile['title']}。"
        "请保持该人物公开形象中的思考方式与表达风格，"
        "但不要声称自己真的就是本人。"
    )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for model_name in model_candidates:
                response = await client.post(
                    f"{LLM_API_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 800,
                    },
                )
                if response.is_success:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if content:
                        return content, "deepseek"
                elif response.status_code < 500:
                    continue
    except Exception:
        pass

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
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Serif+SC:wght@500;600;700;900&display=swap" rel="stylesheet">
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
      --bg: #08080b;
      --bg2: #101014;
      --bg3: #18181d;
      --ink: #fafafa;
      --muted: #a1a1aa;
      --line: rgba(245, 217, 138, 0.13);
      --card: rgba(28, 28, 34, 0.92);
      --accent: #e2b64f;
      --accent-soft: rgba(226, 182, 79, 0.13);
      --gold: #e2b64f;
      --gold-2: #f5d98a;
      --shadow: 0 28px 80px rgba(0, 0, 0, 0.35);
      --radius: 28px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Inter", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 18% 8%, rgba(226, 182, 79, 0.14), transparent 28%),
        radial-gradient(circle at 82% 16%, rgba(94, 78, 44, 0.24), transparent 22%),
        linear-gradient(180deg, #050506 0%, var(--bg) 42%, #0d0d10 100%);
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
      flex-wrap: wrap;
      align-items: center;
      gap: 12px;
      color: var(--muted);
      font-size: 0.94rem;
    }
    .lang-toggle {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.06);
      border: 1px solid rgba(17, 24, 39, 0.08);
    }
    .nav-pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 34px;
      padding: 0 12px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--muted);
      background: rgba(255, 255, 255, 0.045);
      text-decoration: none;
      font-size: 0.88rem;
    }
    .lang-button {
      border: none;
      background: transparent;
      color: var(--muted);
      min-height: 34px;
      padding: 0 12px;
      border-radius: 999px;
      font: inherit;
      cursor: pointer;
      transition: background 180ms ease, color 180ms ease, transform 180ms ease;
    }
    .lang-button.active {
      background: linear-gradient(135deg, #111827, #1d4ed8);
      color: white;
    }
    .lang-button:hover {
      transform: translateY(-1px);
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
    .curriculum {
      display: grid;
      gap: 18px;
      margin: 0 0 28px;
    }
    .curriculum-head {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 18px;
    }
    .curriculum-head h3 {
      margin: 10px 0 0;
      font-size: clamp(2rem, 3vw, 3rem);
      line-height: 1.04;
      letter-spacing: -0.05em;
    }
    .curriculum-head p {
      margin: 8px 0 0;
      max-width: 780px;
      color: #465467;
      line-height: 1.8;
    }
    .curriculum-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 46px;
      padding: 0 18px;
      border-radius: 999px;
      background: rgba(255,255,255,0.76);
      border: 1px solid rgba(17, 24, 39, 0.08);
      color: var(--ink);
      text-decoration: none;
      white-space: nowrap;
      transition: transform 180ms ease;
    }
    .curriculum-shell {
      display: grid;
      grid-template-columns: minmax(0, 1.3fr) minmax(300px, 0.7fr);
      gap: 18px;
      align-items: start;
    }
    .curriculum-panel,
    .spotlight-panel,
    .featured-card {
      border-radius: 28px;
      background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(255,255,255,0.68));
      border: 1px solid rgba(255,255,255,0.72);
      box-shadow: var(--shadow);
    }
    .curriculum-panel,
    .spotlight-panel {
      padding: 22px;
    }
    .curriculum-stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }
    .curriculum-stat,
    .domain-chip,
    .blueprint-card,
    .spotlight-lesson,
    .featured-card {
      border-radius: 22px;
      border: 1px solid rgba(17, 24, 39, 0.08);
      background: rgba(255,255,255,0.74);
    }
    .curriculum-stat {
      padding: 16px;
    }
    .curriculum-stat strong {
      display: block;
      font-size: 1.65rem;
      line-height: 1;
      letter-spacing: -0.04em;
      color: var(--accent);
    }
    .curriculum-stat span {
      display: block;
      margin-top: 8px;
      color: var(--muted);
      font-size: 0.84rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .blueprint-rail {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 12px;
    }
    .blueprint-card {
      padding: 16px;
      min-height: 100%;
    }
    .blueprint-card strong,
    .domain-chip strong,
    .spotlight-panel strong,
    .featured-card strong {
      display: block;
      color: var(--ink);
      line-height: 1.35;
    }
    .blueprint-card p,
    .domain-chip p,
    .spotlight-panel p,
    .featured-card p {
      margin: 8px 0 0;
      color: #465467;
      line-height: 1.75;
      font-size: 0.92rem;
    }
    .blueprint-card small,
    .domain-chip small,
    .spotlight-panel small,
    .featured-card small {
      display: block;
      margin-top: 10px;
      color: var(--muted);
      line-height: 1.6;
    }
    .blueprint-num,
    .domain-count {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.06);
      color: var(--muted);
      font-size: 0.74rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .domain-board {
      display: grid;
      gap: 10px;
    }
    .domain-chip {
      padding: 16px;
      border-left: 4px solid var(--domain-accent, #1d4ed8);
    }
    .spotlight-panel {
      display: grid;
      gap: 14px;
    }
    .spotlight-top {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .spotlight-avatar {
      width: 68px;
      height: 68px;
      border-radius: 24px;
      border: 1px solid rgba(17, 24, 39, 0.08);
      background: rgba(255,255,255,0.85);
      object-fit: cover;
      flex: 0 0 auto;
    }
    .spotlight-tags,
    .featured-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .spotlight-tags span,
    .featured-tags span {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      background: rgba(29, 78, 216, 0.08);
      color: var(--accent);
      font-size: 0.78rem;
    }
    .spotlight-lessons {
      display: grid;
      gap: 10px;
    }
    .spotlight-lesson {
      padding: 14px 16px;
    }
    .spotlight-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .spotlight-actions a {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 42px;
      padding: 0 14px;
      border-radius: 999px;
      text-decoration: none;
      border: 1px solid rgba(17, 24, 39, 0.08);
      transition: transform 180ms ease;
    }
    .spotlight-actions .primary {
      background: linear-gradient(135deg, #111827, #1d4ed8);
      color: white;
      border-color: transparent;
    }
    .spotlight-actions .secondary {
      background: rgba(255,255,255,0.78);
      color: var(--ink);
    }
    .featured-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }
    .featured-card {
      padding: 18px;
      text-decoration: none;
      color: inherit;
      transition: transform 180ms ease, border-color 180ms ease;
    }
    .featured-card-top {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .featured-card-top img {
      width: 52px;
      height: 52px;
      border-radius: 18px;
      border: 1px solid rgba(17, 24, 39, 0.08);
      background: rgba(255,255,255,0.88);
      object-fit: cover;
      flex: 0 0 auto;
    }
    .featured-card:hover,
    .curriculum-link:hover,
    .spotlight-actions a:hover {
      transform: translateY(-1px);
    }
    .featured-card:hover {
      border-color: rgba(29, 78, 216, 0.18);
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
      background-size: 42px 42px;
      mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.72), transparent 75%);
    }
    .nav {
      position: sticky;
      top: 0;
      z-index: 20;
      padding: 10px 0;
      background: rgba(8, 8, 11, 0.72);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(18px);
    }
    .brand h1,
    .hero-copy h2,
    .quickstart-copy h3,
    .film-copy h3,
    .cinema-copy h3,
    .curriculum-head h3,
    .detail-title h3,
    .faq h3 {
      font-family: "Noto Serif SC", serif;
    }
    .brand-mark {
      color: #17130a;
      background: linear-gradient(135deg, var(--gold-2), var(--gold));
      box-shadow: 0 18px 48px rgba(226, 182, 79, 0.18);
    }
    .brand p,
    .status,
    .hero-copy p,
    .quickstart-copy p,
    .film-copy p,
    .cinema-copy p,
    .curriculum-head p,
    .blueprint-card p,
    .domain-chip p,
    .spotlight-panel p,
    .featured-card p,
    .prompt-card span,
    .film-stat span,
    .cinema-point span,
    .tiny {
      color: var(--muted);
    }
    .hero,
    .hero-stats,
    .prompt-card,
    .film-shell,
    .curriculum-panel,
    .spotlight-panel,
    .featured-card,
    .faq-item,
    .search,
    .chat,
    .profile-detail,
    .expert-card,
    .quickstart-grid .prompt-card {
      border: 1px solid var(--line);
      background:
        radial-gradient(circle at 82% 14%, rgba(226, 182, 79, 0.12), transparent 28%),
        linear-gradient(145deg, rgba(28, 28, 34, 0.96), rgba(12, 12, 15, 0.96));
      box-shadow: var(--shadow);
    }
    .hero {
      min-height: 620px;
      display: grid;
      align-items: center;
    }
    .hero::after {
      background:
        linear-gradient(115deg, transparent 0 38%, rgba(226, 182, 79, 0.06) 39% 41%, transparent 42%),
        radial-gradient(circle at 50% 110%, rgba(226, 182, 79, 0.16), transparent 36%);
    }
    .hero-copy h2 {
      color: var(--ink);
      font-weight: 900;
    }
    .hero-copy h2 span,
    .eyebrow,
    .stat-label,
    .prompt-card small,
    .blueprint-num,
    .domain-count {
      color: var(--gold-2);
    }
    .hero-proof .proof-pill,
    .lang-toggle,
    .curriculum-link,
    .hero-link.secondary,
    .spotlight-actions .secondary,
    .spotlight-tags span,
    .featured-tags span {
      color: var(--muted);
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.045);
    }
    .hero-link.primary,
    .lang-button.active,
    .spotlight-actions .primary {
      color: #17130a;
      background: linear-gradient(135deg, var(--gold-2), var(--gold));
      border-color: transparent;
    }
    .lang-button,
    .hero-link.secondary,
    .curriculum-link,
    .spotlight-actions .secondary {
      color: var(--muted);
    }
    .stat-value,
    .curriculum-stat strong {
      color: var(--gold-2);
    }
    .curriculum-stat,
    .domain-chip,
    .blueprint-card,
    .spotlight-lesson,
    .featured-card,
    .faq-item {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.045);
    }
    .blueprint-card strong,
    .domain-chip strong,
    .spotlight-panel strong,
    .featured-card strong,
    .prompt-card strong,
    .film-caption strong,
    .cinema-point strong,
    .brand h1 {
      color: var(--ink);
    }
    .domain-chip {
      border-left-color: var(--domain-accent, var(--gold));
    }
    .film-screen,
    .cinema-player {
      border: 1px solid rgba(245, 217, 138, 0.13);
    }
    .film-caption,
    .film-stat,
    .cinema-point {
      border-color: var(--line);
      color: var(--muted);
    }
    .search input,
    textarea,
    select {
      color: var(--ink);
      border-color: var(--line);
      background: rgba(255, 255, 255, 0.06);
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
      .curriculum-shell,
      .featured-grid,
      .detail-grid,
      .faq-grid,
      .toolbar,
      .chat-form,
      .cinema-frame {
        grid-template-columns: 1fr;
      }
      .blueprint-rail {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .curriculum-stats {
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
      .curriculum-head {
        flex-direction: column;
        align-items: flex-start;
      }
      .blueprint-rail {
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
<body data-lang="zh">
  <div class="page">
    <div class="nav">
      <div class="brand">
        <div class="brand-mark">智</div>
        <div>
          <h1>Digital Sage</h1>
          <p id="brandTagline">与全球最聪明的 100 个大脑对话</p>
        </div>
      </div>
      <div class="status">
        <a class="nav-pill" href="/growth">增长落地</a>
        <span id="loadedCount">载入中</span>
        <span id="statusLabel">Production Live · DeepSeek</span>
        <div class="lang-toggle" id="langToggle">
          <button type="button" class="lang-button active" data-lang="zh">中文</button>
          <button type="button" class="lang-button" data-lang="en">EN</button>
        </div>
      </div>
    </div>

    <section class="hero">
      <div class="hero-grid">
        <div class="hero-copy">
          <h2><span id="heroAccent">Thought Interface</span><span id="heroTitle">智者</span></h2>
          <p id="heroBody">
            把巴菲特、乔布斯、图灵、钟南山、孔子等 100 位人物的公开立场、长期方法论和表达风格，
            整理成一个可对话的判断界面。你不是来玩随机角色扮演，而是来借世界级思路把复杂问题看清一层。
          </p>
          <div class="hero-proof">
            <span class="proof-pill" id="proofPill0">100 位长期主义智者</span>
            <span class="proof-pill" id="proofPill1">DeepSeek 实时生成回答</span>
            <span class="proof-pill" id="proofPill2">首页自带品牌成片</span>
            <span class="proof-pill" id="proofPill3">适合创业、产品、战略判断</span>
          </div>
          <div class="hero-actions">
            <a class="hero-link primary" id="heroActionFilm" href="#filmDemo">观看成片 Demo</a>
            <a class="hero-link secondary" id="heroActionChat" href="#conversationWorkbench">直接开始对话</a>
          </div>
        </div>
        <div class="hero-stats">
          <div>
            <div class="stat-label" id="heroStatLabel0">人物总数</div>
            <div class="stat-value" id="heroCount">100</div>
          </div>
          <div>
            <div class="stat-label" id="heroStatLabel1">覆盖领域</div>
            <div class="tiny" id="heroStatBody1">商业 / 科技 / 科学 / 医学 / 思想 / 文化 / 治理 / 设计</div>
          </div>
          <div>
            <div class="stat-label" id="heroStatLabel2">体验方式</div>
            <div class="tiny" id="heroStatBody2">先看成片，再点典型问题，一键切到对应智者开始对话</div>
          </div>
        </div>
      </div>
    </section>

    <section class="quickstart" id="quickStart">
      <div class="quickstart-copy">
        <div class="eyebrow" id="quickstartEyebrow">Quick Start</div>
        <h3 id="quickstartTitle">第一次打开，不必先研究。直接带着一个真实问题进入产品。</h3>
        <p id="quickstartBody">
          下面三条是最容易感受到产品价值的入口。点击后会自动切换到对应人物，
          并把问题填进对话框，适合首访、演示和转发给团队成员试用。
        </p>
      </div>
      <div class="quickstart-grid">
        <button class="prompt-card" id="promptCard0" type="button" data-prompt-celeb="sam_altman" data-prompt-text="如果我要从 0 到 1 做一个全球化产品，你会先看哪三个变量？">
          <small id="promptCard0Small">创业 / 增长</small>
          <strong id="promptCard0Strong">用山姆·奥特曼的视角，看全球化产品从 0 到 1。</strong>
          <span id="promptCard0Body">适合创业者、增长负责人、出海团队先快速试一次真实对话。</span>
        </button>
        <button class="prompt-card" id="promptCard1" type="button" data-prompt-celeb="buffett" data-prompt-text="现金流只够 6 个月，我应该先守住利润、客户还是团队？">
          <small id="promptCard1Small">经营 / 决策</small>
          <strong id="promptCard1Strong">用巴菲特的视角，先拆清企业生死线应该守什么。</strong>
          <span id="promptCard1Body">适合经营压力、融资窗口、裁撤与聚焦等高压判断场景。</span>
        </button>
        <button class="prompt-card" id="promptCard2" type="button" data-prompt-celeb="peter_drucker" data-prompt-text="如果团队目标很散，明天开始我该先改哪三个管理动作？">
          <small id="promptCard2Small">管理 / 组织</small>
          <strong id="promptCard2Strong">用德鲁克的视角，把模糊管理问题收敛成明天就能执行的动作。</strong>
          <span id="promptCard2Body">适合 CEO、产品负责人、项目 owner 做组织收敛和方向统一。</span>
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

    <section class="curriculum" id="curriculum">
      <div class="curriculum-head">
        <div>
          <div class="eyebrow">Spark 2 Curriculum</div>
          <h3 id="curriculumTitle">学院式课程地图：100 位智者，每人 10 课，先听课再进入结构化训练。</h3>
          <p id="curriculumBody">主页和课程站共用同一份课程 catalog。这里先用 Spark 2 看见全局、领域和重点人物，点进课程页后会看到统一的深色讲义、课程音频、案例、书单和 7 天训练。</p>
        </div>
        <a class="curriculum-link" id="curriculumLink" href="/courses/">进入全部课程</a>
      </div>

      <div class="curriculum-shell">
        <div class="curriculum-panel">
          <div class="curriculum-stats" id="courseStats"></div>
          <div class="blueprint-rail" id="blueprintRail"></div>
        </div>
        <div class="curriculum-panel">
          <div class="eyebrow" id="curriculumDomainsEyebrow">Domains</div>
          <div class="domain-board" id="domainBoard"></div>
        </div>
      </div>

      <div class="spotlight-panel" id="courseSpotlight">
        <div class="tiny" id="courseSpotlightLoading">课程数据载入中…</div>
      </div>

      <div class="featured-grid" id="featuredCourses"></div>
    </section>

    <section class="toolbar">
      <div class="search">
        <span id="searchLabel">搜索</span>
        <input id="searchInput" placeholder="输入中文名、英文名或领域关键词">
      </div>
      <div class="filters" id="filters"></div>
    </section>

    <section class="main">
      <aside class="panel">
        <h3 id="directoryTitle">Expert Directory</h3>
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
            <h5 id="detailHeadingValues">核心价值</h5>
            <ul id="coreValues"></ul>
          </article>
          <article class="detail">
            <h5 id="detailHeadingFramework">判断框架</h5>
            <ul id="framework"></ul>
          </article>
          <article class="detail">
            <h5 id="detailHeadingPositions">重点立场</h5>
            <ul id="positions"></ul>
          </article>
        </section>

        <section class="chat-shell" id="conversationWorkbench">
          <div class="chat-head">
            <div class="chat-title">
              <img class="chat-avatar" id="chatAvatar" alt="聊天头像">
              <div>
                <strong id="chatName">正在连接</strong>
                <div class="tiny" id="chatSubtitle">基于公开资料的 AI 模拟回答</div>
              </div>
            </div>
            <div class="tiny" id="chatSource">准备中</div>
          </div>
          <div class="chat-log" id="chatLog"></div>
          <form class="chat-form" id="chatForm">
            <textarea id="messageInput" placeholder="例如：如果我要从 0 到 1 做一个全球化产品，你会先看哪三个变量？"></textarea>
            <button class="submit" id="chatSubmit" type="submit">开始对话</button>
          </form>
        </section>
      </div>
    </section>

    <section class="faq-section" id="faq">
      <div class="eyebrow">FAQ</div>
      <h3 id="faqTitle">它不是泛泛聊天工具，而是一个为高价值判断设计的认知界面。</h3>
      <div class="faq-grid">
        <article class="faq-item">
          <h4 id="faqQ0">这是不是简单的名人角色扮演？</h4>
          <p id="faqA0">不是。Digital Sage 优先围绕人物公开资料、长期立场、判断框架和表达风格来组织回答，重点是帮助你比较不同思路，而不是追求像不像。</p>
        </article>
        <article class="faq-item">
          <h4 id="faqQ1">第一次体验，最推荐从哪里开始？</h4>
          <p id="faqA1">先看首页成片，再点上面的典型问题入口。它会自动切到对应智者，把问题填进输入框，让你在 1 分钟内感受到产品价值。</p>
        </article>
        <article class="faq-item">
          <h4 id="faqQ2">它最适合哪些场景？</h4>
          <p id="faqA2">最适合创业决策、产品方向、战略判断、研究框架梳理，以及那些不能只靠情绪和直觉做决定的关键节点。</p>
        </article>
      </div>
    </section>
  </div>

  <script>
    const categoryLabels = {
      zh: {
        all: "全部",
        business: "商业",
        technology: "科技",
        science: "科学",
        medical: "医学",
        philosophy: "思想",
        culture: "文化",
        policy: "治理",
        design: "设计"
      },
      en: {
        all: "All",
        business: "Business",
        technology: "Technology",
        science: "Science",
        medical: "Medical",
        philosophy: "Philosophy",
        culture: "Culture",
        policy: "Governance",
        design: "Design"
      }
    };

    const uiCopy = {
      zh: {
        brandTagline: "与全球最聪明的 100 个大脑对话",
        statusLabel: "Production Live · DeepSeek",
        heroAccent: "Thought Interface",
        heroTitle: "智者",
        heroBody: "把巴菲特、乔布斯、图灵、钟南山、孔子等 100 位人物的公开立场、长期方法论和表达风格，整理成一个可对话的判断界面。你不是来玩随机角色扮演，而是来借世界级思路把复杂问题看清一层。",
        proofPills: ["100 位长期主义智者", "DeepSeek 实时生成回答", "首页自带品牌成片", "适合创业、产品、战略判断"],
        heroActions: ["观看成片 Demo", "直接开始对话"],
        heroStatLabels: ["人物总数", "覆盖领域", "体验方式"],
        heroStatBodies: ["", "商业 / 科技 / 科学 / 医学 / 思想 / 文化 / 治理 / 设计", "先看成片，再点典型问题，一键切到对应智者开始对话"],
        quickstartEyebrow: "Quick Start",
        quickstartTitle: "第一次打开，不必先研究。直接带着一个真实问题进入产品。",
        quickstartBody: "下面三条是最容易感受到产品价值的入口。点击后会自动切换到对应人物，并把问题填进对话框，适合首访、演示和转发给团队成员试用。",
        prompts: [
          {
            small: "创业 / 增长",
            strong: "用山姆·奥特曼的视角，看全球化产品从 0 到 1。",
            body: "适合创业者、增长负责人、出海团队先快速试一次真实对话。"
          },
          {
            small: "经营 / 决策",
            strong: "用巴菲特的视角，先拆清企业生死线应该守什么。",
            body: "适合经营压力、融资窗口、裁撤与聚焦等高压判断场景。"
          },
          {
            small: "管理 / 组织",
            strong: "用德鲁克的视角，把模糊管理问题收敛成明天就能执行的动作。",
            body: "适合 CEO、产品负责人、项目 owner 做组织收敛和方向统一。"
          }
        ],
        curriculumTitle: "学院式课程地图：100 位智者，每人 10 课，先听课再进入结构化训练。",
        curriculumBody: "主页和课程站共用同一份课程 catalog。这里先用 Spark 2 看见全局、领域和重点人物，点进课程页后会看到统一的深色讲义、课程音频、案例、书单和 7 天训练。",
        curriculumLink: "进入全部课程",
        curriculumDomainsEyebrow: "Domains",
        courseLoading: "课程数据载入中…",
        searchLabel: "搜索",
        searchPlaceholder: "输入中文名、英文名或领域关键词",
        directoryTitle: "Expert Directory",
        detailCategoryDefault: "人物档案",
        detailLoadingName: "载入中",
        detailLoadingBody: "请稍候，正在加载 100 位智者档案。",
        detailHeadings: ["核心价值", "判断框架", "重点立场"],
        chatSubtitle: "基于公开资料的 AI 模拟回答",
        chatSourcePreparing: "准备中",
        chatPlaceholder: "例如：如果我要从 0 到 1 做一个全球化产品，你会先看哪三个变量？",
        chatSubmit: "开始对话",
        faqTitle: "它不是泛泛聊天工具，而是一个为高价值判断设计的认知界面。",
        faq: [
          {
            q: "这是不是简单的名人角色扮演？",
            a: "不是。Digital Sage 优先围绕人物公开资料、长期立场、判断框架和表达风格来组织回答，重点是帮助你比较不同思路，而不是追求像不像。"
          },
          {
            q: "第一次体验，最推荐从哪里开始？",
            a: "先看首页成片，再点上面的典型问题入口。它会自动切到对应智者，把问题填进输入框，让你在 1 分钟内感受到产品价值。"
          },
          {
            q: "它最适合哪些场景？",
            a: "最适合创业决策、产品方向、战略判断、研究框架梳理，以及那些不能只靠情绪和直觉做决定的关键节点。"
          }
        ],
        emptySearch: "没有匹配结果。",
        chatGenerating: "正在生成回答…",
        demoPause: "暂停 Demo",
        demoResume: "继续播放",
        loadedCount: (count) => `已载入 ${count} 位智者`,
        detailCategory: (labelZh) => labelZh,
        detailTitle: (profile) => `${profile.title} · ${profile.name_en}`,
        chatName: (profile) => `与 ${profile.name} 对话`,
        chatSource: (profile) => `方法论焦点：${profile.focus_tags.slice(0, 3).join(" / ")}`,
        chatIntro: (profile) => `已进入 ${profile.name} 的思考界面。你可以直接提问，我会优先沿着 ${profile.focus_tags.slice(0, 3).join("、")} 这条线索回答。`,
        sourceLabelDeepseek: "Source: DeepSeek API",
        sourceLabelFallback: "Source: Local fallback persona"
      },
      en: {
        brandTagline: "Talk with 100 of the world's sharpest minds",
        statusLabel: "Production Live · DeepSeek",
        heroAccent: "Thought Interface",
        heroTitle: "Digital Sage",
        heroBody: "Digital Sage turns the public positions, long-term methods, and speaking patterns of 100 iconic thinkers into a conversational judgment interface. This is not random role-play. It is a way to borrow world-class reasoning when the problem in front of you is still unclear.",
        proofPills: ["100 long-horizon minds", "DeepSeek-generated live answers", "Built-in brand film on the homepage", "Designed for strategy, product, and founder decisions"],
        heroActions: ["Watch the demo film", "Start a live session"],
        heroStatLabels: ["Profiles", "Coverage", "Experience"],
        heroStatBodies: ["", "Business / Technology / Science / Medicine / Philosophy / Culture / Governance / Design", "Watch the film, tap a real prompt, and jump directly into the matched mind."],
        quickstartEyebrow: "Quick Start",
        quickstartTitle: "Do not study the interface first. Enter with a real decision.",
        quickstartBody: "These three prompts are the fastest way to feel the product. Each click switches to the right mind and pre-fills the question so a first-time visitor can understand the value in under a minute.",
        prompts: [
          {
            small: "Founders / Growth",
            strong: "Use Sam Altman's lens to inspect a 0-to-1 global product.",
            body: "Best for founders, growth leads, and outbound teams who want one real conversation first."
          },
          {
            small: "Operating / Decisions",
            strong: "Use Buffett's lens to decide what must be protected first.",
            body: "Best for cash pressure, financing windows, layoffs, and focus decisions under stress."
          },
          {
            small: "Management / Organization",
            strong: "Use Drucker's lens to turn vague management pain into next-day actions.",
            body: "Best for CEOs, product leads, and project owners who need operating alignment."
          }
        ],
        curriculumTitle: "An academy-style curriculum map: 100 minds, 10 lessons each, audio first, structured practice next.",
        curriculumBody: "The homepage and the course site share the same catalog. Use the Spark 2 board to see the full map, then open each course for the dark lecture layout, audio narration, cases, reference shelf, and 7-day drills.",
        curriculumLink: "Open full curriculum",
        curriculumDomainsEyebrow: "Domains",
        courseLoading: "Loading curriculum data…",
        searchLabel: "Search",
        searchPlaceholder: "Search by Chinese name, English name, or domain keyword",
        directoryTitle: "Expert Directory",
        detailCategoryDefault: "Profile",
        detailLoadingName: "Loading",
        detailLoadingBody: "Loading the 100-mind profile layer.",
        detailHeadings: ["Core Values", "Judgment Framework", "Core Positions"],
        chatSubtitle: "AI simulation grounded in public materials",
        chatSourcePreparing: "Preparing",
        chatPlaceholder: "Example: If I am building a global product from zero, which three variables would you inspect first?",
        chatSubmit: "Start session",
        faqTitle: "This is not a generic chat toy. It is a reasoning surface for high-value decisions.",
        faq: [
          {
            q: "Is this just celebrity role-play?",
            a: "No. Digital Sage organizes replies around public materials, long-term positions, judgment order, and speaking style. The goal is to compare reasoning systems, not to imitate a face."
          },
          {
            q: "Where should a first-time visitor start?",
            a: "Watch the film first, then tap one of the live prompts. The product will switch to the right mind, prefill the question, and make the value obvious quickly."
          },
          {
            q: "What is it best suited for?",
            a: "Founder decisions, product direction, strategic judgment, and research framing, especially when intuition alone is too expensive."
          }
        ],
        emptySearch: "No matching profiles.",
        chatGenerating: "Generating answer…",
        demoPause: "Pause demo",
        demoResume: "Resume demo",
        loadedCount: (count) => `${count} profiles loaded`,
        detailCategory: (labelZh, profile, meta) => meta?.category_label_en || labelZh,
        detailTitle: (profile, meta) => `${profile.name} · ${meta?.category_label_en || profile.title}`,
        chatName: (profile) => `Talk with ${profile.name_en || profile.name}`,
        chatSource: (profile) => `Method focus: ${profile.focus_tags.slice(0, 3).join(" / ")}`,
        chatIntro: (profile) => `You are now inside ${profile.name_en || profile.name}'s reasoning interface. Ask directly and the answer will start from ${profile.focus_tags.slice(0, 3).join(", ")} first.`,
        sourceLabelDeepseek: "Source: DeepSeek API",
        sourceLabelFallback: "Source: Local fallback persona"
      }
    };

    const state = {
      celebrities: [],
      courseCatalog: null,
      activeId: null,
      activeCategory: "all",
      search: "",
      lang: (() => {
        try {
          return localStorage.getItem("digital-sage-home-lang") || "zh";
        } catch (err) {
          return "zh";
        }
      })()
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
      brandTagline: document.getElementById("brandTagline"),
      statusLabel: document.getElementById("statusLabel"),
      langButtons: Array.from(document.querySelectorAll(".lang-button[data-lang]")),
      heroAccent: document.getElementById("heroAccent"),
      heroTitle: document.getElementById("heroTitle"),
      heroBody: document.getElementById("heroBody"),
      proofPills: [0, 1, 2, 3].map((index) => document.getElementById(`proofPill${index}`)),
      heroActionFilm: document.getElementById("heroActionFilm"),
      heroActionChat: document.getElementById("heroActionChat"),
      heroStatLabel0: document.getElementById("heroStatLabel0"),
      heroStatLabel1: document.getElementById("heroStatLabel1"),
      heroStatLabel2: document.getElementById("heroStatLabel2"),
      heroStatBody1: document.getElementById("heroStatBody1"),
      heroStatBody2: document.getElementById("heroStatBody2"),
      quickstartEyebrow: document.getElementById("quickstartEyebrow"),
      quickstartTitle: document.getElementById("quickstartTitle"),
      quickstartBody: document.getElementById("quickstartBody"),
      promptCardSmall: [0, 1, 2].map((index) => document.getElementById(`promptCard${index}Small`)),
      promptCardStrong: [0, 1, 2].map((index) => document.getElementById(`promptCard${index}Strong`)),
      promptCardBody: [0, 1, 2].map((index) => document.getElementById(`promptCard${index}Body`)),
      curriculumTitle: document.getElementById("curriculumTitle"),
      curriculumBody: document.getElementById("curriculumBody"),
      curriculumLink: document.getElementById("curriculumLink"),
      curriculumDomainsEyebrow: document.getElementById("curriculumDomainsEyebrow"),
      courseSpotlightLoading: document.getElementById("courseSpotlightLoading"),
      heroCount: document.getElementById("heroCount"),
      loadedCount: document.getElementById("loadedCount"),
      searchLabel: document.getElementById("searchLabel"),
      filters: document.getElementById("filters"),
      expertList: document.getElementById("expertList"),
      directoryTitle: document.getElementById("directoryTitle"),
      searchInput: document.getElementById("searchInput"),
      detailCategory: document.getElementById("detailCategory"),
      detailAvatar: document.getElementById("detailAvatar"),
      detailName: document.getElementById("detailName"),
      detailTitle: document.getElementById("detailTitle"),
      detailHeadingValues: document.getElementById("detailHeadingValues"),
      detailHeadingFramework: document.getElementById("detailHeadingFramework"),
      detailHeadingPositions: document.getElementById("detailHeadingPositions"),
      coreValues: document.getElementById("coreValues"),
      framework: document.getElementById("framework"),
      positions: document.getElementById("positions"),
      chatAvatar: document.getElementById("chatAvatar"),
      chatName: document.getElementById("chatName"),
      chatSubtitle: document.getElementById("chatSubtitle"),
      chatSource: document.getElementById("chatSource"),
      chatLog: document.getElementById("chatLog"),
      chatForm: document.getElementById("chatForm"),
      messageInput: document.getElementById("messageInput"),
      chatSubmit: document.getElementById("chatSubmit"),
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
      demoDots: document.getElementById("demoDots"),
      courseStats: document.getElementById("courseStats"),
      blueprintRail: document.getElementById("blueprintRail"),
      domainBoard: document.getElementById("domainBoard"),
      courseSpotlight: document.getElementById("courseSpotlight"),
      featuredCourses: document.getElementById("featuredCourses"),
      faqTitle: document.getElementById("faqTitle"),
      faqQ: [0, 1, 2].map((index) => document.getElementById(`faqQ${index}`)),
      faqA: [0, 1, 2].map((index) => document.getElementById(`faqA${index}`))
    };

    function copy() {
      return uiCopy[state.lang] || uiCopy.zh;
    }

    function categoryLabelFor(key) {
      return (categoryLabels[state.lang] || categoryLabels.zh)[key] || key;
    }

    function courseMetaFor(id) {
      return (state.courseCatalog?.thinkers || []).find((item) => item.id === id) || null;
    }

    function updateLoadedCount() {
      els.loadedCount.textContent = copy().loadedCount(state.celebrities.length);
    }

    function updateLanguageButtons() {
      document.body.dataset.lang = state.lang;
      els.langButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.lang === state.lang);
      });
    }

    function applyLanguage() {
      const text = copy();
      els.brandTagline.textContent = text.brandTagline;
      els.statusLabel.textContent = text.statusLabel;
      els.heroAccent.textContent = text.heroAccent;
      els.heroTitle.textContent = text.heroTitle;
      els.heroBody.textContent = text.heroBody;
      text.proofPills.forEach((value, index) => {
        if (els.proofPills[index]) els.proofPills[index].textContent = value;
      });
      els.heroActionFilm.textContent = text.heroActions[0];
      els.heroActionChat.textContent = text.heroActions[1];
      els.heroStatLabel0.textContent = text.heroStatLabels[0];
      els.heroStatLabel1.textContent = text.heroStatLabels[1];
      els.heroStatLabel2.textContent = text.heroStatLabels[2];
      els.heroStatBody1.textContent = text.heroStatBodies[1];
      els.heroStatBody2.textContent = text.heroStatBodies[2];
      els.quickstartEyebrow.textContent = text.quickstartEyebrow;
      els.quickstartTitle.textContent = text.quickstartTitle;
      els.quickstartBody.textContent = text.quickstartBody;
      text.prompts.forEach((item, index) => {
        els.promptCardSmall[index].textContent = item.small;
        els.promptCardStrong[index].textContent = item.strong;
        els.promptCardBody[index].textContent = item.body;
      });
      els.curriculumTitle.textContent = text.curriculumTitle;
      els.curriculumBody.textContent = text.curriculumBody;
      els.curriculumLink.textContent = text.curriculumLink;
      els.curriculumDomainsEyebrow.textContent = text.curriculumDomainsEyebrow;
      if (els.courseSpotlightLoading) {
        els.courseSpotlightLoading.textContent = text.courseLoading;
      }
      els.searchLabel.textContent = text.searchLabel;
      els.searchInput.placeholder = text.searchPlaceholder;
      els.directoryTitle.textContent = text.directoryTitle;
      els.detailHeadingValues.textContent = text.detailHeadings[0];
      els.detailHeadingFramework.textContent = text.detailHeadings[1];
      els.detailHeadingPositions.textContent = text.detailHeadings[2];
      els.chatSubtitle.textContent = text.chatSubtitle;
      els.chatSubmit.textContent = text.chatSubmit;
      els.messageInput.placeholder = text.chatPlaceholder;
      els.faqTitle.textContent = text.faqTitle;
      text.faq.forEach((item, index) => {
        els.faqQ[index].textContent = item.q;
        els.faqA[index].textContent = item.a;
      });
      els.demoToggle.textContent = demoState.playing ? text.demoPause : text.demoResume;
      updateLoadedCount();
      updateLanguageButtons();
      renderFilters();
      renderExpertList();
      if (state.courseCatalog) {
        renderCourseShowcase();
      } else {
        renderCourseFallback();
      }
      renderCourseSpotlight();
      if (state.activeId) {
        const profile = state.celebrities.find((item) => item.id === state.activeId);
        if (profile) {
          const meta = courseMetaFor(profile.id);
          els.detailCategory.textContent = text.detailCategory(profile.category_label, profile, meta);
          els.detailName.textContent = state.lang === "en" ? (profile.name_en || profile.name) : profile.name;
          els.detailTitle.textContent = text.detailTitle(profile, meta);
          els.chatName.textContent = text.chatName(profile);
          els.chatSource.textContent = text.chatSource(profile);
        }
      } else {
        els.detailCategory.textContent = text.detailCategoryDefault;
        els.detailName.textContent = text.detailLoadingName;
        els.detailTitle.textContent = text.detailLoadingBody;
        els.chatName.textContent = text.detailLoadingName;
        els.chatSource.textContent = text.chatSourcePreparing;
      }
    }

    function setLanguage(lang) {
      state.lang = lang === "en" ? "en" : "zh";
      try {
        localStorage.setItem("digital-sage-home-lang", state.lang);
      } catch (err) {}
      applyLanguage();
    }

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
      els.demoToggle.textContent = demoState.playing ? copy().demoPause : copy().demoResume;
    }

    function initDemo() {
      renderDemoDots();
      setDemoScene(0);
      els.demoToggle.addEventListener("click", toggleDemoPlayback);
      demoState.frame = window.requestAnimationFrame(demoTick);
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function renderCourseShowcase() {
      if (!state.courseCatalog) return;
      const english = state.lang === "en";

      const stats = state.courseCatalog.stats || {};
      els.courseStats.innerHTML = `
        <article class="curriculum-stat">
          <strong>${escapeHtml(stats.thinkers || 0)}</strong>
          <span>${english ? "minds" : "智者数量"}</span>
        </article>
        <article class="curriculum-stat">
          <strong>${escapeHtml(stats.lessons || 0)}</strong>
          <span>${english ? "lessons" : "课程总数"}</span>
        </article>
        <article class="curriculum-stat">
          <strong>${escapeHtml(stats.categories || 0)}</strong>
          <span>${english ? "domains" : "知识领域"}</span>
        </article>
      `;

      els.blueprintRail.innerHTML = (state.courseCatalog.blueprint || []).map((item) => `
        <article class="blueprint-card">
          <span class="blueprint-num">${english ? `Lesson ${escapeHtml(item.number)}` : `第${escapeHtml(item.number)}课`}</span>
          <strong>${escapeHtml(english ? (item.title_en || item.title) : item.title)}</strong>
          <p>${escapeHtml(english ? (item.focus_en || item.focus) : item.focus)}</p>
          <small>${escapeHtml(english ? (item.deliverable_en || item.deliverable) : item.deliverable)}</small>
        </article>
      `).join("");

      els.domainBoard.innerHTML = (state.courseCatalog.categories || []).map((item) => `
        <article class="domain-chip" style="--domain-accent:${escapeHtml(item.accent)}">
          <div class="domain-count">${escapeHtml(item.count)} minds</div>
          <strong>${escapeHtml(english ? (item.label_en || item.label) : item.label)}</strong>
          <p>${escapeHtml(english ? (item.theme_en || item.theme) : item.theme)}</p>
          <small>${escapeHtml(english ? (item.signal_en || item.signal) : item.signal)}</small>
        </article>
      `).join("");

      const featured = (state.courseCatalog.thinkers || []).filter((item) => item.featured).slice(0, 8);
      els.featuredCourses.innerHTML = featured.map((item) => `
        <a class="featured-card" href="${escapeHtml(item.index_url)}">
          <div class="featured-card-top">
            ${(() => {
              const celebrity = state.celebrities.find((entry) => entry.id === item.id);
              return celebrity?.avatar_url
                ? `<img src="${escapeHtml(celebrity.avatar_url)}" alt="${escapeHtml(item.name)} 卡通头像" loading="lazy">`
                : "";
            })()}
            <div>
              <strong>${escapeHtml(english ? (item.name_en || item.name) : item.name)}</strong>
              <small>${escapeHtml(english ? `${item.name} · ${item.category_label_en || item.category_label}` : item.title)}</small>
            </div>
          </div>
          <p>${escapeHtml(english ? (item.guiding_question_en || item.guiding_question || item.quote || "") : (item.guiding_question || item.quote || ""))}</p>
          <div class="featured-tags">${(item.tags || []).slice(0, 3).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}</div>
        </a>
      `).join("");
    }

    function renderCourseFallback() {
      const english = state.lang === "en";
      els.courseStats.innerHTML = `
        <article class="curriculum-stat">
          <strong>100</strong>
          <span>${english ? "curriculum loading" : "课程整理中"}</span>
        </article>
        <article class="curriculum-stat">
          <strong>10x</strong>
          <span>${english ? "shared lesson arc" : "统一课程弧线"}</span>
        </article>
        <article class="curriculum-stat">
          <strong>8</strong>
          <span>${english ? "core domains" : "核心领域"}</span>
        </article>
      `;
      els.blueprintRail.innerHTML = english
        ? '<article class="blueprint-card"><strong>Curriculum catalog is syncing</strong><p>The homepage will automatically render the full Spark 2 curriculum board once the catalog is available.</p><small>Chat on the main site is not affected.</small></article>'
        : '<article class="blueprint-card"><strong>课程目录正在同步</strong><p>主页会在课程 catalog 发布后自动拉起完整的 Spark 2 课程看板。</p><small>当前不影响主站对话能力。</small></article>';
      els.domainBoard.innerHTML = english
        ? '<article class="domain-chip"><strong>Curriculum data not fetched yet</strong><p>Enter through the conversation workbench or the full course directory first. Domain and featured mind boards will appear here after sync.</p></article>'
        : '<article class="domain-chip"><strong>课程数据暂未拉取</strong><p>请先从对话区或课程总目录进入。课程 catalog 同步完成后，这里会自动显示 8 大领域和重点人物。</p></article>';
      els.courseSpotlight.innerHTML = english
        ? '<div class="tiny">The course catalog is syncing. You can open the <a href="/courses/">full curriculum</a> now.</div>'
        : '<div class="tiny">课程 catalog 正在同步，当前可先直接进入 <a href="/courses/">课程总目录</a>。</div>';
      els.featuredCourses.innerHTML = "";
    }

    function renderCourseSpotlight() {
      if (!state.courseCatalog || !state.activeId) return;
      const english = state.lang === "en";
      const thinker = (state.courseCatalog.thinkers || []).find((item) => item.id === state.activeId);
      if (!thinker) {
        els.courseSpotlight.innerHTML = english
          ? `<div class="tiny">This thinker&#39;s curriculum is still being prepared.</div>`
          : '<div class="tiny">该人物的课程还在整理中。</div>';
        return;
      }
      const celebrity = state.celebrities.find((entry) => entry.id === thinker.id);
      const avatarUrl = celebrity?.avatar_url || "";

      const firstLessons = (thinker.lessons || []).slice(0, 3);
      els.courseSpotlight.innerHTML = `
        <div class="spotlight-top">
          ${avatarUrl ? `<img class="spotlight-avatar" src="${escapeHtml(avatarUrl)}" alt="${escapeHtml(thinker.name)} 头像" loading="lazy">` : ""}
          <div>
            <div class="eyebrow">Active Curriculum</div>
            <strong>${escapeHtml(english ? `${thinker.name_en || thinker.name} · 10-lesson arc` : `${thinker.name} 的 10 课学习路径`)}</strong>
            <p>${escapeHtml(english ? `${thinker.category_label_en || thinker.category_label} · ${thinker.name}` : `${thinker.category_label} · ${thinker.title}`)}</p>
          </div>
        </div>
        <div class="spotlight-tags">${(thinker.tags || []).slice(0, 3).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}</div>
        <p>${escapeHtml(english ? (thinker.guiding_question_en || thinker.guiding_question || thinker.quote || "") : (thinker.guiding_question || thinker.quote || ""))}</p>
        <div class="spotlight-lessons">
          ${firstLessons.map((lesson) => `
            <article class="spotlight-lesson">
              <small>${english ? `Lesson ${escapeHtml(lesson.number)} · ${escapeHtml(lesson.focus_en || lesson.focus || "")}` : `第${escapeHtml(lesson.number)}课 · ${escapeHtml(lesson.focus || "")}`}</small>
              <strong>${escapeHtml(english ? (lesson.title_en || lesson.title) : lesson.title)}</strong>
              <p>${escapeHtml(english ? (lesson.deliverable_en || lesson.deliverable || lesson.subtitle_en || lesson.subtitle || "") : (lesson.deliverable || lesson.subtitle || ""))}</p>
            </article>
          `).join("")}
        </div>
        <div class="spotlight-actions">
          <a class="primary" href="${escapeHtml(thinker.index_url)}">${english ? `Open ${escapeHtml(thinker.name_en || thinker.name)} curriculum` : `进入 ${escapeHtml(thinker.name)} 课程`}</a>
          <a class="secondary" href="/courses/">${english ? "Browse all 100 minds" : "看 100 位总目录"}</a>
        </div>
      `;
    }

    function renderFilters() {
      els.filters.innerHTML = "";
      Object.entries(categoryLabels[state.lang] || categoryLabels.zh).forEach(([key, label]) => {
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
        empty.textContent = copy().emptySearch;
        els.expertList.appendChild(empty);
        return;
      }

      if (!items.some((item) => item.id === state.activeId)) {
        state.activeId = items[0].id;
        selectCelebrity(state.activeId);
      }

      items.forEach((item) => {
        const meta = courseMetaFor(item.id);
        const primaryName = state.lang === "en" ? (item.name_en || item.name) : item.name;
        const secondaryLine = state.lang === "en"
          ? `${item.name} · ${meta?.category_label_en || item.title}`
          : `${item.name_en} · ${item.title}`;
        const card = document.createElement("button");
        card.type = "button";
        card.className = "expert-card" + (item.id === state.activeId ? " active" : "");
        card.innerHTML = `
          <img class="expert-avatar" src="${item.avatar_url}" alt="${item.name} 卡通头像" loading="lazy">
          <div class="expert-card-body">
            <strong>${primaryName}</strong>
            <small>${secondaryLine}</small>
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
      const meta = courseMetaFor(id);
      const text = copy();

      els.detailCategory.textContent = text.detailCategory(profile.category_label, profile, meta);
      els.detailAvatar.src = profile.avatar_url;
      els.detailAvatar.alt = `${profile.name} 卡通头像`;
      els.detailName.textContent = state.lang === "en" ? (profile.name_en || profile.name) : profile.name;
      els.detailTitle.textContent = text.detailTitle(profile, meta);
      els.chatAvatar.src = profile.avatar_url;
      els.chatAvatar.alt = `${profile.name} 聊天头像`;
      els.chatName.textContent = text.chatName(profile);
      els.chatSource.textContent = text.chatSource(profile);

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
      renderCourseSpotlight();

      els.chatLog.innerHTML = "";
      addBubble("ai", text.chatIntro(profile));
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
      const [celebRes, courseRes] = await Promise.allSettled([
        fetch("/api/celebrities"),
        fetch("/courses/assets/course-catalog.json"),
      ]);

      state.celebrities = celebRes.status === "fulfilled" ? await celebRes.value.json() : [];
      if (courseRes.status === "fulfilled" && courseRes.value.ok) {
        state.courseCatalog = await courseRes.value.json();
        renderCourseShowcase();
      } else {
        renderCourseFallback();
      }

      els.heroCount.textContent = String(state.celebrities.length);
      updateLoadedCount();
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
      els.chatSource.textContent = copy().chatGenerating;

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
      els.chatSource.textContent = data.source === "deepseek" ? copy().sourceLabelDeepseek : copy().sourceLabelFallback;
    });

    els.langButtons.forEach((button) => {
      button.addEventListener("click", () => setLanguage(button.dataset.lang));
    });

    applyLanguage();
    initDemo();
    bootstrap();
  </script>
</body>
</html>"""
    return shell.replace("__DEMO_SCENES_JSON__", json.dumps(DEMO_SCENES, ensure_ascii=False))


def _build_growth_shell() -> str:
    pack = GROWTH_CAMPAIGN_PACK

    def card(title: str, body: str, meta: str = "", class_name: str = "card") -> str:
        meta_html = f'<p class="meta">{escape(meta)}</p>' if meta else ""
        return (
            f'<article class="{class_name}">'
            f"<h3>{escape(title)}</h3>"
            f"{meta_html}"
            f"<p>{escape(body)}</p>"
            "</article>"
        )

    pricing_cards = "".join(
        (
            '<article class="price-card">'
            f"<span>{escape(item['unit'])}</span>"
            f"<h3>{escape(item['name'])}</h3>"
            f"<strong>{escape(item['price'])}</strong>"
            f"<p>{escape(item['best_for'])}</p>"
            "</article>"
        )
        for item in pack["pricing"]
    )
    funnel_cards = "".join(
        card(item["stage"], item["goal"], " / ".join(item["channels"]), "card funnel-card")
        + f'<div class="cta-line">{escape(item["cta"])}</div>'
        for item in pack["funnel"]
    )
    xhs_cards = "".join(
        (
            '<article class="script-card">'
            f"<div class=\"platform\">小红书</div><h3>{escape(item['title'])}</h3>"
            f"<p><b>封面：</b>{escape(item['cover'])}</p>"
            f"<p><b>开头：</b>{escape(item['hook'])}</p>"
            f"<p>{escape(item['body'])}</p>"
            f"<p class=\"tags\">{escape(' '.join(item['tags']))}</p>"
            f"<button data-copy=\"{escape(item['title'] + chr(10) + item['hook'] + chr(10) + item['body'] + chr(10) + ' '.join(item['tags']) + chr(10) + item['cta'])}\">复制笔记</button>"
            "</article>"
        )
        for item in pack["xiaohongshu"]
    )
    douyin_cards = "".join(
        (
            '<article class="script-card">'
            f"<div class=\"platform\">抖音 · {escape(item['duration'])}</div><h3>{escape(item['title'])}</h3>"
            f"<p><b>前 3 秒：</b>{escape(item['hook'])}</p>"
            f"<ol>{''.join(f'<li>{escape(shot)}</li>' for shot in item['shots'])}</ol>"
            f"<p><b>旁白：</b>{escape(item['voiceover'])}</p>"
            f"<p><b>CTA：</b>{escape(item['cta'])}</p>"
            f"<button data-copy=\"{escape(item['title'] + chr(10) + item['hook'] + chr(10) + item['voiceover'] + chr(10) + item['cta'])}\">复制脚本</button>"
            "</article>"
        )
        for item in pack["douyin"]
    )
    human_cards = "".join(
        (
            '<article class="human-card">'
            f"<h3>{escape(item['sage'])}</h3>"
            f"<p><b>视觉：</b>{escape(item['avatar_direction'])}</p>"
            f"<blockquote>{escape(item['opening'])}</blockquote>"
            f"<p><b>主打场景：</b>{escape(item['use_case'])}</p>"
            f"<button data-copy=\"{escape(item['sage'] + chr(10) + item['avatar_direction'] + chr(10) + item['opening'] + chr(10) + item['use_case'])}\">复制数字人设定</button>"
            "</article>"
        )
        for item in pack["digital_humans"]
    )
    calendar_rows = "".join(
        (
            "<tr>"
            f"<td>{escape(item['day'])}</td>"
            f"<td>{escape(item['channel'])}</td>"
            f"<td>{escape(item['asset'])}</td>"
            f"<td>{escape(item['topic'])}</td>"
            "</tr>"
        )
        for item in pack["calendar"]
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Digital Sage 增长落地控制台</title>
  <meta name="description" content="Digital Sage 的商业模式、小红书、抖音和数字人宣传控制台。">
  <link rel="canonical" href="https://www.digitalsage.cloud/growth">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Serif+SC:wght@500;600;700;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #08080b;
      --card: rgba(28, 28, 34, 0.94);
      --ink: #fafafa;
      --muted: #a1a1aa;
      --line: rgba(245, 217, 138, 0.14);
      --gold: #e2b64f;
      --gold2: #f5d98a;
      --shadow: 0 28px 80px rgba(0,0,0,.36);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: Inter, "PingFang SC", sans-serif;
      background:
        radial-gradient(circle at 16% 8%, rgba(226,182,79,.16), transparent 28%),
        radial-gradient(circle at 84% 18%, rgba(94,78,44,.24), transparent 24%),
        linear-gradient(180deg, #050506 0%, var(--bg) 44%, #0d0d10 100%);
    }}
    a {{ color: var(--gold2); text-decoration: none; }}
    .page {{ width: min(1240px, calc(100vw - 32px)); margin: 0 auto; padding: 24px 0 64px; }}
    .nav {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 0 24px; }}
    .nav strong {{ letter-spacing: .14em; text-transform: uppercase; }}
    .nav-links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .pill, button {{
      min-height: 38px;
      padding: 0 14px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--ink);
      background: rgba(255,255,255,.045);
      font: inherit;
      cursor: pointer;
    }}
    button {{ color: #17130a; background: linear-gradient(135deg, var(--gold2), var(--gold)); border: 0; font-weight: 800; }}
    .hero {{
      min-height: 520px;
      display: grid;
      place-items: center;
      text-align: center;
      padding: 56px 28px;
      border: 1px solid var(--line);
      border-radius: 34px;
      background:
        radial-gradient(circle at 70% 18%, rgba(245,217,138,.13), transparent 30%),
        linear-gradient(145deg, rgba(24,24,29,.98), rgba(12,12,15,.96));
      box-shadow: var(--shadow);
    }}
    .eyebrow {{ color: var(--gold2); font-size: .78rem; font-weight: 800; letter-spacing: .18em; text-transform: uppercase; }}
    h1, h2, h3 {{ font-family: "Noto Serif SC", serif; }}
    h1 {{ max-width: 920px; margin: 16px auto; font-size: clamp(2.7rem, 7vw, 5.8rem); line-height: 1.02; letter-spacing: -.06em; }}
    .hero p {{ max-width: 820px; margin: 0 auto; color: var(--muted); line-height: 1.85; font-size: 1.05rem; }}
    .hero-actions {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; margin-top: 28px; }}
    .primary {{ color: #17130a; background: linear-gradient(135deg, var(--gold2), var(--gold)); }}
    section {{ margin-top: 28px; }}
    .section-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: end; margin-bottom: 14px; }}
    .section-head h2 {{ margin: 8px 0 0; font-size: clamp(1.7rem, 3vw, 2.7rem); }}
    .section-head p {{ color: var(--muted); line-height: 1.75; max-width: 620px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 14px; }}
    .card, .price-card, .script-card, .human-card, .table-card {{
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--card);
      box-shadow: var(--shadow);
      padding: 20px;
    }}
    .card h3, .price-card h3, .script-card h3, .human-card h3 {{ margin: 0 0 10px; font-size: 1.22rem; }}
    .card p, .price-card p, .script-card p, .human-card p, li {{ color: var(--muted); line-height: 1.72; }}
    .meta, .platform, .price-card span, .tags {{ color: var(--gold2); font-size: .78rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
    .price-card strong {{ display: block; margin: 12px 0; color: var(--gold2); font-size: 2rem; }}
    .cta-line {{ margin: -10px 0 14px; padding: 0 20px 18px; color: var(--gold2); }}
    blockquote {{ margin: 12px 0; padding-left: 14px; border-left: 3px solid var(--gold); color: var(--ink); line-height: 1.8; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 14px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--gold2); }}
    td {{ color: var(--muted); }}
    .toast {{ position: fixed; right: 18px; bottom: 18px; display: none; padding: 12px 14px; border-radius: 14px; color: #17130a; background: var(--gold2); font-weight: 800; }}
    @media (max-width: 760px) {{
      .nav, .section-head {{ align-items: flex-start; flex-direction: column; }}
      .hero {{ min-height: auto; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <nav class="nav">
      <strong>Digital Sage Growth</strong>
      <div class="nav-links">
        <a class="pill" href="/">主站首页</a>
        <a class="pill" href="/courses/">课程总目录</a>
        <a class="pill" href="/api/growth-campaigns">JSON 数据</a>
      </div>
    </nav>

    <header class="hero">
      <div>
        <div class="eyebrow">Launch Console</div>
        <h1>实际落地：把 100 位智者做成可收费、可传播、可复用的增长飞轮。</h1>
        <p>这不是一份静态方案，而是上线可访问的增长控制台：收费模型、转化漏斗、小红书笔记、抖音短视频、数字人分身脚本、7 天冷启动排期都已经结构化，可以直接复制执行。</p>
        <div class="hero-actions">
          <a class="pill primary" href="#pricing">查看收费模型</a>
          <a class="pill" href="#xiaohongshu">复制小红书笔记</a>
          <a class="pill" href="#douyin">复制抖音脚本</a>
          <a class="pill" href="#digital-human">数字人宣传</a>
        </div>
      </div>
    </header>

    <section id="pricing">
      <div class="section-head">
        <div><div class="eyebrow">Business Model</div><h2>现金流设计</h2></div>
        <p>先用免费文字试用降低门槛，再把用户导向语音、视频和记忆订阅。价格用于冷启动验证，后续可按转化率调整。</p>
      </div>
      <div class="grid">{pricing_cards}</div>
    </section>

    <section>
      <div class="section-head">
        <div><div class="eyebrow">Funnel</div><h2>从内容种草到付费通话</h2></div>
        <p>每条内容都只服务一个目的：让用户带着真实问题进入产品，而不是只看完一个 AI 概念。</p>
      </div>
      <div class="grid">{funnel_cards}</div>
    </section>

    <section id="xiaohongshu">
      <div class="section-head">
        <div><div class="eyebrow">Xiaohongshu</div><h2>小红书种草笔记</h2></div>
        <p>小红书主打信任与收藏，内容要像真实使用体验，避免硬广腔。每条都保留封面、开头、正文、标签和 CTA。</p>
      </div>
      <div class="grid">{xhs_cards}</div>
    </section>

    <section id="douyin">
      <div class="section-head">
        <div><div class="eyebrow">Douyin</div><h2>抖音短视频脚本</h2></div>
        <p>抖音主打强钩子与高密度信息，前 3 秒必须出现冲突、问题或反差，再快速展示产品如何产生答案。</p>
      </div>
      <div class="grid">{douyin_cards}</div>
    </section>

    <section id="digital-human">
      <div class="section-head">
        <div><div class="eyebrow">Digital Human</div><h2>数字人分身宣传</h2></div>
        <p>每个数字人都绑定一个高频问题场景，方便后续接入视频生成、直播切片、电话桥接和课程导流。</p>
      </div>
      <div class="grid">{human_cards}</div>
    </section>

    <section>
      <div class="section-head">
        <div><div class="eyebrow">7-Day Launch</div><h2>冷启动排期</h2></div>
        <p>先跑一周，观察点击、收藏、私信、免费试用、付费预约五个指标。不要一开始就追求全渠道完美。</p>
      </div>
      <div class="table-card">
        <table>
          <thead><tr><th>日期</th><th>渠道</th><th>素材</th><th>主题</th></tr></thead>
          <tbody>{calendar_rows}</tbody>
        </table>
      </div>
    </section>
  </div>
  <div class="toast" id="toast">已复制</div>
  <script>
    const toast = document.getElementById("toast");
    document.querySelectorAll("[data-copy]").forEach((button) => {{
      button.addEventListener("click", async () => {{
        await navigator.clipboard.writeText(button.dataset.copy || "");
        toast.style.display = "block";
        window.setTimeout(() => toast.style.display = "none", 1200);
      }});
    }});
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return _build_shell()


@app.get("/growth", response_class=HTMLResponse)
async def growth_console() -> str:
    return _build_growth_shell()


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
        "llm_provider": LLM_PROVIDER_LABEL,
        "llm_base": LLM_API_BASE,
        "llm_primary_model": LLM_PRIMARY_MODEL,
        "llm_fallback_model": LLM_FALLBACK_MODEL,
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
    response, source = await _call_deepseek(
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
    response, source = await _call_deepseek(
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


@app.get("/api/growth-campaigns")
async def get_growth_campaigns() -> dict:
    return {
        "product": "Digital Sage",
        "domain": "https://www.digitalsage.cloud",
        "status": "launch-ready",
        "campaign_pack": GROWTH_CAMPAIGN_PACK,
    }


@app.get("/courses.html", response_class=HTMLResponse)
async def courses_page():
    courses_html = BASE_DIR / "docs/courses.html"
    if courses_html.exists():
        return courses_html.read_text(encoding="utf-8")
    return "<h1>Course list not found</h1>"


if __name__ == "__main__":
    import uvicorn

    print("智者 Digital Sage 启动中...")
    uvicorn.run(app, host="0.0.0.0", port=8103)
