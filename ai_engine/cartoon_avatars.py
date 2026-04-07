"""
Digital Sage 程序化卡通头像生成器。

目标：
- 为 100 位人物统一提供更接近本人的临时卡通头像
- 不依赖外部图片资源
- 通过更细的人物特征，让首页、分镜与成片共享同一套视觉角色
"""

from __future__ import annotations

import hashlib
from html import escape


PALETTES = [
    {
        "bg": ("#dceefe", "#f7fbff"),
        "skin": "#f2d1bf",
        "hair": "#34241d",
        "outfit": "#203a5f",
        "accent": "#6fa9ff",
    },
    {
        "bg": ("#ede6ff", "#fbf8ff"),
        "skin": "#e9c2aa",
        "hair": "#1d1721",
        "outfit": "#473a74",
        "accent": "#a084ff",
    },
    {
        "bg": ("#dff7ee", "#f7fffb"),
        "skin": "#f0c7a2",
        "hair": "#2c261f",
        "outfit": "#1d4c47",
        "accent": "#42c8a0",
    },
    {
        "bg": ("#fff0da", "#fffaf3"),
        "skin": "#f3d6c6",
        "hair": "#4c2d21",
        "outfit": "#63422f",
        "accent": "#ffb55c",
    },
    {
        "bg": ("#e2f5ff", "#f9fdff"),
        "skin": "#deb89e",
        "hair": "#232e3b",
        "outfit": "#204762",
        "accent": "#48bdf0",
    },
    {
        "bg": ("#f6e4dc", "#fff7f2"),
        "skin": "#e6b494",
        "hair": "#291f1c",
        "outfit": "#5a3140",
        "accent": "#ff8b8b",
    },
]

CATEGORY_OVERRIDES = {
    "business": {"outfit": "suit", "shape": "calm", "face_shape": "oval", "eye_style": "focused"},
    "technology": {"outfit": "hoodie", "shape": "curious", "face_shape": "square", "eye_style": "sharp"},
    "science": {"outfit": "lab", "shape": "calm", "face_shape": "long", "eye_style": "soft"},
    "medical": {"outfit": "coat", "shape": "warm", "face_shape": "oval", "eye_style": "warm"},
    "philosophy": {"outfit": "robe", "shape": "wise", "face_shape": "long", "eye_style": "soft"},
    "culture": {"outfit": "soft", "shape": "playful", "face_shape": "heart", "eye_style": "smile"},
    "policy": {"outfit": "formal", "shape": "steady", "face_shape": "square", "eye_style": "focused"},
    "design": {"outfit": "turtleneck", "shape": "cool", "face_shape": "heart", "eye_style": "sharp"},
}

