#!/usr/bin/env python3
"""Generate beautiful SVG course cards for 100 Digital Sage sages."""

import json
import re
import os

# Read data
with open("/root/digital-sage/docs/courses/summaries.json", "r", encoding="utf-8") as f:
    data = json.load(f)

output_dir = "/root/digital-sage/docs/courses/images"
os.makedirs(output_dir, exist_ok=True)

# Category definitions based on core values keywords
CATEGORIES = {
    "business": {
        "label": "商业投资",
        "color": "#f59e0b",
        "icon": "📈",
        "keywords": ["长期主义", "资源配置", "复利", "飞轮"]
    },
    "tech": {
        "label": "科技创新",
        "color": "#3b82f6",
        "icon": "⚡",
        "keywords": ["第一性原理", "系统思维", "算力", "平台"]
    },
    "science": {
        "label": "科学探索",
        "color": "#8b5cf6",
        "icon": "🔬",
        "keywords": ["证据优先", "可证伪性"]
    },
    "medical": {
        "label": "医学健康",
        "color": "#10b981",
        "icon": "🏥",
        "keywords": ["循证医学", "预防优先"]
    },
    "philosophy": {
        "label": "哲学思想",
        "color": "#ec4899",
        "icon": "📜",
        "keywords": ["定义先行", "价值排序"]
    },
    "design": {
        "label": "设计艺术",
        "color": "#f97316",
        "icon": "🎨",
        "keywords": ["少即是多", "形式服从体验", "作品诚实", "长期打磨"]
    },
    "governance": {
        "label": "政治治理",
        "color": "#06b6d4",
        "icon": "🏛️",
        "keywords": ["系统治理", "现实主义"]
    }
}


def parse_fields(text):
    """Extract 核心领域 and 经典语录 from the text."""
    domain = ""
    quote = ""
    
    m = re.search(r"他的核心领域是(.+?)。", text)
    if m:
        domain = m.group(1).strip()
    
    m = re.search(r"他的经典语录是[：:](.+?)。", text)
    if m:
        quote = m.group(1).strip()
    
    return domain, quote


def detect_category(text):
    """Detect category based on keywords in the text."""
    best_cat = "business"
    best_score = 0
    for cat_id, cat_info in CATEGORIES.items():
        score = sum(1 for kw in cat_info["keywords"] if kw in text)
        if score > best_score:
            best_score = score
            best_cat = cat_id
    return best_cat


def wrap_text(text, max_chars):
    """Simple line wrapping for SVG text."""
    lines = []
    current = ""
    for ch in text:
        current += ch
        if len(current) >= max_chars:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


