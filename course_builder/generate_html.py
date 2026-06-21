#!/usr/bin/env python3
"""
Digital Sage Course HTML Generator
Converts 100 markdown course files into beautiful interactive HTML pages.
"""
import os, re, json, random
from pathlib import Path

BASE = Path(os.path.expanduser("~/Desktop/OPC/digital-sage"))
SRC = BASE / "docs/courses"  # markdown source
OUT = BASE / "docs_courses"   # HTML output

# Category metadata for UI
CATEGORIES = {
    "business": {"icon": "💼", "label": "商业领袖", "color": "#e2b64f", "bg": "rgba(226,182,79,0.1)"},
    "technology": {"icon": "⚡", "label": "科技思想家", "color": "#00d4ff", "bg": "rgba(0,212,255,0.1)"},
    "science": {"icon": "🔬", "label": "科学家", "color": "#7cff6b", "bg": "rgba(124,255,107,0.1)"},
    "medical": {"icon": "🏥", "label": "医学专家", "color": "#ff6b8a", "bg": "rgba(255,107,138,0.1)"},
    "philosophy": {"icon": "🧠", "label": "思想家", "color": "#c084fc", "bg": "rgba(192,132,252,0.1)"},
    "culture": {"icon": "🎨", "label": "文化创作者", "color": "#f97316", "bg": "rgba(249,115,22,0.1)"},
    "policy": {"icon": "🏛️", "label": "公共治理", "color": "#38bdf8", "bg": "rgba(56,189,248,0.1)"},
    "design": {"icon": "✏️", "label": "设计大师", "color": "#f472b6", "bg": "rgba(244,114,182,0.1)"},
}

DIFFICULTY_MAP = {
    "science": 4, "medical": 4, "philosophy": 5, "policy": 4,
    "business": 3, "technology": 3, "design": 3, "culture": 2,
}

HEADER = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — Digital Sage 思想课程</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #0a0a14;
  --surface: #12122a;
  --card: #1a1a3e;
  --text: #e0e0f0;
  --muted: #8888aa;
  --accent: {accent};
  --accent-bg: {accent_bg};
  --gold: #e2b64f;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Noto Sans SC',sans-serif; background:var(--bg); color:var(--text); line-height:1.7; }}
.container {{ max-width:900px; margin:0 auto; padding:20px; }}

/* Hero */
.hero {{ background:linear-gradient(135deg, {accent_bg} 0%, var(--bg) 100%); border:1px solid {accent}33; border-radius:20px; padding:40px 30px; margin:30px 0; position:relative; overflow:hidden; }}
.hero::before {{ content:''; position:absolute; top:-50%; right:-20%; width:300px; height:300px; background:radial-gradient(circle, {accent}15 0%, transparent 70%); }}
.hero .category {{ display:inline-block; background:{accent}22; color:{accent}; padding:4px 14px; border-radius:20px; font-size:13px; margin-bottom:16px; }}
.hero h1 {{ font-size:2.2em; font-weight:700; margin:8px 0; position:relative; }}
.hero .subtitle {{ color:var(--muted); font-size:1.1em; }}
.hero .quote {{ margin-top:20px; padding:16px 20px; background:var(--card); border-left:3px solid var(--accent); border-radius:0 12px 12px 0; font-style:italic; color:var(--gold); }}

/* Meta bar */
.meta {{ display:flex; gap:20px; flex-wrap:wrap; margin:24px 0; }}
.meta-item {{ background:var(--card); padding:12px 20px; border-radius:12px; }}
.meta-item .label {{ font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:1px; }}
.meta-item .value {{ font-size:15px; font-weight:500; margin-top:2px; }}

/* Stars for difficulty */
.stars {{ color:var(--accent); letter-spacing:2px; }}

/* Section */
.section {{ background:var(--surface); border-radius:16px; padding:30px; margin:24px 0; border:1px solid #ffffff08; }}
.section h2 {{ font-size:1.5em; margin-bottom:20px; color:{accent}; }}
.section h3 {{ font-size:1.1em; color:var(--gold); margin:20px 0 12px; }}

/* Values grid */
.values {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(250px,1fr)); gap:14px; }}
.value-card {{ background:var(--card); padding:18px; border-radius:12px; border-left:3px solid var(--accent); }}
.value-card .num {{ font-size:12px; color:{accent}; }}