ICONIC_OVERRIDES = {
    "buffett": {"hair_style": "side", "hair_color": "#f7f3f0", "glasses": "round", "age": "senior", "face_shape": "round", "mouth_style": "gentle"},
    "musk": {"hair_style": "swept_back", "hair_color": "#3a2e28", "face_shape": "square", "eye_style": "sharp", "mouth_style": "serious"},
    "zhangyiming": {"hair_style": "short", "hair_color": "#231e1b", "face_shape": "long", "mouth_style": "gentle"},
    "jensen_huang": {"hair_style": "swept", "hair_color": "#1a1a1a", "outfit": "leather", "face_shape": "heart", "eye_style": "sharp"},
    "bezos": {"hair_style": "bald", "hair_color": "#2e261f", "face_shape": "round", "mouth_style": "serious"},
    "duan_yongping": {"hair_style": "short", "hair_color": "#2a221f", "face_shape": "round", "eye_style": "warm"},
    "caodewang": {"hair_style": "short", "hair_color": "#e8e8e8", "glasses": "square", "age": "senior", "face_shape": "square", "mouth_style": "gentle"},
    "lei_jun": {"hair_style": "short", "hair_color": "#1e1b20", "face_shape": "round", "mouth_style": "gentle"},
    "ren_zhengfei": {"hair_style": "short", "hair_color": "#ececec", "age": "senior", "face_shape": "square", "eye_style": "focused"},
    "satya_nadella": {"hair_style": "bald", "beard": "light", "face_shape": "oval", "mouth_style": "gentle"},
    "reed_hastings": {"hair_style": "side", "hair_color": "#c7c0b8", "age": "senior", "face_shape": "long", "mouth_style": "serious"},
    "ray_dalio": {"hair_style": "thin", "hair_color": "#f2f2f2", "age": "senior", "face_shape": "oval", "eye_style": "warm", "mouth_style": "gentle"},
    "indra_nooyi": {"hair_style": "shoulder", "hair_color": "#2f2521", "outfit": "formal", "face_shape": "heart", "accessory": "earrings", "eye_style": "focused"},
    "sheryl_sandberg": {"hair_style": "wave_long", "hair_color": "#5b4032", "outfit": "formal", "face_shape": "heart", "accessory": "earrings", "mouth_style": "gentle"},
    "howard_schultz": {"hair_style": "swept", "hair_color": "#c6c1bc", "age": "senior", "face_shape": "oval", "mouth_style": "serious"},
    "jack_ma": {"hair_style": "short", "hair_color": "#181612", "face_shape": "long", "eye_style": "sharp"},
    "wang_xing": {"hair_style": "short", "hair_color": "#1e1b18", "face_shape": "long", "mouth_style": "serious"},
    "masayoshi_son": {"hair_style": "bald", "glasses": "round", "face_shape": "round", "mouth_style": "gentle"},
    "peter_thiel": {"hair_style": "recede", "hair_color": "#a28570", "face_shape": "long", "eye_style": "sharp", "mouth_style": "serious"},
    "steve_jobs": {"hair_style": "close", "hair_color": "#1f1f1f", "outfit": "turtleneck", "face_shape": "long", "eye_style": "sharp", "mouth_style": "serious"},
    "bill_gates": {"hair_style": "side", "hair_color": "#b6b0a8", "glasses": "square", "age": "senior", "face_shape": "round", "mouth_style": "gentle"},
    "sam_altman": {"hair_style": "side", "hair_color": "#6b4b3b", "face_shape": "long", "mouth_style": "serious"},
    "li_feifei": {"hair_style": "bob", "hair_color": "#1b1a20", "face_shape": "heart", "accessory": "earrings", "eye_style": "warm"},
    "andrew_ng": {"hair_style": "short", "hair_color": "#27221c", "glasses": "round", "face_shape": "round", "mouth_style": "gentle"},
    "andrej_karpathy": {"hair_style": "curtain", "hair_color": "#5f4030", "beard": "light", "face_shape": "long", "eye_style": "sharp"},
    "demis_hassabis": {"hair_style": "short", "hair_color": "#1b1a1a", "beard": "light", "face_shape": "round", "mouth_style": "serious"},
    "ilya_sutskever": {"hair_style": "curly_short", "hair_color": "#6f513c", "beard": "full", "face_shape": "round", "eye_style": "soft"},
    "larry_page": {"hair_style": "close", "hair_color": "#6f4d35", "face_shape": "long", "mouth_style": "serious"},
    "sergey_brin": {"hair_style": "curtain", "hair_color": "#2f261f", "beard": "light", "face_shape": "round", "eye_style": "curious"},
    "mark_zuckerberg": {"hair_style": "short", "hair_color": "#8b5a3f", "outfit": "hoodie", "face_shape": "round", "mouth_style": "serious"},
    "tim_cook": {"hair_style": "close", "hair_color": "#ececec", "glasses": "square", "age": "senior", "face_shape": "long", "mouth_style": "gentle"},
    "tim_berners_lee": {"hair_style": "thin", "hair_color": "#f1f1f1", "age": "senior", "face_shape": "long", "eye_style": "warm"},
    "susan_wojcicki": {"hair_style": "shoulder", "hair_color": "#50392d", "face_shape": "heart", "accessory": "earrings", "mouth_style": "gentle"},
    "linus_torvalds": {"hair_style": "recede", "hair_color": "#7f5e43", "glasses": "round", "beard": "light", "face_shape": "round", "mouth_style": "serious"},
    "ada_lovelace": {"hair_style": "wave_long", "hair_color": "#2b1f1c", "outfit": "soft", "face_shape": "heart", "accessory": "earrings", "mouth_style": "gentle"},
    "alan_turing": {"hair_style": "side", "hair_color": "#2a211d", "outfit": "formal", "face_shape": "long", "eye_style": "focused"},
    "richard_feynman": {"hair_style": "swept", "hair_color": "#1d1818", "face_shape": "long", "eye_style": "curious", "mouth_style": "smirk"},
    "albert_einstein": {"hair_style": "wild", "hair_color": "#f4f4f4", "mustache": "full", "age": "senior", "face_shape": "round", "eye_style": "warm"},
    "isaac_newton": {"hair_style": "long", "hair_color": "#d8d8d8", "outfit": "robe", "face_shape": "long", "mouth_style": "serious"},
    "stephen_hawking": {"hair_style": "thin", "hair_color": "#bdbdbd", "glasses": "square", "age": "senior", "face_shape": "oval", "mouth_style": "gentle"},
    "marie_curie": {"hair_style": "bun", "hair_color": "#4a3b36", "face_shape": "long", "mouth_style": "serious"},
    "jane_goodall": {"hair_style": "bun", "hair_color": "#efefef", "age": "senior", "face_shape": "heart", "mouth_style": "gentle"},
    "yang_zhenning": {"hair_style": "thin", "hair_color": "#f1f1f1", "age": "senior", "face_shape": "long", "eye_style": "warm"},
    "yan_ning": {"hair_style": "pixie", "hair_color": "#1c1b20", "face_shape": "heart", "eye_style": "sharp", "mouth_style": "serious"},
    "zhang_feng": {"hair_style": "short", "hair_color": "#1b1a17", "glasses": "round", "face_shape": "oval", "mouth_style": "gentle"},
    "tu_youyou": {"hair_style": "short", "hair_color": "#efefef", "age": "senior", "face_shape": "heart", "mouth_style": "gentle"},
    "rosalind_franklin": {"hair_style": "wave_long", "hair_color": "#3c2a25", "face_shape": "heart", "mouth_style": "serious"},
    "edward_wilson": {"hair_style": "thin", "hair_color": "#efefef", "glasses": "round", "age": "senior", "face_shape": "oval"},
    "carl_sagan": {"hair_style": "wave", "hair_color": "#6a4a34", "outfit": "turtleneck", "face_shape": "round", "eye_style": "warm"},
    "nikola_tesla": {"hair_style": "swept_back", "hair_color": "#2a1f1e", "mustache": "thin", "face_shape": "long", "mouth_style": "serious"},
    "zhongnanshan": {"hair_style": "side", "hair_color": "#f1f1f1", "age": "senior", "glasses": "round", "face_shape": "oval"},
    "zhang_wenhong": {"hair_style": "short", "hair_color": "#1c1c1c", "glasses": "square", "face_shape": "round", "mouth_style": "gentle"},
    "li_lanjuan": {"hair_style": "short", "hair_color": "#f0f0f0", "age": "senior", "face_shape": "heart", "accessory": "earrings"},
    "atu_gawande": {"hair_style": "short", "hair_color": "#1d1a19", "glasses": "round", "face_shape": "oval", "mouth_style": "serious"},
    "paul_farmer": {"hair_style": "short", "hair_color": "#6a4b39", "face_shape": "square", "mouth_style": "gentle"},
    "anthony_fauci": {"hair_style": "thin", "hair_color": "#efefef", "glasses": "square", "age": "senior", "face_shape": "oval"},
    "william_osler": {"hair_style": "side", "hair_color": "#eeeeee", "mustache": "full", "age": "senior", "face_shape": "long"},
    "elizabeth_blackburn": {"hair_style": "shoulder", "hair_color": "#8a6a4a", "accessory": "earrings", "face_shape": "heart", "mouth_style": "gentle"},
    "david_sinclair": {"hair_style": "side", "hair_color": "#c4b9b0", "age": "senior", "face_shape": "long", "mouth_style": "serious"},
    "barry_marshall": {"hair_style": "thin", "hair_color": "#f0f0f0", "glasses": "round", "age": "senior", "face_shape": "round"},
    "charlie_munger": {"hair_style": "short", "hair_color": "#f0f0f0", "glasses": "square", "age": "senior", "face_shape": "round", "mouth_style": "serious"},
    "naval_ravikant": {"hair_style": "close", "hair_color": "#171514", "beard": "goatee", "outfit": "open_collar", "face_shape": "oval", "eye_style": "soft"},
    "nassim_taleb": {"hair_style": "curly_short", "hair_color": "#34302d", "beard": "full", "outfit": "open_collar", "face_shape": "square", "eye_style": "sharp"},
    "yuval_harari": {"hair_style": "bald", "glasses": "round", "face_shape": "round", "mouth_style": "serious"},
    "peter_drucker": {"hair_style": "thin", "hair_color": "#f2f2f2", "glasses": "square", "age": "senior", "face_shape": "long", "mouth_style": "gentle"},
    "jordan_peterson": {"hair_style": "side", "hair_color": "#7d5b43", "face_shape": "square", "eye_style": "focused"},
    "confucius": {"hair_style": "topknot", "hair_color": "#1b1715", "beard": "full", "outfit": "robe", "face_shape": "long", "eye_style": "soft"},
    "laozi": {"hair_style": "topknot", "hair_color": "#f2f2f2", "mustache": "long", "beard": "full", "age": "senior", "face_shape": "long"},
    "wang_yangming": {"hair_style": "topknot", "hair_color": "#1f1d18", "outfit": "robe", "face_shape": "oval", "mouth_style": "serious"},
    "socrates": {"hair_style": "bald", "beard": "full", "face_shape": "round", "eye_style": "soft"},
    "aristotle": {"hair_style": "wave", "hair_color": "#5a463e", "beard": "light", "face_shape": "long", "mouth_style": "serious"},
    "simone_de_beauvoir": {"hair_style": "wave_long", "hair_color": "#3f312a", "face_shape": "heart", "mouth_style": "serious"},
    "daniel_kahneman": {"hair_style": "thin", "hair_color": "#efefef", "glasses": "square", "age": "senior", "face_shape": "round", "mouth_style": "gentle"},
    "carol_dweck": {"hair_style": "bob", "hair_color": "#6f5142", "face_shape": "heart", "mouth_style": "gentle"},
    "adam_grant": {"hair_style": "short", "hair_color": "#5a4032", "face_shape": "square", "mouth_style": "gentle"},
    "jonathan_haidt": {"hair_style": "side", "hair_color": "#b9b0a5", "glasses": "square", "age": "senior", "face_shape": "round"},
    "angela_duckworth": {"hair_style": "shoulder", "hair_color": "#1d1a20", "face_shape": "heart", "accessory": "earrings", "eye_style": "warm"},
    "annie_duke": {"hair_style": "bob", "hair_color": "#a07d62", "face_shape": "heart", "mouth_style": "smirk"},
    "martin_seligman": {"hair_style": "thin", "hair_color": "#f0f0f0", "glasses": "square", "age": "senior", "face_shape": "round"},
    "daniel_pink": {"hair_style": "bald", "face_shape": "round", "mouth_style": "gentle"},
    "leonardo_da_vinci": {"hair_style": "long", "hair_color": "#f1f1f1", "beard": "full", "age": "senior", "outfit": "robe", "face_shape": "long"},
    "jony_ive": {"hair_style": "close", "hair_color": "#f2f2f2", "outfit": "turtleneck", "age": "senior", "face_shape": "oval", "mouth_style": "serious"},
    "dieter_rams": {"hair_style": "thin", "hair_color": "#f3f3f3", "glasses": "square", "age": "senior", "face_shape": "square", "mouth_style": "gentle"},
    "zaha_hadid": {"hair_style": "wave_long", "hair_color": "#1a1518", "face_shape": "heart", "accessory": "scarf", "eye_style": "sharp"},
    "hayao_miyazaki": {"hair_style": "fluffy", "hair_color": "#efefef", "glasses": "round", "age": "senior", "face_shape": "round", "mouth_style": "gentle"},
    "akira_kurosawa": {"hair_style": "wave", "hair_color": "#f1f1f1", "glasses": "round", "age": "senior", "face_shape": "round"},
    "issey_miyake": {"hair_style": "thin", "hair_color": "#efefef", "age": "senior", "outfit": "turtleneck", "face_shape": "long"},
    "tadao_ando": {"hair_style": "short", "hair_color": "#ededed", "age": "senior", "face_shape": "square", "mouth_style": "serious"},
    "john_maeda": {"hair_style": "close", "hair_color": "#1d1a1a", "glasses": "round", "face_shape": "round", "mouth_style": "gentle"},
    "rei_kawakubo": {"hair_style": "bob", "hair_color": "#111113", "face_shape": "heart", "accessory": "scarf", "eye_style": "sharp"},
    "lee_kuan_yew": {"hair_style": "side", "hair_color": "#f2f2f2", "age": "senior", "face_shape": "long", "mouth_style": "serious"},
    "deng_xiaoping": {"hair_style": "short", "hair_color": "#efefef", "age": "senior", "face_shape": "round", "mouth_style": "gentle"},
    "abraham_lincoln": {"hair_style": "side", "hair_color": "#1a1615", "beard": "chin", "outfit": "formal", "face_shape": "long", "mouth_style": "serious"},
    "nelson_mandela": {"hair_style": "curly_short", "hair_color": "#ececec", "outfit": "formal", "age": "senior", "skin_color": "#8c5c43", "face_shape": "oval", "mouth_style": "gentle"},
    "winston_churchill": {"hair_style": "thin", "hair_color": "#efefef", "outfit": "formal", "age": "senior", "face_shape": "round", "mouth_style": "serious"},
    "peter_senge": {"hair_style": "thin", "hair_color": "#dad5cf", "beard": "light", "age": "senior", "face_shape": "oval"},
    "clay_christensen": {"hair_style": "side", "hair_color": "#eeeeee", "glasses": "square", "age": "senior", "face_shape": "long", "mouth_style": "gentle"},
    "benjamin_franklin": {"hair_style": "long", "hair_color": "#efefef", "age": "senior", "outfit": "formal", "face_shape": "round"},
    "elinor_ostrom": {"hair_style": "short", "hair_color": "#efefef", "glasses": "square", "age": "senior", "face_shape": "heart", "accessory": "earrings"},
    "muhammad_yunus": {"hair_style": "thin", "hair_color": "#efefef", "glasses": "square", "age": "senior", "skin_color": "#b57f56", "face_shape": "oval"},
}


