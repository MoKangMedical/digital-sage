"""
Digital Sage — Streamlit 对话界面
与100位历史智者跨时空对话
"""

import json
import os
import random
import time
from pathlib import Path

import streamlit as st

# ── 页面配置 ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Digital Sage — 与智者对话",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 加载智者数据 ──────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent.parent / "data" / "philosophers.json"


@st.cache_data
def load_philosophers() -> list[dict]:
    """加载智者数据，缓存以提高性能"""
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


philosophers = load_philosophers()
sage_names = [p["name"] for p in philosophers]
sage_name_map = {p["name"]: p for p in philosophers}

# ── 自定义样式 ──────────────────────────────────────────────────────
st.markdown(
    """
<style>
    .sage-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .sage-card h3 { color: white; margin-bottom: 0.5rem; }
    .sage-card .era { opacity: 0.85; font-size: 0.9rem; }
    .quote-box {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem 1.5rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
        font-style: italic;
    }
    .chat-user {
        background: #e3f2fd;
        padding: 0.8rem 1.2rem;
        border-radius: 12px 12px 0 12px;
        margin: 0.5rem 0;
    }
    .chat-sage {
        background: #f3e5f5;
        padding: 0.8rem 1.2rem;
        border-radius: 12px 12px 12px 0;
        margin: 0.5rem 0;
    }
    .debate-header {
        text-align: center;
        font-size: 1.2rem;
        color: #667eea;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ── 辅助函数 ──────────────────────────────────────────────────────────
def render_sage_card(sage: dict) -> None:
    """渲染智者信息卡片"""
    name_cn = sage.get("name_cn", sage["name"])
    era = sage.get("era", "")
    country = sage.get("country", "")
    core_ideas = sage.get("core_ideas", [])
    quotes = sage.get("famous_quotes", [])
    traits = sage.get("personality_traits", [])
    style = sage.get("speaking_style", "")

    st.markdown(
        f"""
<div class="sage-card">
    <h3>🏛️ {name_cn} ({sage['name']})</h3>
    <p class="era">📅 {era} · 🌍 {country}</p>
    <p><strong>核心思想：</strong>{'、'.join(core_ideas)}</p>
    <p><strong>性格特质：</strong>{'、'.join(traits)}</p>
    <p><strong>说话风格：</strong>{style}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    if quotes:
        quote = random.choice(quotes)
        st.markdown(
            f'<div class="quote-box">💬 "{quote}"</div>',
            unsafe_allow_html=True,
        )


def simulate_sage_response(sage: dict, user_message: str, chat_history: list) -> str:
    """模拟智者的回复（基于其性格和说话风格）

    在实际部署中，这里应接入 LLM API（如 OpenAI、Claude），
    将智者的背景信息作为 system prompt 来生成回复。
    """
    name_cn = sage.get("name_cn", sage["name"])
    style = sage.get("speaking_style", "深思熟虑地回答")
    traits = sage.get("personality_traits", [])
    quotes = sage.get("famous_quotes", [])
    core_ideas = sage.get("core_ideas", [])

    # 模拟回复模板（演示用，实际应接入 LLM）
    templates = [
        f"作为{name_cn}，我认为这个问题值得深入探讨。{style}，让我从{core_ideas[0] if core_ideas else '哲学'}的角度来分析……",
        f"你提了一个好问题。{random.choice(traits)}的我，会这样思考：{user_message}的本质在于……",
        f"正如我曾说过：「{random.choice(quotes) if quotes else '思考是灵魂的对话'}」，"
        f"关于你的问题，{style}……",
    ]

    return random.choice(templates)


def simulate_debate(
    sage_a: dict, sage_b: dict, topic: str, round_num: int = 1
) -> list[dict]:
    """模拟两位智者的跨时空对话"""
    messages = []
    name_a = sage_a.get("name_cn", sage_a["name"])
    name_b = sage_b.get("name_cn", sage_b["name"])

    # 第一轮：各自阐述观点
    style_a = sage_a.get("speaking_style", "深思熟虑")
    style_b = sage_b.get("speaking_style", "深思熟虑")
    ideas_a = sage_a.get("core_ideas", ["智慧"])
    ideas_b = sage_b.get("core_ideas", ["真理"])

    messages.append(
        {
            "role": name_a,
            "content": f"关于「{topic}」，从{ideas_a[0]}的角度来看，{style_a}——我认为这需要我们首先审视前提假设。",
        }
    )
    messages.append(
        {
            "role": name_b,
            "content": f"有趣的观点。但{ideas_b[0]}告诉我们，{style_b}——或许我们应该换个角度思考这个问题。",
        }
    )

    # 后续轮次：回应对方
    for i in range(1, round_num):
        messages.append(
            {
                "role": name_a,
                "content": f"你说得有道理，但请允许我反驳——{random.choice(sage_a.get('famous_quotes', ['思考']))}，这正说明了问题所在。",
            }
        )
        messages.append(
            {
                "role": name_b,
                "content": f"我理解你的立场。不过{random.choice(sage_b.get('famous_quotes', ['真理']))}，这难道不值得我们重新考虑吗？",
            }
        )

    return messages


# ── 侧边栏 ──────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏛️ Digital Sage")
    st.markdown("与100位历史智者跨时空对话")

    mode = st.radio(
        "选择模式",
        ["💬 与智者对话", "⚔️ 跨时空对话"],
        index=0,
    )

    st.markdown("---")
    st.markdown(
        """
**使用说明**
1. 选择一位你感兴趣的智者
2. 阅读其简介和名言
3. 开始对话，提出你的问题
4. 在「跨时空对话」模式下，可让两位智者辩论
"""
    )

    st.markdown("---")
    st.markdown(f"📚 已收录 **{len(philosophers)}** 位智者")

# ── 主界面 ──────────────────────────────────────────────────────────
if mode == "💬 与智者对话":
    st.title("💬 与智者对话")
    st.markdown("选择一位智者，开始你的思想之旅")

    # 选择智者
    selected_name = st.selectbox(
        "选择智者",
        sage_names,
        format_func=lambda x: f"{sage_name_map[x].get('name_cn', x)} ({x})",
    )

    if selected_name and selected_name in sage_name_map:
        sage = sage_name_map[selected_name]

        # 显示智者信息
        col1, col2 = st.columns([1, 2])

        with col1:
            render_sage_card(sage)

        with col2:
            st.subheader("📖 智者名言")
            for quote in sage.get("famous_quotes", []):
                st.markdown(f"💬 *「{quote}」*")")

        st.markdown("---")

        # 对话界面
        st.subheader("🗨️ 开始对话")

        # 初始化聊天历史
        chat_key = f"chat_{selected_name}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        # 显示聊天历史
        for msg in st.session_state[chat_key]:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-user">🧑 **你：** {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                name_cn = sage.get("name_cn", sage["name"])
                st.markdown(
                    f'<div class="chat-sage">🏛️ **{name_cn}：** {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )

        # 用户输入
        user_input = st.chat_input(f"向{sage.get('name_cn', selected_name)}提问…")

        if user_input:
            # 添加用户消息
            st.session_state[chat_key].append({"role": "user", "content": user_input})

            # 生成智者回复
            response = simulate_sage_response(
                sage, user_input, st.session_state[chat_key]
            )
            st.session_state[chat_key].append({"role": "sage", "content": response})

            st.rerun()

        # 清空对话按钮
        if st.session_state[chat_key]:
            if st.button("🗑️ 清空对话", key=f"clear_{selected_name}"):
                st.session_state[chat_key] = []
                st.rerun()

elif mode == "⚔️ 跨时空对话":
    st.title("⚔️ 跨时空对话")
    st.markdown("选择两位智者，让他们就一个话题展开辩论")

    col1, col2 = st.columns(2)

    with col1:
        sage_a_name = st.selectbox(
            "选择智者 A",
            sage_names,
            format_func=lambda x: f"{sage_name_map[x].get('name_cn', x)} ({x})",
            key="sage_a",
        )

    with col2:
        sage_b_name = st.selectbox(
            "选择智者 B",
            sage_names,
            format_func=lambda x: f"{sage_name_map[x].get('name_cn', x)} ({x})",
            key="sage_b",
            index=min(1, len(sage_names) - 1),
        )

    if sage_a_name and sage_b_name:
        sage_a = sage_name_map[sage_a_name]
        sage_b = sage_name_map[sage_b_name]

        # 显示两位智者信息
        col1, col2 = st.columns(2)
        with col1:
            render_sage_card(sage_a)
        with col2:
            render_sage_card(sage_b)

        st.markdown("---")

        # 话题输入
        topic = st.text_input(
            "🎯 输入辩论话题",
            placeholder="例如：人性本善还是本恶？知识是天赋还是后天习得？",
        )

        rounds = st.slider("辩论轮数", 1, 5, 2)

        if topic and st.button("⚔️ 开始辩论"):
            st.markdown(
                f'<div class="debate-header">⚔️ {sage_a.get("name_cn", sage_a_name)} VS {sage_b.get("name_cn", sage_b_name)}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**话题：** {topic}")
            st.markdown("---")

            debate_messages = simulate_debate(sage_a, sage_b, topic, rounds)

            for msg in debate_messages:
                role = msg["role"]
                content = msg["content"]
                # 根据角色决定样式
                if role == sage_a.get("name_cn", sage_a_name):
                    st.markdown(
                        f'<div class="chat-sage">🏛️ **{role}：** {content}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="chat-user">🏛️ **{role}：** {content}</div>',
                        unsafe_allow_html=True,
                    )

                time.sleep(0.3)  # 模拟思考延迟

            st.success("辩论结束！以上是两位智者的观点交锋。")

# ── 页脚 ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>"
    "🏛️ Digital Sage — 与100位历史智者跨时空对话 | "
    "Built with Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
