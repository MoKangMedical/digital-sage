#!/usr/bin/env python3
"""
为 Digital Sage 生成可导出的成片 demo。
产物:
- media/demo/digital-sage-film.mp4
- media/demo/digital-sage-film.webm
- media/demo/digital-sage-film-poster.jpg
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai_engine.cartoon_avatars import render_cartoon_avatar_svg
from ai_engine.demo_story import DEMO_SCENES
from ai_engine.thought_profiles import get_profile


MEDIA_DIR = ROOT / "media" / "demo"
BUILD_DIR = MEDIA_DIR / "_build"
FRAMES_DIR = BUILD_DIR / "frames"
AUDIO_DIR = BUILD_DIR / "audio"
AVATAR_DIR = BUILD_DIR / "avatars"

WIDTH = 1600
HEIGHT = 900
FPS = 24
TRANSITION_SEC = 0.85
VOICE_NAME = "Tingting"
VOICE_RATE = "175"
NARRATION_DELAY = 0.38
SCENE_TAIL = 1.15
POSTER_SCENE_INDEX = 2

FONT_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_LATIN = "/System/Library/Fonts/SFCompact.ttf"

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
RESAMPLING = getattr(Image, "Resampling", Image)

FINAL_GRID_IDS = [
    "buffett",
    "jensen_huang",
    "steve_jobs",
    "sam_altman",
    "albert_einstein",
    "zhongnanshan",
    "confucius",
    "jony_ive",
    "lee_kuan_yew",
    "leonardo_da_vinci",
    "caodewang",
    "mark_zuckerberg",
    "marie_curie",
    "zhang_wenhong",
    "charlie_munger",
    "daniel_kahneman",
    "zaha_hadid",
    "nelson_mandela",
    "tu_youyou",
    "hayao_miyazaki",
    "bill_gates",
    "andrew_ng",
    "ada_lovelace",
    "laozi",
    "dieter_rams",
]

THEMES = {
    "nightfall": {
        "bg_top": (7, 17, 31),
        "bg_bottom": (26, 42, 70),
        "glow_a": (72, 139, 255, 155),
        "glow_b": (255, 212, 124, 80),
        "accent": (125, 178, 255),
        "accent_2": (240, 198, 114),
    },
    "constellation": {
        "bg_top": (10, 15, 40),
        "bg_bottom": (28, 31, 84),
        "glow_a": (121, 132, 255, 140),
        "glow_b": (64, 196, 255, 90),
        "accent": (146, 157, 255),
        "accent_2": (132, 218, 255),
    },
    "signal": {
        "bg_top": (9, 18, 31),
        "bg_bottom": (18, 58, 82),
        "glow_a": (34, 197, 94, 125),
        "glow_b": (56, 189, 248, 95),
        "accent": (97, 226, 149),
        "accent_2": (111, 203, 255),
    },
    "sunrise": {
        "bg_top": (49, 25, 48),
        "bg_bottom": (121, 67, 98),
        "glow_a": (244, 114, 182, 110),
        "glow_b": (255, 210, 100, 110),
        "accent": (255, 173, 218),
        "accent_2": (255, 213, 119),
    },
    "daybreak": {
        "bg_top": (24, 39, 64),
        "bg_bottom": (60, 97, 124),
        "glow_a": (147, 228, 255, 120),
        "glow_b": (255, 255, 255, 110),
        "accent": (178, 234, 255),
        "accent_2": (255, 255, 255),
    },
}


@dataclass
class SceneTiming:
    scene: dict
    clip_path: Path
    clip_duration: float
    start: float
    duration: float


def ease_out_cubic(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1 - pow(1 - value, 3)


def ease_in_out_sine(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return -(math.cos(math.pi * value) - 1) / 2


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def blend_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(lerp(a[0], b[0], t)),
        int(lerp(a[1], b[1], t)),
        int(lerp(a[2], b[2], t)),
    )


def load_font(size: int, *, latin: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_LATIN if latin else FONT_CJK
    return ImageFont.truetype(path, size)


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for char in text:
        test = current + char
        if current and text_width(draw, test, font) > max_width:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int] | tuple[int, int, int],
    max_width: int,
    line_gap: int,
) -> int:
    lines = wrap_text(draw, text, font, max_width)
    offset_y = y
    for line in lines:
        draw.text((x, offset_y), line, font=font, fill=fill)
        line_box = draw.textbbox((x, offset_y), line, font=font)
        offset_y = line_box[3] + line_gap
    return offset_y


def draw_round_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def ensure_avatar_png(celeb_id: str, size: int = 512) -> Path:
    svg_path = AVATAR_DIR / f"{celeb_id}.svg"
    png_path = AVATAR_DIR / f"{svg_path.name}.png"
    if png_path.exists():
        return png_path

    svg_path.write_text(render_cartoon_avatar_svg(celeb_id, get_profile(celeb_id)), encoding="utf-8")
    subprocess.run(
        ["qlmanage", "-t", "-s", str(size), "-o", str(AVATAR_DIR), str(svg_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return png_path


@lru_cache(maxsize=256)
def load_avatar_image(celeb_id: str, size: int = 512) -> Image.Image:
    return Image.open(ensure_avatar_png(celeb_id, size)).convert("RGBA")


def paste_avatar(base: Image.Image, celeb_id: str, *, x: int, y: int, size: int, radius: int) -> None:
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow, "RGBA")
    sdraw.rounded_rectangle((x + 4, y + 8, x + size + 4, y + size + 8), radius=radius, fill=(5, 10, 18, 82))
    base.alpha_composite(shadow)

    avatar = load_avatar_image(celeb_id, max(size * 3, 384)).copy()
    avatar = avatar.resize((size, size), RESAMPLING.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)

    clipped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    clipped.paste(avatar, (0, 0), mask)
    base.alpha_composite(clipped, (x, y))

    border = ImageDraw.Draw(base, "RGBA")
    border.rounded_rectangle((x, y, x + size, y + size), radius=radius, outline=(255, 255, 255, 108), width=2)


def create_base(theme: dict, t: float) -> Image.Image:
    base = Image.new("RGBA", (WIDTH, HEIGHT), theme["bg_top"] + (255,))
    draw = ImageDraw.Draw(base, "RGBA")

    for y in range(HEIGHT):
        blend = y / max(1, HEIGHT - 1)
        color = blend_color(theme["bg_top"], theme["bg_bottom"], blend)
        draw.line((0, y, WIDTH, y), fill=color + (255,))

    # Large atmosphere glows.
    drift = math.sin(t * 0.35) * 40
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow, "RGBA")
    gdraw.ellipse((-120 + drift, -80, 620 + drift, 580), fill=theme["glow_a"])
    gdraw.ellipse((WIDTH - 600 - drift, HEIGHT - 440, WIDTH + 120 - drift, HEIGHT + 120), fill=theme["glow_b"])
    gdraw.ellipse((WIDTH * 0.52, HEIGHT * 0.08, WIDTH * 0.92, HEIGHT * 0.42), fill=(255, 255, 255, 18))
    base = Image.alpha_composite(base, glow)

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    for idx in range(0, HEIGHT, 6):
        alpha = 9 if idx % 12 == 0 else 4
        odraw.line((0, idx, WIDTH, idx), fill=(255, 255, 255, alpha))
    base = Image.alpha_composite(base, overlay)
    return base


def progressive_text(text: str, local_t: float, voice_duration: float) -> str:
    if local_t <= NARRATION_DELAY:
        return ""
    speech_t = clamp((local_t - NARRATION_DELAY) / max(voice_duration, 0.1), 0.0, 1.0)
    count = max(1, int(len(text) * ease_out_cubic(speech_t)))
    return text[:count]


def render_common_title(
    draw: ImageDraw.ImageDraw,
    scene: dict,
    *,
    left: int,
    top: int,
) -> None:
    small = load_font(24, latin=True)
    title_font = load_font(66)
    body_font = load_font(27)
    quote_font = load_font(29)

    draw.text((left, top), scene["moment"], font=small, fill=(234, 241, 255, 185))
    end_y = draw_text_block(
        draw,
        scene["title"],
        x=left,
        y=top + 34,
        font=title_font,
        fill=(255, 255, 255),
        max_width=640,
        line_gap=10,
    )
    end_y = draw_text_block(
        draw,
        scene["body"],
        x=left,
        y=end_y + 14,
        font=body_font,
        fill=(232, 239, 251, 210),
        max_width=620,
        line_gap=10,
    )
    draw.line((left, end_y + 22, left + 50, end_y + 22), fill=(255, 255, 255, 120), width=2)
    draw_text_block(
        draw,
        scene["quote"],
        x=left + 22,
        y=end_y + 28,
        font=quote_font,
        fill=(255, 255, 255, 240),
        max_width=560,
        line_gap=8,
    )


def draw_people_tokens(
    base: Image.Image,
    draw: ImageDraw.ImageDraw,
    experts: Iterable[dict[str, str]],
    *,
    x: int,
    y: int,
    max_width: int,
) -> int:
    font = load_font(20)
    token_height = 48
    cursor_x = x
    cursor_y = y
    for expert in experts:
        name = expert["name"]
        width = max(156, int(text_width(draw, name, font) + 72))
        if cursor_x + width > max_width:
            cursor_x = x
            cursor_y += token_height + 10
        draw_round_rect(
            draw,
            (cursor_x, cursor_y, cursor_x + width, cursor_y + token_height),
            radius=24,
            fill=(24, 39, 61, 236),
            outline=(137, 178, 255, 56),
        )
        paste_avatar(base, expert["id"], x=cursor_x + 8, y=cursor_y + 8, size=32, radius=12)
        draw.text((cursor_x + 48, cursor_y + 12), name, font=font, fill=(239, 244, 255, 240))
        cursor_x += width + 10
    return cursor_y + token_height


def draw_product_window(
    base: Image.Image,
    draw: ImageDraw.ImageDraw,
    scene: dict,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    shift_y: float = 0.0,
) -> None:
    x1 = int(x)
    y1 = int(y + shift_y)
    x2 = int(x + w)
    y2 = int(y + h + shift_y)
    draw_round_rect(draw, (x1, y1, x2, y2), radius=28, fill=(10, 18, 30, 228), outline=(255, 255, 255, 26))
    draw_round_rect(draw, (x1 + 16, y1 + 16, x2 - 16, y2 - 16), radius=24, fill=(17, 28, 43, 235))

    # Traffic dots
    for idx, color in enumerate(((255, 99, 132), (255, 204, 84), (52, 211, 153))):
        dot_x = x1 + 32 + idx * 18
        draw.ellipse((dot_x, y1 + 24, dot_x + 10, y1 + 34), fill=color + (255,))

    draw.text((x1 + 110, y1 + 18), "Digital Sage", font=load_font(23, latin=True), fill=(255, 255, 255, 168))
    tokens_bottom = draw_people_tokens(base, draw, scene["experts"], x=x1 + 24, y=y1 + 58, max_width=x2 - 26)

    question_font = load_font(24)
    answer_font = load_font(22)
    question_top = tokens_bottom + 18
    question_bottom = question_top + 78
    draw_round_rect(draw, (x1 + 24, question_top, x2 - 26, question_bottom), radius=22, fill=(47, 108, 255, 226))
    draw.text((x1 + 40, question_top + 12), "用户提问", font=load_font(16, latin=True), fill=(219, 232, 255, 210))
    draw_text_block(
        draw,
        scene["question"],
        x=x1 + 40,
        y=question_top + 32,
        font=question_font,
        fill=(255, 255, 255),
        max_width=w - 90,
        line_gap=6,
    )
    answer_top = question_bottom + 16
    answer_bottom = y2 - 122
    draw_round_rect(draw, (x1 + 24, answer_top, x2 - 26, answer_bottom), radius=24, fill=(21, 34, 54, 240), outline=(129, 170, 255, 34))
    draw.text((x1 + 40, answer_top + 14), "智者回复", font=load_font(16, latin=True), fill=(187, 204, 231, 170))
    draw_text_block(
        draw,
        scene["answer"],
        x=x1 + 38,
        y=answer_top + 36,
        font=answer_font,
        fill=(241, 246, 255, 240),
        max_width=w - 82,
        line_gap=8,
    )

    draw_round_rect(draw, (x1 + 24, y2 - 110, x2 - 26, y2 - 30), radius=22, fill=(255, 255, 255, 14), outline=(255, 255, 255, 18))
    draw.text((x1 + 40, y2 - 97), scene["outcome_label"], font=load_font(18, latin=True), fill=(185, 201, 230, 175))
    draw_text_block(
        draw,
        scene["outcome"],
        x=x1 + 40,
        y=y2 - 74,
        font=load_font(29),
        fill=(255, 255, 255, 240),
        max_width=w - 88,
        line_gap=6,
    )


def draw_office_scene(base: Image.Image, draw: ImageDraw.ImageDraw, scene: dict, local_t: float, duration: float) -> None:
    fade = ease_out_cubic(min(1.0, local_t / 1.2))
    render_common_title(draw, scene, left=100, top=100)

    # Window and skyline.
    draw_round_rect(draw, (950, 88, 1490, 640), radius=32, fill=(255, 255, 255, 18), outline=(255, 255, 255, 34))
    for i in range(15):
        bx = 985 + i * 32
        bh = 120 + int((math.sin(i * 0.8 + local_t * 0.4) + 1) * 120)
        draw.rectangle((bx, 620 - bh, bx + 20, 620), fill=(255, 227, 160, 70 if i % 2 else 38))
    draw.rectangle((0, 700, WIDTH, HEIGHT), fill=(8, 13, 23, 220))
    draw.rounded_rectangle((840, 640, 1520, 770), radius=30, fill=(17, 24, 39, 255))

    # Character silhouette.
    cx = 1030
    cy = 655
    draw.ellipse((cx - 48, cy - 130, cx + 48, cy - 34), fill=(11, 15, 25, 255))
    draw.rounded_rectangle((cx - 92, cy - 44, cx + 80, cy + 120), radius=36, fill=(14, 18, 29, 255))
    draw.polygon(((cx + 66, cy + 24), (cx + 180, cy + 80), (cx + 150, cy + 108), (cx + 48, cy + 40)), fill=(13, 17, 27, 240))
    draw.rectangle((1092, 694, 1282, 716), fill=(80, 96, 126, 255))
    draw.rectangle((1136, 716, 1238, 746), fill=(39, 53, 81, 255))

    panel_shift = 80 * (1 - fade)
    draw_product_window(base, draw, scene, x=1060, y=152, w=400, h=540, shift_y=panel_shift)


def draw_constellation_scene(base: Image.Image, draw: ImageDraw.ImageDraw, scene: dict, local_t: float, duration: float) -> None:
    render_common_title(draw, scene, left=90, top=92)
    center_x, center_y = 1140, 370
    draw_round_rect(draw, (936, 216, 1388, 544), radius=30, fill=(255, 255, 255, 18), outline=(255, 255, 255, 35))
    draw.text((968, 244), "Digital Sage · Compare Perspectives", font=load_font(18, latin=True), fill=(217, 230, 255, 168))
    draw_round_rect(draw, (968, 280, 1356, 368), radius=24, fill=(47, 108, 255, 224))
    draw.text((998, 298), "核心问题", font=load_font(15, latin=True), fill=(223, 233, 255, 210))
    draw_text_block(
        draw,
        scene["question"],
        x=998,
        y=318,
        font=load_font(25),
        fill=(255, 255, 255),
        max_width=324,
        line_gap=6,
    )
    draw_round_rect(draw, (968, 392, 1356, 516), radius=24, fill=(17, 30, 48, 238), outline=(255, 255, 255, 20))
    draw.text((998, 410), "Digital Sage 归纳", font=load_font(15, latin=True), fill=(189, 204, 230, 180))
    draw_text_block(
        draw,
        scene["outcome"],
        x=998,
        y=434,
        font=load_font(28),
        fill=(244, 248, 255, 242),
        max_width=324,
        line_gap=8,
    )

    orbit_r = 235
    for idx, expert in enumerate(scene["experts"]):
        ang = local_t * 0.28 + idx * (math.pi / 2)
        px = center_x + math.cos(ang) * orbit_r
        py = center_y + math.sin(ang) * (orbit_r * 0.58)
        orb_size = 122 if idx % 2 == 0 else 112
        draw.ellipse((px - orb_size / 2, py - orb_size / 2, px + orb_size / 2, py + orb_size / 2), fill=(255, 255, 255, 24), outline=(255, 255, 255, 86), width=2)
        paste_avatar(base, expert["id"], x=int(px - 34), y=int(py - 56), size=68, radius=22)
        label_font = load_font(20)
        tw = text_width(draw, expert["name"], label_font)
        draw.text((px - tw / 2, py + 22), expert["name"], font=label_font, fill=(255, 255, 255, 245))
        draw.line((center_x, center_y, px, py), fill=(255, 255, 255, 52), width=1)


def draw_signal_scene(base: Image.Image, draw: ImageDraw.ImageDraw, scene: dict, local_t: float, duration: float) -> None:
    render_common_title(draw, scene, left=90, top=88)
    draw_product_window(base, draw, scene, x=890, y=124, w=560, h=600, shift_y=0)

    action_top = 230
    slide = 90 * (1 - ease_out_cubic(min(1.0, local_t / 1.4)))
    actions = [
        ("变量一", "现金流", (91, 226, 149)),
        ("变量二", "组织", (109, 203, 255)),
        ("变量三", "产品", (255, 211, 119)),
        ("变量四", "长期信任", (244, 174, 255)),
    ]
    for idx, (label, value, color) in enumerate(actions):
        top = action_top + idx * 88 + int(slide * (0.85 - idx * 0.12))
        draw_round_rect(draw, (870, top, 1085, top + 64), radius=20, fill=(255, 255, 255, 20), outline=(255, 255, 255, 22))
        draw.text((892, top + 12), label, font=load_font(18, latin=True), fill=(183, 198, 222, 178))
        draw.text((892, top + 32), value, font=load_font(27), fill=color + (255,))
        draw.line((1085, top + 32, 1128, top + 32), fill=(255, 255, 255, 64), width=2)


def draw_sunrise_scene(base: Image.Image, draw: ImageDraw.ImageDraw, scene: dict, local_t: float, duration: float) -> None:
    render_common_title(draw, scene, left=90, top=90)
    sun_y = 250 + 60 * math.sin(local_t * 0.25)
    draw.ellipse((1050, sun_y, 1280, sun_y + 230), fill=(255, 208, 110, 108))
    draw.rectangle((0, 686, WIDTH, HEIGHT), fill=(38, 23, 36, 220))
    draw.rectangle((960, 140, 1505, 640), fill=(255, 255, 255, 10))

    # Figure and message card.
    draw.ellipse((1020, 490, 1108, 584), fill=(18, 13, 22, 255))
    draw.rounded_rectangle((980, 560, 1142, 776), radius=44, fill=(25, 16, 29, 255))
    draw_product_window(base, draw, scene, x=1130, y=162, w=300, h=470, shift_y=0)

    note_x = 1180 + int(28 * math.sin(local_t * 0.7))
    draw_round_rect(draw, (note_x, 560, note_x + 282, 710), radius=26, fill=(255, 255, 255, 28), outline=(255, 255, 255, 30))
    draw.text((note_x + 24, 584), "团队消息", font=load_font(18, latin=True), fill=(254, 233, 200, 185))
    draw_text_block(
        draw,
        "谢谢你们再给我三个月。\n这次我们只做一件事，把它做对。",
        x=note_x + 24,
        y=612,
        font=load_font(24),
        fill=(255, 245, 236, 244),
        max_width=230,
        line_gap=10,
    )


def draw_finale_scene(base: Image.Image, draw: ImageDraw.ImageDraw, scene: dict, local_t: float, duration: float) -> None:
    for index, celeb_id in enumerate(FINAL_GRID_IDS):
        row = index // 5
        col = index % 5
        tile_x = 842 + col * 112
        tile_y = 126 + row * 104 + int(6 * math.sin(local_t * 0.8 + index * 0.22))
        draw_round_rect(draw, (tile_x - 8, tile_y - 8, tile_x + 88, tile_y + 88), radius=28, fill=(255, 255, 255, 16), outline=(255, 255, 255, 30))
        paste_avatar(base, celeb_id, x=tile_x, y=tile_y, size=72, radius=24)

    brand_font = load_font(96)
    sub_font = load_font(32)
    draw.text((90, 112), "Digital", font=brand_font, fill=(247, 251, 255))
    draw.text((90, 208), "Sage", font=brand_font, fill=(168, 229, 255))
    draw_text_block(
        draw,
        "与全球最聪明的 100 个大脑对话",
        x=92,
        y=338,
        font=load_font(42),
        fill=(255, 255, 255, 235),
        max_width=640,
        line_gap=6,
    )
    draw_text_block(
        draw,
        scene["body"],
        x=94,
        y=412,
        font=load_font(28),
        fill=(232, 241, 255, 205),
        max_width=620,
        line_gap=10,
    )
    draw_round_rect(draw, (92, 650, 570, 764), radius=28, fill=(255, 255, 255, 16), outline=(255, 255, 255, 32))
    draw.text((126, 684), scene["outcome"], font=sub_font, fill=(255, 255, 255, 245))


def render_subtitle(draw: ImageDraw.ImageDraw, scene: dict, local_t: float, voice_duration: float) -> None:
    subtitle = progressive_text(scene["narration"], local_t, voice_duration)
    if not subtitle:
        subtitle = scene["subtitle"]
    bar = (130, HEIGHT - 126, WIDTH - 130, HEIGHT - 46)
    draw_round_rect(draw, bar, radius=24, fill=(7, 12, 20, 180), outline=(255, 255, 255, 26))
    draw.text((160, HEIGHT - 105), "旁白", font=load_font(18, latin=True), fill=(176, 192, 220, 188))
    draw_text_block(
        draw,
        subtitle,
        x=228,
        y=HEIGHT - 108,
        font=load_font(27),
        fill=(255, 255, 255, 240),
        max_width=WIDTH - 390,
        line_gap=8,
    )

    # Rhythm bars
    voice_progress = clamp((local_t - NARRATION_DELAY) / max(voice_duration, 0.1), 0.0, 1.0)
    start_x = WIDTH - 250
    for idx in range(28):
        level = 12 + 18 * (0.5 + 0.5 * math.sin(local_t * 3.8 + idx * 0.9))
        alpha = 170 if idx / 28 <= voice_progress else 60
        draw.rounded_rectangle(
            (start_x + idx * 4, HEIGHT - 92 - level, start_x + idx * 4 + 2, HEIGHT - 72),
            radius=1,
            fill=(125, 191, 255, alpha),
        )


def render_scene_frame(scene_timing: SceneTiming, local_t: float) -> Image.Image:
    scene = scene_timing.scene
    theme = THEMES[scene["theme"]]
    img = create_base(theme, scene_timing.start + local_t)
    draw = ImageDraw.Draw(img, "RGBA")

    idx = DEMO_SCENES.index(scene)
    if idx == 0:
        draw_office_scene(img, draw, scene, local_t, scene_timing.duration)
    elif idx == 1:
        draw_constellation_scene(img, draw, scene, local_t, scene_timing.duration)
    elif idx == 2:
        draw_signal_scene(img, draw, scene, local_t, scene_timing.duration)
    elif idx == 3:
        draw_sunrise_scene(img, draw, scene, local_t, scene_timing.duration)
    else:
        draw_finale_scene(img, draw, scene, local_t, scene_timing.duration)

    render_subtitle(draw, scene, local_t, scene_timing.clip_duration)
    return img


def get_wave_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


def synthesize_voiceovers() -> list[SceneTiming]:
    timings: list[SceneTiming] = []
    current_start = 0.0
    for idx, scene in enumerate(DEMO_SCENES, start=1):
        raw_path = AUDIO_DIR / f"scene_{idx:02d}.aiff"
        clip_path = AUDIO_DIR / f"scene_{idx:02d}.wav"
        subprocess.run(
            [
                "say",
                "-v",
                VOICE_NAME,
                "-r",
                VOICE_RATE,
                scene["narration"],
                "-o",
                str(raw_path),
            ],
            check=True,
        )
        run_ffmpeg(
            [
                "-y",
                "-i",
                str(raw_path),
                "-ac",
                "1",
                "-ar",
                "24000",
                "-c:a",
                "pcm_s16le",
                str(clip_path),
            ]
        )
        clip_duration = get_wave_duration(clip_path)
        duration = NARRATION_DELAY + clip_duration + SCENE_TAIL
        timings.append(
            SceneTiming(
                scene=scene,
                clip_path=clip_path,
                clip_duration=clip_duration,
                start=current_start,
                duration=duration,
            )
        )
        current_start += duration
    return timings


def read_wave_pcm(path: Path) -> tuple[np.ndarray, int, int]:
    with wave.open(str(path), "rb") as audio:
        channels = audio.getnchannels()
        width = audio.getsampwidth()
        sample_rate = audio.getframerate()
        frame_count = audio.getnframes()
        raw = audio.readframes(frame_count)

    if width != 2:
        raise RuntimeError(f"暂不支持 {width} 字节采样宽度: {path}")

    data = np.frombuffer(raw, dtype="<i2").astype(np.int16)
    if channels > 1:
        data = data.reshape(-1, channels)
    else:
        data = data.reshape(-1, 1)
    return data, sample_rate, channels


def apply_audio_fade(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    fade_len = int(sample_rate * 0.025)
    if fade_len <= 0 or len(samples) < fade_len * 2:
        return samples
    ramp = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
    shaped = samples.astype(np.float32)
    shaped[:fade_len] *= ramp[:, None]
    shaped[-fade_len:] *= ramp[::-1, None]
    return shaped.astype(np.int16)


def compose_audio(timings: list[SceneTiming], output_path: Path) -> float:
    clips: list[tuple[np.ndarray, int, int]] = [read_wave_pcm(t.clip_path) for t in timings]
    sample_rate = clips[0][1]
    channels = clips[0][2]
    total_duration = timings[-1].start + timings[-1].duration
    total_samples = int(math.ceil(total_duration * sample_rate))
    timeline = np.zeros((total_samples, channels), dtype=np.int32)

    for timing, (clip, clip_rate, clip_channels) in zip(timings, clips, strict=True):
        if clip_rate != sample_rate or clip_channels != channels:
            raise RuntimeError("音轨参数不一致，无法合成。")
        clip = apply_audio_fade(clip, sample_rate)
        start_sample = int((timing.start + NARRATION_DELAY) * sample_rate)
        end_sample = start_sample + len(clip)
        timeline[start_sample:end_sample] += clip.astype(np.int32)

    timeline = np.clip(timeline, -32768, 32767).astype(np.int16)
    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(timeline.tobytes())
    return total_duration


def render_frames(timings: list[SceneTiming], total_duration: float) -> None:
    total_frames = int(math.ceil(total_duration * FPS))
    starts = [item.start for item in timings]
    poster_frame = None

    for frame_idx in range(total_frames):
        t = frame_idx / FPS
        scene_idx = max(i for i, start in enumerate(starts) if start <= t)
        timing = timings[scene_idx]
        local_t = t - timing.start
        frame = render_scene_frame(timing, local_t)

        if scene_idx < len(timings) - 1:
            remaining = timing.duration - local_t
            if remaining <= TRANSITION_SEC:
                mix = ease_in_out_sine(1 - (remaining / TRANSITION_SEC))
                next_timing = timings[scene_idx + 1]
                next_frame = render_scene_frame(next_timing, local_t=max(0.0, local_t - (timing.duration - TRANSITION_SEC)))
                frame = Image.blend(frame, next_frame, mix)

        if scene_idx == POSTER_SCENE_INDEX and poster_frame is None and local_t > timing.duration * 0.45:
            poster_frame = frame.copy()

        frame.convert("RGB").save(FRAMES_DIR / f"frame_{frame_idx:04d}.jpg", quality=96, subsampling=0)

    if poster_frame is None:
        poster_frame = render_scene_frame(timings[0], 0.6)
    poster_frame.convert("RGB").save(MEDIA_DIR / "digital-sage-film-poster.jpg", quality=95, subsampling=0)


def run_ffmpeg(args: list[str]) -> None:
    subprocess.run([FFMPEG, *args], check=True)


def encode_video(audio_path: Path) -> None:
    mp4_path = MEDIA_DIR / "digital-sage-film.mp4"
    webm_path = MEDIA_DIR / "digital-sage-film.webm"

    run_ffmpeg(
        [
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(FRAMES_DIR / "frame_%04d.jpg"),
            "-i",
            str(audio_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "high",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(mp4_path),
        ]
    )

    run_ffmpeg(
        [
            "-y",
            "-i",
            str(mp4_path),
            "-c:v",
            "libvpx-vp9",
            "-crf",
            "32",
            "-b:v",
            "0",
            "-row-mt",
            "1",
            "-c:a",
            "libopus",
            "-b:a",
            "160k",
            str(webm_path),
        ]
    )


def prepare_dirs() -> None:
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    prepare_dirs()
    timings = synthesize_voiceovers()
    audio_path = BUILD_DIR / "digital-sage-voiceover.wav"
    total_duration = compose_audio(timings, audio_path)
    render_frames(timings, total_duration)
    encode_video(audio_path)
    print("Generated:")
    print(MEDIA_DIR / "digital-sage-film.mp4")
    print(MEDIA_DIR / "digital-sage-film.webm")
    print(MEDIA_DIR / "digital-sage-film-poster.jpg")


if __name__ == "__main__":
    main()