def _hash_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16)


def _pick(seq, seed: int, offset: int = 0):
    return seq[(seed + offset) % len(seq)]


def _category_accent(category: str) -> str:
    return {
        "business": "#4f8df7",
        "technology": "#55c6ff",
        "science": "#73d39c",
        "medical": "#6fdbc6",
        "philosophy": "#9c8fff",
        "culture": "#ff9eb8",
        "policy": "#ffbd66",
        "design": "#9db5ff",
    }.get(category, "#7aa2ff")


def build_avatar_traits(celeb_id: str, profile: dict) -> dict:
    seed = _hash_int(celeb_id)
    palette = PALETTES[seed % len(PALETTES)].copy()
    category = profile["category"]
    defaults = CATEGORY_OVERRIDES.get(category, {})

    traits = {
        "hair_style": _pick(
            [
                "short",
                "side",
                "swept",
                "wave",
                "bob",
                "close",
                "recede",
                "bun",
                "curly_short",
                "fluffy",
                "curtain",
                "shoulder",
                "pixie",
                "swept_back",
            ],
            seed,
        ),
        "hair_color": palette["hair"],
        "glasses": _pick(["none", "none", "none", "round", "square"], seed, 3),
        "beard": _pick(["none", "none", "light", "goatee"], seed, 5),
        "mustache": "none",
        "outfit": defaults.get("outfit", "suit"),
        "shape": defaults.get("shape", "calm"),
        "age": _pick(["adult", "adult", "adult", "senior"], seed, 7),
        "face_shape": defaults.get("face_shape", _pick(["oval", "round", "square", "heart", "long"], seed, 11)),
        "eye_style": defaults.get("eye_style", _pick(["soft", "warm", "focused", "sharp", "smile"], seed, 13)),
        "brow_style": defaults.get("brow_style", _pick(["soft", "arched", "flat", "bold"], seed, 17)),
        "mouth_style": defaults.get("mouth_style", _pick(["gentle", "smile", "serious", "smirk"], seed, 19)),
        "nose_style": defaults.get("nose_style", _pick(["soft", "button", "straight", "strong"], seed, 23)),
        "accessory": defaults.get("accessory", "none"),
        "skin_color": palette["skin"],
    }

    palette["accent"] = _category_accent(category)
    override = dict(ICONIC_OVERRIDES.get(celeb_id, {}))
    palette_update = override.pop("palette", None)
    if palette_update:
        palette.update(palette_update)
    accent = override.pop("accent", None)
    if accent:
        palette["accent"] = accent
    traits.update(override)
    traits["palette"] = palette
    return traits