def generate_svg(cid, name, title, domain, quote, category):
    """Generate a beautiful SVG card."""
    cat = CATEGORIES[category]
    cat_label = cat["label"]
    cat_color = cat["color"]
    cat_icon = cat["icon"]
    
    # Wrap quote for display (Chinese chars are wide)
    quote_lines = wrap_text(quote, 16)
    
    # Build domain tag pills
    domain_tags = [d.strip() for d in domain.split("、")]
    
    # Calculate positions
    svg_width = 400
    svg_height = 600
    
    # Build domain tags SVG
    tag_x = 40
    tag_y = 310
    tags_svg = ""
    for i, tag in enumerate(domain_tags):
        tw = len(tag) * 16 + 24
        if tag_x + tw > svg_width - 40:
            tag_x = 40
            tag_y += 38
        tags_svg += f'''<rect x="{tag_x}" y="{tag_y}" width="{tw}" height="28" rx="14" fill="none" stroke="{cat_color}" stroke-width="1" opacity="0.5"/>
    <text x="{tag_x + tw/2}" y="{tag_y + 19}" text-anchor="middle" fill="{cat_color}" font-size="13" font-family="'Noto Sans SC', 'PingFang SC', sans-serif">{tag}</text>'''
        tag_x += tw + 10

    # Quote lines
    quote_y_start = tag_y + 70
    quote_svg = ""
    for i, line in enumerate(quote_lines):
        y = quote_y_start + i * 28
        quote_svg += f'''<text x="{svg_width/2}" y="{y}" text-anchor="middle" fill="#e2e8f0" font-size="16" font-family="'Noto Sans SC', 'PingFang SC', 'STKaiti', serif" font-style="italic" opacity="0.9">"{line}"</text>
    '''

    # Decorative elements
    total_quote_height = len(quote_lines) * 28
    quote_end_y = quote_y_start + total_quote_height + 30
    
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">
  <defs>
    <linearGradient id="bg_{cid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="gold_{cid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fbbf24"/>
      <stop offset="50%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
    <linearGradient id="accent_{cid}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{cat_color}" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="{cat_color}" stop-opacity="0.2"/>
    </linearGradient>
    <filter id="glow_{cid}" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="clip_{cid}">
      <rect x="0" y="0" width="{svg_width}" height="{svg_height}" rx="16"/>
    </clipPath>
  </defs>

  <!-- Background -->
  <rect width="{svg_width}" height="{svg_height}" rx="16" fill="url(#bg_{cid})"/>
  
  <!-- Decorative top bar -->
  <rect x="0" y="0" width="{svg_width}" height="4" fill="url(#gold_{cid})" rx="0"/>
  
  <!-- Subtle corner decoration -->
  <circle cx="380" cy="40" r="60" fill="{cat_color}" opacity="0.03"/>
  <circle cx="380" cy="40" r="40" fill="{cat_color}" opacity="0.05"/>
  <circle cx="380" cy="40" r="20" fill="{cat_color}" opacity="0.08"/>
  
  <!-- Left accent line -->
  <rect x="24" y="80" width="3" height="80" rx="2" fill="url(#gold_{cid})" opacity="0.6"/>
  
  <!-- Category icon circle -->
  <circle cx="60" cy="60" r="28" fill="{cat_color}" opacity="0.15"/>
  <text x="60" y="70" text-anchor="middle" font-size="28">{cat_icon}</text>
  
  <!-- Category label -->
  <rect x="100" y="42" width="{len(cat_label) * 14 + 20}" height="26" rx="13" fill="{cat_color}" opacity="0.2"/>
  <text x="{100 + (len(cat_label) * 14 + 20)/2}" y="60" text-anchor="middle" fill="{cat_color}" font-size="13" font-family="'Noto Sans SC', 'PingFang SC', sans-serif" font-weight="500">{cat_label}</text>
  
  <!-- Sage Name -->
  <text x="40" y="120" fill="#fbbf24" font-size="32" font-family="'Noto Sans SC', 'PingFang SC', sans-serif" font-weight="700">{name}</text>
  
  <!-- Title -->
  <text x="40" y="155" fill="#94a3b8" font-size="16" font-family="'Noto Sans SC', 'PingFang SC', sans-serif">{title}</text>
  
  <!-- Divider line -->
  <line x1="40" y1="175" x2="{svg_width - 40}" y2="175" stroke="#334155" stroke-width="1"/>
  
  <!-- Digital Sage Brand -->
  <text x="40" y="210" fill="#64748b" font-size="11" font-family="'Noto Sans SC', 'PingFang SC', sans-serif" letter-spacing="2">DIGITAL SAGE 智者课程</text>
  
  <!-- Section: Core Domain -->
  <text x="40" y="250" fill="#fbbf24" font-size="13" font-family="'Noto Sans SC', 'PingFang SC', sans-serif" font-weight="600">◆ 核心领域</text>
  
  <!-- Domain tags -->
  {tags_svg}
  
  <!-- Section: Quote -->
  <text x="40" y="{quote_y_start - 28}" fill="#fbbf24" font-size="13" font-family="'Noto Sans SC', 'PingFang SC', sans-serif" font-weight="600">◆ 经典语录</text>
  
  <!-- Quote marks -->
  <text x="35" y="{quote_y_start + 8}" fill="#fbbf24" font-size="40" font-family="Georgia, serif" opacity="0.4">"</text>
  
  <!-- Quote text -->
  {quote_svg}
  
  <!-- Closing quote -->
  <text x="{svg_width - 55}" y="{quote_end_y - 18}" fill="#fbbf24" font-size="40" font-family="Georgia, serif" opacity="0.4">"</text>
  
  <!-- Bottom decorative area -->
  <line x1="40" y1="{svg_height - 100}" x2="{svg_width - 40}" y2="{svg_height - 100}" stroke="#334155" stroke-width="1"/>
  
  <!-- Bottom brand -->
  <text x="{svg_width/2}" y="{svg_height - 65}" text-anchor="middle" fill="#475569" font-size="12" font-family="'Noto Sans SC', 'PingFang SC', sans-serif" letter-spacing="1">与智者对话 · 体验思维的力量</text>
  
  <!-- Digital Sage logo text -->
  <text x="{svg_width/2}" y="{svg_height - 38}" text-anchor="middle" fill="#fbbf24" font-size="14" font-family="Georgia, serif" font-weight="700" letter-spacing="3" opacity="0.7">DIGITAL SAGE</text>
  
  <!-- Bottom gold bar -->
  <rect x="0" y="{svg_height - 4}" width="{svg_width}" height="4" fill="url(#gold_{cid})" rx="0"/>
  
  <!-- Subtle grid pattern overlay -->
  <rect x="0" y="0" width="{svg_width}" height="{svg_height}" rx="16" fill="none" stroke="#1e293b" stroke-width="0.5" opacity="0.3"/>
</svg>'''
    
    return svg


# Process all entries
count = 0
for cid, info in data.items():
    name = info["name"]
    title = info["title"]
    text = info["text"]
    
    domain, quote = parse_fields(text)
    category = detect_category(text)
    
    svg_content = generate_svg(cid, name, title, domain, quote, category)
    
    filepath = os.path.join(output_dir, f"{cid}.svg")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    count += 1
    print(f"[{count:3d}] ✓ {cid}.svg — {name} ({CATEGORIES[category]['label']})")

print(f"\n✅ Done! Generated {count} SVG cards in {output_dir}")