/* Positions */
.position-item {{ padding:10px 0; border-bottom:1px solid #ffffff08; }}
.position-item .key {{ color:{accent}; font-weight:500; }}

/* Framework steps */
.framework-steps {{ counter-reset:step; }}
.framework-steps .step {{ padding:14px 18px; margin:8px 0; background:var(--card); border-radius:10px; position:relative; padding-left:50px; }}
.framework-steps .step::before {{ counter-increment:step; content:counter(step); position:absolute; left:16px; top:14px; width:24px; height:24px; background:{accent}33; color:{accent}; border-radius:50%; text-align:center; line-height:24px; font-size:13px; font-weight:700; }}

/* Cases */
.case {{ background:var(--card); padding:20px; border-radius:12px; margin:12px 0; }}
.case .case-title {{ font-weight:600; color:var(--gold); margin-bottom:10px; }}
.case .lesson {{ color:var(--accent); margin-top:8px; }}

/* Learning path */
.path-stage {{ background:var(--card); padding:18px 20px; border-radius:10px; margin:10px 0; }}
.path-stage .stage-header {{ font-weight:600; color:var(--accent); }}

/* Exercises */
.exercise-group {{ margin:16px 0; }}
.exercise-group h4 {{ color:var(--accent); margin-bottom:8px; }}
.exercise-group li {{ margin:6px 0; padding-left:8px; color:var(--muted); }}

/* Prompt box */
.prompt-box {{ background:#0d0d1a; border:1px solid {accent}22; border-radius:10px; padding:16px; margin:10px 0; }}
.prompt-box code {{ color:#7cff6b; font-size:13px; white-space:pre-wrap; }}

/* SVG container */
.svg-container {{ background:var(--card); border-radius:14px; padding:20px; margin:16px 0; text-align:center; }}
.svg-container svg {{ max-width:100%; }}

/* Connections */
.connection {{ display:inline-block; background:{accent}15; color:{accent}; padding:6px 14px; border-radius:20px; margin:4px; font-size:13px; }}

/* Footer */
footer {{ text-align:center; padding:40px 20px; color:var(--muted); font-size:13px; border-top:1px solid #ffffff08; margin-top:40px; }}
footer a {{ color:var(--accent); text-decoration:none; }}

/* Responsive */
@media(max-width:600px) {{
  .hero h1 {{ font-size:1.5em; }}
  .meta {{ flex-direction:column; gap:8px; }}
  .container {{ padding:12px; }}
}}
</style>
</head>
<body>
<div class="container">
'''

FOOTER = '''</div>
<footer>
  <p>Digital Sage — 与 100 位智者对话 | <a href="../courses.html">课程列表</a> | <a href="/">首页</a></p>
  <p style="margin-top:8px">© 2026 Digital Sage. 思想的力量超越时空。</p>
</footer>
</body>
</html>
'''


def parse_md(path):
    """Parse a markdown course file into structured data."""
    text = path.read_text()
    
    # Title
    title_m = re.search(r'# 📚 (.+?)—', text)
    name = title_m.group(1).strip() if title_m else "Unknown"
    
    # Subtitle line
    sub_m = re.search(r'> (.+?) \| 分类：(.+?)\n> 核心领域：(.+)', text)
    title = sub_m.group(1).strip() if sub_m else ""
    cat_label = sub_m.group(2).strip() if sub_m else ""
    focus_str = sub_m.group(3).strip() if sub_m else ""
    focus_tags = [t.strip() for t in focus_str.replace("，", ",").split(",") if t.strip()]
    
    # English name from "英文名" field
    en_m = re.search(r'\*\*英文名\*\*：(.+)', text)
    name_en = en_m.group(1).strip() if en_m else name
    
    # Signature quote
    quote_m = re.search(r'### 经典语录\n> (.+)', text)
    signature = quote_m.group(1).strip() if quote_m else ""
    
    # Category from label
    category = "business"
    for cat_id, cat_data in CATEGORIES.items():
        if cat_data["label"] == cat_label:
            category = cat_id
            break
    
    # Core values
    values_section = re.search(r'### 核心价值观\n(.*?)(?=\n###|\n---)', text, re.DOTALL)
    values = []
    if values_section:
        for line in values_section.group(1).strip().split('\n'):
            m = re.match(r'\d+\.\s*(.+)', line.strip())
            if m: values.append(m.group(1))
    
    # Positions
    positions_section = re.search(r'### 关键立场\n(.*?)(?=\n###|\n---)', text, re.DOTALL)
    positions = []
    if positions_section:
        for line in positions_section.group(1).strip().split('\n'):
            m = re.match(r'- \*\*(.+?)\*\*：(.+)', line.strip())
            if m: positions.append({"key": m.group(1), "value": m.group(2)})
    
    # Decision framework
    framework_section = re.search(r'### 决策框架\n(.*?)(?=\n###|\n---)', text, re.DOTALL)
    framework = []
    if framework_section:
        for line in framework_section.group(1).strip().split('\n'):
            m = re.match(r'- \*\*step(\d+)\*\*：(.+)', line.strip())
            if m: framework.append(m.group(2))
    
    # Speaking style
    style_section = re.search(r'### 说话风格\n(.*?)(?=\n###|\n---)', text, re.DOTALL)
    style = {}
    if style_section:
        for line in style_section.group(1).strip().split('\n'):
            m = re.match(r'- \*\*(.+?)\*\*：(.+)', line.strip())
            if m: style[m.group(1)] = m.group(2)
    
    # Experience cases
    cases_section = re.search(r'### 经验案例\n(.*?)(?=\n---)', text, re.DOTALL)
    cases = []
    if cases_section:
        case_blocks = re.split(r'\*\*案例(\d+)：(.+?)\*\*', cases_section.group(1))
        for i in range(1, len(case_blocks), 3):
            if i+2 < len(case_blocks):
                cases.append({
                    "title": case_blocks[i+1].strip(),
                    "lesson": re.search(r'教训：(.+)', case_blocks[i+2] if i+2 < len(case_blocks) else ""),
                    "outcome": re.search(r'结果：(.+)', case_blocks[i+2] if i+2 < len(case_blocks) else ""),
                })
    
    # Learning path stages
    path_stages = []
    for stage_match in re.finditer(r'### 第(\d+)阶段：(.+?)（(.+?)）\n(.*?)(?=\n###|\n---|\Z)', text, re.DOTALL):
        items = [s.strip()[2:] for s in stage_match.group(4).strip().split('\n') if s.strip().startswith(('1.', '2.', '3.'))]
        path_stages.append({
            "name": stage_match.group(2),
            "duration": stage_match.group(3),
            "items": items,
        })
    
    # Exercises
    exercises = {}
    ex_sections = {
        "concept": r'### 概念理解\n(.*?)(?=\n###)',
        "application": r'### 应用练习\n(.*?)(?=\n###)',
        "critical": r'### 思辨练习\n(.*?)(?=\n---)',
    }
    for key, pattern in ex_sections.items():
        m = re.search(pattern, text, re.DOTALL)
        if m:
            items = []
            for line in m.group(1).strip().split('\n'):
                item_m = re.match(r'\d+\.\s*(.+)', line.strip())
                if item_m: items.append(item_m.group(1))
            exercises[key] = items
    
    # Chat prompts
    prompts = {}
    prompt_sections = {
        "intro": r'### 入门对话\n```\n(.*?)```',
        "advanced": r'### 进阶对话\n```\n(.*?)```',
        "deep": r'### 深度对话\n```\n(.*?)```',
    }
    for key, pattern in prompt_sections.items():
        m = re.search(pattern, text, re.DOTALL)
        if m: prompts[key] = m.group(1).strip()
    
    return {
        "name": name, "name_en": name_en, "title": title, "category": category,
        "cat_label": cat_label, "focus_tags": focus_tags, "signature": signature,
        "values": values, "positions": positions, "framework": framework,
        "style": style, "cases": cases, "path_stages": path_stages,
        "exercises": exercises, "prompts": prompts,
    }


def generate_svg_mindmap(data):
    """Generate SVG thought map for the expert."""
    name = data["name"]
    values = data["values"][:4]
    accent = CATEGORIES[data["category"]]["color"]
    
    svg = f'''<svg viewBox="0 0 600 380" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <!-- Title -->
  <text x="300" y="35" text-anchor="middle" fill="{accent}" font-size="18" font-weight="700">{name} 思想地图</text>
  <!-- Center node -->
  <circle cx="300" cy="180" r="55" fill="{accent}22" stroke="{accent}" stroke-width="2" filter="url(#glow)"/>
  <text x="300" y="175" text-anchor="middle" fill="#fff" font-size="13" font-weight="600">{name}</text>
  <text x="300" y="195" text-anchor="middle" fill="{accent}" font-size="11">{data["cat_label"]}</text>
  <!-- Branch values -->
'''
    positions = [
        (140, 130), (460, 130), (140, 250), (460, 250)
    ]
    for i, (val, (cx, cy)) in enumerate(zip(values, positions)):
        label = val[:12] + "…" if len(val) > 12 else val
        svg += f'''
  <line x1="300" y1="180" x2="{cx}" y2="{cy}" stroke="{accent}44" stroke-width="1.5"/>
  <rect x="{cx-65}" y="{cy-18}" width="130" height="36" rx="10" fill="{accent}15" stroke="{accent}55" stroke-width="1"/>
  <text x="{cx}" y="{cy+5}" text-anchor="middle" fill="#ddd" font-size="11">{label}</text>
'''
    svg += '\n</svg>'
    return svg


def generate_html(data):
    """Generate complete course HTML page."""
    cats = CATEGORIES[data["category"]]
    diff = DIFFICULTY_MAP.get(data["category"], 3)
    
    html = HEADER.format(
        name=data["name"],
        accent=cats["color"],
        accent_bg=cats["bg"],
    )
    
    # Hero
    html += f'''
<div class="hero">
  <span class="category">{cats["icon"]} {cats["label"]}</span>
  <h1>{data["name"]}</h1>
  <p class="subtitle">{data["title"]} · {data["name_en"]}</p>
  <div class="quote">"{data['signature']}"</div>
</div>

<!-- Meta Bar -->
<div class="meta">
  <div class="meta-item">
    <div class="label">难度</div>
    <div class="value"><span class="stars">{"★" * diff}{"☆" * (5 - diff)}</span></div>
  </div>
  <div class="meta-item">
    <div class="label">核心领域</div>
    <div class="value">{", ".join(data["focus_tags"])}</div>
  </div>
  <div class="meta-item">
    <div class="label">课程时长</div>
    <div class="value">约 {"5-7" if diff <= 3 else "7-14"} 天</div>
  </div>
  <div class="meta-item">
    <div class="label">前置要求</div>
    <div class="value">{"无" if diff <= 2 else "基础阅读能力" if diff <= 4 else "建议先修相关基础课程"}</div>
  </div>
</div>
'''

    # SVG Mindmap
    svg = generate_svg_mindmap(data)
    html += f'<div class="svg-container">{svg}</div>\n'
    
    # Section 1: Core Values
    if data["values"]:
        html += '<div class="section"><h2>🧬 核心价值观</h2><div class="values">\n'
        for i, v in enumerate(data["values"], 1):
            html += f'<div class="value-card"><div class="num">0{i}</div>{v}</div>\n'
        html += '</div></div>\n'
    
    # Section 2: Decision Framework
    if data["framework"]:
        html += '<div class="section"><h2>🎯 决策框架</h2><div class="framework-steps">\n'
        for s in data["framework"]:
            html += f'<div class="step">{s}</div>\n'
        html += '</div></div>\n'
    
    # Section 3: Key Positions
    if data["positions"]:
        html += '<div class="section"><h2>💡 关键立场</h2>\n'
        for p in data["positions"]:
            html += f'<div class="position-item"><span class="key">{p["key"]}</span>：{p["value"]}</div>\n'
        html += '</div>\n'
    
    # Section 4: Experience Cases
    if data["cases"]:
        html += '<div class="section"><h2>📖 经验案例</h2>\n'
        for c in data["cases"]:
            html += f'<div class="case">\n'
            html += f'<div class="case-title">{c["title"]}</div>\n'
            html += f'<p>{c["lesson"].group(1) if c["lesson"] else ""}</p>\n'
            html += f'<p class="lesson">结果：{c["outcome"].group(1) if c["outcome"] else ""}</p>\n'
            html += '</div>\n'
        html += '</div>\n'
    
    # Section 5: Learning Path
    if data["path_stages"]:
        html += '<div class="section"><h2>🛤️ 学习路径</h2>\n'
        for stage in data["path_stages"]:
            html += f'<div class="path-stage">\n'
            html += f'<div class="stage-header">{stage["name"]} <span style="color:var(--muted)">({stage["duration"]})</span></div>\n'
            html += '<ul style="margin-top:8px;padding-left:20px;">\n'
            for item in stage["items"]:
                html += f'<li style="margin:4px 0;color:var(--muted)">{item}</li>\n'
            html += '</ul></div>\n'
        html += '</div>\n'
    
    # Section 6: Exercises
    if data["exercises"]:
        html += '<div class="section"><h2>📝 练习与思考</h2>\n'
        labels = {"concept": "概念理解", "application": "应用练习", "critical": "思辨练习"}
        for key, label in labels.items():
            if key in data["exercises"] and data["exercises"][key]:
                html += f'<div class="exercise-group"><h4>{label}</h4><ul>\n'
                for item in data["exercises"][key]:
                    html += f'<li>{item}</li>\n'
                html += '</ul></div>\n'
        html += '</div>\n'
    
    # Section 7: Digital Sage Prompts
    if data["prompts"]:
        html += '<div class="section"><h2>🤖 与智者对话</h2>\n'
        prompt_labels = {"intro": "入门对话", "advanced": "进阶对话", "deep": "深度对话"}
        for key, label in prompt_labels.items():
            if key in data["prompts"] and data["prompts"][key]:
                html += f'<h3>{label}</h3>\n'
                html += f'<div class="prompt-box"><code>{data["prompts"][key]}</code></div>\n'
        html += '</div>\n'
    
    # Section 8: Connections (generated from same category)
    html += '<div class="section"><h2>🔗 思想连接</h2>\n'
    html += f'<p style="color:var(--muted);margin-bottom:12px">同一领域的其他智者：</p>\n'
    html += f'<span class="connection">{data["cat_label"]}领域</span>\n'
    html += '<span class="connection">跨领域启发</span>\n'
    html += '</div>\n'
    
    html += FOOTER
    return html


def generate_course_list(all_data):
    """Generate courses.html listing page."""
    cats = CATEGORIES
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Digital Sage — 100位智者课程</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Noto Sans SC',sans-serif; background:#0a0a14; color:#e0e0f0; line-height:1.6; }
.container { max-width:1200px; margin:0 auto; padding:20px; }

header { text-align:center; padding:50px 20px 30px; }
header h1 { font-size:2.5em; background:linear-gradient(135deg, #e2b64f, #00d4ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
header p { color:#8888aa; margin-top:8px; font-size:1.1em; }

.category-section { margin:30px 0; }
.cat-header { display:flex; align-items:center; gap:12px; margin-bottom:16px; padding-bottom:8px; border-bottom:1px solid #ffffff08; }
.cat-header .cat-icon { font-size:1.3em; }
.cat-header h2 { font-size:1.3em; }
.cat-header .count { color:#8888aa; font-size:0.9em; }

.course-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(280px,1fr)); gap:14px; }
.course-card { background:#12122a; border:1px solid #ffffff08; border-radius:14px; padding:18px; transition:all 0.2s; cursor:pointer; text-decoration:none; color:inherit; display:block; }
.course-card:hover { border-color:var(--card-accent); transform:translateY(-2px); background:#1a1a3e; }
.course-card h3 { font-size:1.05em; margin-bottom:4px; }
.course-card .title { color:#8888aa; font-size:0.85em; margin-bottom:6px; }
.course-card .tags { display:flex; gap:6px; flex-wrap:wrap; margin-top:10px; }
.course-card .tag { font-size:11px; padding:2px 10px; border-radius:10px; background:var(--card-accent)15; color:var(--card-accent); }
.course-card .diff { font-size:12px; color:#8888aa; margin-top:8px; }

.search-bar { margin:20px auto; max-width:500px; }
.search-bar input { width:100%; padding:14px 20px; background:#1a1a3e; border:1px solid #ffffff15; border-radius:30px; color:#e0e0f0; font-size:16px; outline:none; }
.search-bar input:focus { border-color:#e2b64f; }

footer { text-align:center; padding:40px 20px; color:#8888aa; font-size:13px; border-top:1px solid #ffffff08; margin-top:40px; }
footer a { color:#00d4ff; }
</style>
</head>
<body>
<div class="container">
<header>
  <h1>Digital Sage 思想课程</h1>
  <p>与100位历史智者对话 · 系统化思维训练</p>
</header>

<div class="search-bar">
  <input type="text" id="search" placeholder="🔍 搜索智者姓名、领域或关键词..." oninput="filterCourses()">
</div>
'''
    
    # Group by category
    grouped = {}
    for d in all_data:
        cat = d["category"]
        if cat not in grouped: grouped[cat] = []
        grouped[cat].append(d)
    
    for cat_id in ["philosophy", "science", "business", "technology", "design", "policy", "medical", "culture"]:
        if cat_id not in grouped: continue
        cd = cats[cat_id]
        items = grouped[cat_id]
        
        html += f'''
<div class="category-section" data-category="{cd['label']}">
  <div class="cat-header">
    <span class="cat-icon">{cd['icon']}</span>
    <h2 style="color:{cd['color']}">{cd['label']}</h2>
    <span class="count">{len(items)} 位智者</span>
  </div>
  <div class="course-grid">
'''
        for d in sorted(items, key=lambda x: x['name']):
            diff = DIFFICULTY_MAP.get(cat_id, 3)
            stars = "★" * diff + "☆" * (5 - diff)
            tags_html = "".join(f'<span class="tag">{t}</span>' for t in d['focus_tags'][:3])
            html += f'''
    <a class="course-card" href="courses/{d['file_id']}.html" style="--card-accent:{cd['color']}">
      <h3>{cd['icon']} {d['name']}</h3>
      <div class="title">{d['title']}</div>
      <div class="tags">{tags_html}</div>
      <div class="diff">{stars}</div>
    </a>
'''
        html += '  </div>\n</div>\n'
    
    html += '''
</div>
<script>
function filterCourses() {
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.course-card').forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = text.includes(q) ? '' : 'none';
  });
  // Show/hide category sections
  document.querySelectorAll('.category-section').forEach(sec => {
    const visible = sec.querySelectorAll('.course-card[style*="display"]').length < sec.querySelectorAll('.course-card').length;
    const anyVisible = Array.from(sec.querySelectorAll('.course-card')).some(c => c.style.display !== 'none');
    sec.style.display = anyVisible ? '' : 'none';
  });
}
</script>
<footer>
  <p>Digital Sage — 与 100 位智者对话 | <a href="/">首页</a> | <a href="/pricing.html">定价</a></p>
  <p>© 2026 Digital Sage</p>
</footer>
</body>
</html>
'''
    return html


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    
    md_files = sorted(SRC.glob("*.md"))
    md_files = [f for f in md_files if f.stem not in ("README", "audio")]
    
    all_data = []
    
    for mdf in md_files:
        try:
            data = parse_md(mdf)
            data["file_id"] = mdf.stem
            all_data.append(data)
            
            # Generate HTML
            html = generate_html(data)
            out_path = OUT / f"{mdf.stem}.html"
            out_path.write_text(html)
            
            print(f"  ✓ {data['name']} ({data['cat_label']})")
        except Exception as e:
            print(f"  ✗ {mdf.stem}: {e}")
    
    # Generate course listing
    list_html = generate_course_list(all_data)
    (BASE / "docs/courses.html").write_text(list_html)
    
    print(f"\n{'='*50}")
    print(f"Generated {len(all_data)} course pages")
    print(f"Course list: docs/courses.html")
    print(f"Course pages: docs/courses_html/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