def _hair_svg(style: str, color: str) -> str:
    if style == "bald":
        return ""
    if style == "side":
        return f'<path d="M74 98 C88 58, 164 52, 188 92 C180 66, 148 58, 118 62 C95 66, 82 78, 74 98 Z" fill="{color}"/>'
    if style == "swept":
        return f'<path d="M70 103 C76 58, 166 48, 194 88 C178 76, 152 70, 122 68 C96 66, 82 76, 70 103 Z" fill="{color}"/>'
    if style == "swept_back":
        return f'<path d="M76 104 C88 56, 166 54, 188 98 C172 74, 154 68, 132 68 C110 68, 92 74, 76 104 Z" fill="{color}"/><path d="M98 76 C108 62, 124 56, 140 58" stroke="{color}" stroke-width="12" stroke-linecap="round"/>'
    if style == "wave":
        return f'<path d="M72 100 C84 56, 170 56, 188 100 C176 80, 156 74, 134 76 C114 78, 94 70, 72 100 Z" fill="{color}"/>'
    if style == "bob":
        return f'<path d="M68 102 C72 58, 178 56, 192 102 L192 144 C180 166, 80 164, 68 140 Z" fill="{color}"/>'
    if style == "shoulder":
        return f'<path d="M66 102 C72 56, 180 56, 194 102 L198 180 C178 194, 80 194, 60 172 Z" fill="{color}"/>'
    if style == "close":
        return f'<path d="M78 103 C88 64, 164 60, 184 100 C168 88, 148 84, 128 84 C112 84, 94 88, 78 103 Z" fill="{color}"/>'
    if style == "pixie":
        return f'<path d="M78 103 C82 66, 170 58, 186 100 C164 80, 144 78, 120 80 C104 82, 90 86, 78 103 Z" fill="{color}"/><path d="M172 102 C180 116, 176 130, 162 136" stroke="{color}" stroke-width="12" stroke-linecap="round"/>'
    if style == "recede":
        return f'<path d="M84 102 C98 72, 158 72, 176 100 C164 84, 148 82, 132 82 C112 82, 98 86, 84 102 Z" fill="{color}"/>'
    if style == "bun":
        return f'<circle cx="128" cy="56" r="20" fill="{color}"/><path d="M70 104 C78 58, 174 58, 188 102 L190 136 C176 154, 82 156, 68 136 Z" fill="{color}"/>'
    if style == "curly_short":
        return f'<path d="M70 104 C74 70, 182 68, 190 106 C180 78, 160 70, 140 72 C118 74, 94 72, 70 104 Z" fill="{color}"/><circle cx="90" cy="88" r="12" fill="{color}"/><circle cx="114" cy="76" r="14" fill="{color}"/><circle cx="148" cy="78" r="13" fill="{color}"/><circle cx="172" cy="92" r="11" fill="{color}"/>'
    if style == "fluffy":
        return f'<path d="M66 108 C72 56, 184 54, 194 106 C182 80, 160 68, 134 72 C110 76, 90 70, 66 108 Z" fill="{color}"/><circle cx="92" cy="78" r="14" fill="{color}"/><circle cx="164" cy="74" r="15" fill="{color}"/>'
    if style == "topknot":
        return f'<circle cx="128" cy="54" r="16" fill="{color}"/><path d="M74 104 C82 64, 174 64, 188 104 C176 82, 156 76, 130 76 C106 76, 90 82, 74 104 Z" fill="{color}"/>'
    if style == "long":
        return f'<path d="M70 102 C80 54, 174 54, 190 102 L198 176 C174 188, 82 188, 60 172 Z" fill="{color}"/>'
    if style == "wave_long":
        return f'<path d="M66 106 C70 56, 180 50, 194 104 L202 176 C182 192, 78 190, 58 168 Z" fill="{color}"/><path d="M74 122 C94 144, 104 160, 108 182" stroke="{color}" stroke-width="16" stroke-linecap="round"/>'
    if style == "wild":
        return f'<path d="M66 108 C72 60, 184 58, 194 104 C188 86, 166 66, 138 72 C108 78, 90 62, 66 108 Z" fill="{color}"/><path d="M62 96 L36 84 M80 70 L68 40 M178 78 L196 48 M194 108 L220 96" stroke="{color}" stroke-width="10" stroke-linecap="round"/>'
    if style == "thin":
        return f'<path d="M84 103 C94 82, 160 80, 176 102 C164 92, 150 88, 132 88 C114 88, 100 92, 84 103 Z" fill="{color}"/>'
    if style == "curtain":
        return f'<path d="M72 104 C82 60, 174 60, 190 100 C176 84, 152 74, 128 72 C104 74, 84 84, 72 104 Z" fill="{color}"/><path d="M128 72 C126 90, 126 98, 128 110" stroke="{color}" stroke-width="12" stroke-linecap="round"/>'
    return f'<path d="M74 104 C82 60, 174 60, 188 104 C176 82, 156 76, 130 76 C108 76, 88 82, 74 104 Z" fill="{color}"/>'


def _face_svg(shape: str, skin: str) -> str:
    if shape == "round":
        return f'<circle cx="128" cy="136" r="58" fill="{skin}"/>'
    if shape == "square":
        return f'<rect x="72" y="80" width="112" height="116" rx="40" fill="{skin}"/>'
    if shape == "heart":
        return f'<path d="M128 78 C156 78, 182 98, 182 128 C182 166, 156 196, 128 204 C100 196, 74 166, 74 128 C74 98, 100 78, 128 78 Z" fill="{skin}"/>'
    if shape == "long":
        return f'<ellipse cx="128" cy="138" rx="52" ry="64" fill="{skin}"/>'
    return f'<ellipse cx="128" cy="136" rx="56" ry="60" fill="{skin}"/>'


def _glasses_svg(glasses: str) -> str:
    if glasses == "round":
        return (
            '<circle cx="102" cy="134" r="17" fill="none" stroke="#44536a" stroke-width="6"/>'
            '<circle cx="154" cy="134" r="17" fill="none" stroke="#44536a" stroke-width="6"/>'
            '<path d="M119 134 H137" stroke="#44536a" stroke-width="5" stroke-linecap="round"/>'
        )
    if glasses == "square":
        return (
            '<rect x="83" y="118" width="38" height="31" rx="11" fill="none" stroke="#44536a" stroke-width="6"/>'
            '<rect x="136" y="118" width="38" height="31" rx="11" fill="none" stroke="#44536a" stroke-width="6"/>'
            '<path d="M120 134 H137" stroke="#44536a" stroke-width="5" stroke-linecap="round"/>'
        )
    return ""


def _brows_svg(style: str, brow_y: int) -> str:
    if style == "arched":
        return (
            f'<path d="M94 {brow_y + 1} C102 {brow_y - 8}, 110 {brow_y - 8}, 118 {brow_y + 1}" stroke="#5b3b36" stroke-width="5" stroke-linecap="round"/>'
            f'<path d="M138 {brow_y + 1} C146 {brow_y - 8}, 154 {brow_y - 8}, 162 {brow_y + 1}" stroke="#5b3b36" stroke-width="5" stroke-linecap="round"/>'
        )
    if style == "flat":
        return (
            f'<path d="M96 {brow_y} H118" stroke="#5b3b36" stroke-width="5" stroke-linecap="round"/>'
            f'<path d="M140 {brow_y} H162" stroke="#5b3b36" stroke-width="5" stroke-linecap="round"/>'
        )
    if style == "bold":
        return (
            f'<path d="M92 {brow_y + 2} C100 {brow_y - 4}, 112 {brow_y - 6}, 120 {brow_y}" stroke="#52332e" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="M136 {brow_y} C144 {brow_y - 6}, 156 {brow_y - 4}, 164 {brow_y + 2}" stroke="#52332e" stroke-width="7" stroke-linecap="round"/>'
        )
    return (
        f'<path d="M95 {brow_y} C102 {brow_y - 5}, 110 {brow_y - 5}, 117 {brow_y}" stroke="#5b3b36" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M139 {brow_y} C146 {brow_y - 5}, 154 {brow_y - 5}, 161 {brow_y}" stroke="#5b3b36" stroke-width="5" stroke-linecap="round"/>'
    )


def _eyes_svg(style: str, eye_y: int) -> str:
    if style == "smile":
        return (
            f'<path d="M96 {eye_y} C101 {eye_y + 6}, 111 {eye_y + 6}, 116 {eye_y}" stroke="#2F3847" stroke-width="5" stroke-linecap="round" fill="none"/>'
            f'<path d="M140 {eye_y} C145 {eye_y + 6}, 155 {eye_y + 6}, 160 {eye_y}" stroke="#2F3847" stroke-width="5" stroke-linecap="round" fill="none"/>'
        )
    if style == "sharp":
        return (
            f'<ellipse cx="106" cy="{eye_y}" rx="7" ry="6" fill="#2F3847"/>'
            f'<ellipse cx="150" cy="{eye_y}" rx="7" ry="6" fill="#2F3847"/>'
            f'<circle cx="109" cy="{eye_y - 2}" r="2" fill="#FFFFFF"/>'
            f'<circle cx="153" cy="{eye_y - 2}" r="2" fill="#FFFFFF"/>'
        )
    if style == "warm":
        return (
            f'<ellipse cx="106" cy="{eye_y}" rx="6" ry="8" fill="#2F3847"/>'
            f'<ellipse cx="150" cy="{eye_y}" rx="6" ry="8" fill="#2F3847"/>'
            f'<circle cx="108" cy="{eye_y - 2}" r="2.4" fill="#FFFFFF"/>'
            f'<circle cx="152" cy="{eye_y - 2}" r="2.4" fill="#FFFFFF"/>'
        )
    if style == "focused":
        return (
            f'<ellipse cx="106" cy="{eye_y}" rx="5" ry="8" fill="#2F3847"/>'
            f'<ellipse cx="150" cy="{eye_y}" rx="5" ry="8" fill="#2F3847"/>'
            f'<circle cx="107" cy="{eye_y - 2}" r="1.8" fill="#FFFFFF"/>'
            f'<circle cx="151" cy="{eye_y - 2}" r="1.8" fill="#FFFFFF"/>'
        )
    return (
        f'<ellipse cx="106" cy="{eye_y}" rx="6" ry="8" fill="#2F3847"/>'
        f'<ellipse cx="150" cy="{eye_y}" rx="6" ry="8" fill="#2F3847"/>'
        f'<circle cx="108" cy="{eye_y - 2}" r="2.2" fill="#FFFFFF"/>'
        f'<circle cx="152" cy="{eye_y - 2}" r="2.2" fill="#FFFFFF"/>'
    )


def _nose_svg(style: str) -> str:
    if style == "button":
        return '<ellipse cx="128" cy="161" rx="7" ry="5" fill="#E2B09C"/>'
    if style == "strong":
        return '<path d="M128 142 C123 156, 122 166, 128 170 C134 166, 133 156, 128 142 Z" fill="#D9A58F"/>'
    if style == "straight":
        return '<path d="M128 142 C126 154, 126 162, 128 167 C130 162, 130 154, 128 142 Z" fill="#E0AD99"/>'
    return '<path d="M128 144 C125 154, 125 162, 128 166 C131 162, 131 154, 128 144 Z" fill="#E2B09C"/>'


def _mouth_svg(style: str, mouth_y: int, shape: str) -> str:
    if style == "serious" or shape == "cool":
        return f'<path d="M112 {mouth_y + 2} H146" stroke="#905853" stroke-width="5" stroke-linecap="round"/>'
    if style == "smirk":
        return f'<path d="M110 {mouth_y + 1} C120 {mouth_y + 9}, 138 {mouth_y + 6}, 150 {mouth_y - 1}" stroke="#9c5f57" stroke-width="6" stroke-linecap="round" fill="none"/>'
    if style == "smile":
        return f'<path d="M106 {mouth_y} C116 {mouth_y + 11}, 140 {mouth_y + 11}, 150 {mouth_y}" stroke="#9c5f57" stroke-width="6" stroke-linecap="round" fill="none"/>'
    return f'<path d="M108 {mouth_y} C118 {mouth_y + 8}, 138 {mouth_y + 8}, 148 {mouth_y}" stroke="#9c5f57" stroke-width="6" stroke-linecap="round" fill="none"/>'


def _facial_hair_svg(traits: dict) -> str:
    beard = traits.get("beard", "none")
    mustache = traits.get("mustache", "none")
    color = traits["hair_color"]
    parts = []
    if mustache == "full":
        parts.append(f'<path d="M103 171 C110 164, 118 164, 127 171 C136 164, 145 164, 152 171" stroke="{color}" stroke-width="8" stroke-linecap="round" fill="none"/>')
    if mustache == "long":
        parts.append(f'<path d="M101 170 C112 163, 118 163, 127 171 C136 163, 142 163, 153 170" stroke="{color}" stroke-width="8" stroke-linecap="round" fill="none"/>')
        parts.append(f'<path d="M100 172 C92 180, 92 192, 102 198" stroke="{color}" stroke-width="6" stroke-linecap="round" fill="none"/>')
        parts.append(f'<path d="M154 172 C162 180, 162 192, 152 198" stroke="{color}" stroke-width="6" stroke-linecap="round" fill="none"/>')
    if mustache == "thin":
        parts.append(f'<path d="M108 171 C116 166, 122 166, 128 170 C134 166, 140 166, 148 171" stroke="{color}" stroke-width="5" stroke-linecap="round" fill="none"/>')
    if beard == "light":
        parts.append(f'<path d="M103 182 C112 196, 144 196, 153 182" stroke="{color}" stroke-width="10" stroke-linecap="round" fill="none" opacity="0.88"/>')
    if beard == "goatee":
        parts.append(f'<path d="M120 183 C124 195, 132 196, 136 183" stroke="{color}" stroke-width="10" stroke-linecap="round" fill="none"/>')
    if beard == "full":
        parts.append(f'<path d="M96 178 C100 214, 158 214, 160 178" fill="{color}" opacity="0.95"/>')
    if beard == "chin":
        parts.append(f'<path d="M102 180 C108 212, 148 212, 154 180" fill="{color}" opacity="0.96"/>')
    return "".join(parts)


def _outfit_svg(outfit: str, palette: dict) -> str:
    base = palette["outfit"]
    accent = palette["accent"]
    if outfit == "hoodie":
        return (
            f'<path d="M66 236 C78 202, 178 202, 190 236 L206 256 H50 Z" fill="{base}"/>'
            f'<path d="M90 214 C100 194, 156 194, 166 214" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>'
        )
    if outfit == "lab":
        return (
            '<path d="M68 236 C80 204, 176 204, 188 236 L202 256 H54 Z" fill="#ffffff"/>'
            f'<path d="M108 206 L94 256 M148 206 L162 256" stroke="{base}" stroke-width="6"/>'
            f'<path d="M126 198 L126 256" stroke="{accent}" stroke-width="5"/>'
        )
    if outfit == "coat":
        return (
            '<path d="M68 236 C80 204, 176 204, 188 236 L202 256 H54 Z" fill="#f8ffff"/>'
            f'<path d="M104 204 L92 256 M150 204 L162 256" stroke="{base}" stroke-width="5"/>'
            f'<rect x="116" y="214" width="24" height="16" rx="7" fill="{accent}"/>'
        )
    if outfit == "robe":
        return (
            f'<path d="M64 236 C78 196, 178 196, 194 236 L206 256 H50 Z" fill="{base}"/>'
            f'<path d="M128 194 L108 256 M128 194 L148 256" stroke="{accent}" stroke-width="6"/>'
        )
    if outfit == "turtleneck":
        return (
            '<path d="M66 238 C80 206, 176 206, 190 238 L204 256 H52 Z" fill="#171b23"/>'
            '<rect x="104" y="192" width="48" height="26" rx="11" fill="#202734"/>'
        )
    if outfit == "soft":
        return (
            f'<path d="M66 236 C78 204, 178 204, 190 236 L204 256 H52 Z" fill="{base}"/>'
            f'<path d="M84 214 C102 200, 154 200, 172 214" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>'
        )
    if outfit == "leather":
        return (
            '<path d="M64 238 C78 204, 178 204, 192 238 L208 256 H48 Z" fill="#1d1f28"/>'
            f'<path d="M92 216 H164" stroke="{accent}" stroke-width="6" stroke-linecap="round" opacity="0.8"/>'
        )
    if outfit == "formal":
        return (
            f'<path d="M66 238 C80 204, 176 204, 190 238 L204 256 H52 Z" fill="{base}"/>'
            '<path d="M110 206 L128 230 L146 206" fill="#f8fafc"/>'
            f'<path d="M128 228 L118 256 L138 256 Z" fill="{accent}"/>'
        )
    if outfit == "open_collar":
        return (
            f'<path d="M66 238 C80 204, 176 204, 190 238 L204 256 H52 Z" fill="{base}"/>'
            '<path d="M106 208 L128 226 L150 208" fill="#f3f6fb"/>'
            '<path d="M114 206 C118 214, 121 220, 128 226 C135 220, 138 214, 142 206" stroke="#f3f6fb" stroke-width="4" fill="none"/>'
        )
    return (
        f'<path d="M66 238 C80 204, 176 204, 190 238 L204 256 H52 Z" fill="{base}"/>'
        '<path d="M108 206 L128 226 L148 206" fill="#f9fbff"/>'
    )


def _accessory_svg(accessory: str, palette: dict) -> str:
    accent = palette["accent"]
    if accessory == "earrings":
        return (
            f'<circle cx="84" cy="154" r="4.8" fill="{accent}"/>'
            f'<circle cx="172" cy="154" r="4.8" fill="{accent}"/>'
        )
    if accessory == "necklace":
        return (
            f'<path d="M104 208 C114 220, 142 220, 152 208" stroke="{accent}" stroke-width="4" fill="none"/>'
            f'<circle cx="128" cy="218" r="4" fill="{accent}"/>'
        )
    if accessory == "scarf":
        return (
            f'<path d="M90 206 C106 194, 150 194, 166 206 L156 222 C146 216, 110 216, 100 222 Z" fill="{accent}" opacity="0.92"/>'
            f'<path d="M148 218 L158 252" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>'
        )
    return ""


def render_cartoon_avatar_svg(celeb_id: str, profile: dict) -> str:
    traits = build_avatar_traits(celeb_id, profile)
    palette = traits["palette"]
    bg_start, bg_end = palette["bg"]
    accent = palette["accent"]
    skin = traits["skin_color"]
    hair = traits["hair_color"]
    age = traits.get("age", "adult")
    face_shape = traits.get("face_shape", "oval")
    eye_y = 132 if age != "senior" else 136
    if face_shape == "long":
        eye_y += 1
    brow_y = 118 if age != "senior" else 120
    smile_y = 168 if age != "senior" else 172
    cheeks = (
        '<ellipse cx="90" cy="156" rx="11" ry="7" fill="#ffb7c2" opacity="0.42"/>'
        '<ellipse cx="166" cy="156" rx="11" ry="7" fill="#ffb7c2" opacity="0.42"/>'
    )
    wrinkles = ""
    if age == "senior":
        wrinkles = (
            '<path d="M94 148 C100 144, 106 144, 112 148" stroke="#d8a99a" stroke-width="2" opacity="0.4"/>'
            '<path d="M144 148 C150 144, 156 144, 162 148" stroke="#d8a99a" stroke-width="2" opacity="0.4"/>'
        )

    initials = escape(profile["name"][:2])
    badge = escape(profile["category_label"][:2])
    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256" fill="none">
  <defs>
    <linearGradient id="bg-{celeb_id}" x1="40" y1="18" x2="210" y2="244" gradientUnits="userSpaceOnUse">
      <stop stop-color="{bg_start}"/>
      <stop offset="1" stop-color="{bg_end}"/>
    </linearGradient>
    <filter id="shadow-{celeb_id}" x="18" y="12" width="220" height="230" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#12203A" flood-opacity="0.16"/>
    </filter>
  </defs>
  <rect width="256" height="256" rx="72" fill="url(#bg-{celeb_id})"/>
  <circle cx="58" cy="50" r="34" fill="{accent}" opacity="0.18"/>
  <circle cx="216" cy="220" r="48" fill="{accent}" opacity="0.15"/>
  <g filter="url(#shadow-{celeb_id})">
    <path d="M56 236 C68 194, 186 194, 200 236 L212 256 H44 Z" fill="#FFFFFF" opacity="0.18"/>
    {_outfit_svg(traits.get("outfit", "suit"), palette)}
    {_accessory_svg(traits.get("accessory", "none"), palette)}
    {_face_svg(face_shape, skin)}
    <ellipse cx="72" cy="98" rx="14" ry="9" fill="{accent}" opacity="0.15"/>
    <ellipse cx="182" cy="96" rx="18" ry="11" fill="{accent}" opacity="0.13"/>
    {_hair_svg(traits["hair_style"], hair)}
    <ellipse cx="83" cy="141" rx="8" ry="12" fill="{skin}"/>
    <ellipse cx="173" cy="141" rx="8" ry="12" fill="{skin}"/>
    {_brows_svg(traits.get("brow_style", "soft"), brow_y)}
    {_eyes_svg(traits.get("eye_style", "soft"), eye_y)}
    {_nose_svg(traits.get("nose_style", "soft"))}
    {cheeks}
    {wrinkles}
    {_mouth_svg(traits.get("mouth_style", "gentle"), smile_y, traits.get("shape", "calm"))}
    {_glasses_svg(traits.get("glasses", "none"))}
    {_facial_hair_svg(traits)}
  </g>
  <g>
    <rect x="22" y="20" width="86" height="34" rx="17" fill="#FFFFFF" fill-opacity="0.58"/>
    <text x="65" y="42" text-anchor="middle" font-family="'Hiragino Sans GB','PingFang SC','Arial'" font-size="18" font-weight="700" fill="#203047">{initials}</text>
    <rect x="166" y="198" width="68" height="32" rx="16" fill="#10233E" fill-opacity="0.9"/>
    <text x="200" y="219" text-anchor="middle" font-family="'Hiragino Sans GB','PingFang SC','Arial'" font-size="16" font-weight="700" fill="#F4F8FF">{badge}</text>
  </g>
</svg>
""".strip()
    return svg


def avatar_url(celeb_id: str) -> str:
    return f"/api/avatar/{celeb_id}.svg"
