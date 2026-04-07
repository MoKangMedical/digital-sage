"""
Digital Sage 首页剧情 demo 与成片导出的共享分镜数据。
"""

from __future__ import annotations

from ai_engine.cartoon_avatars import avatar_url
from ai_engine.thought_profiles import CELEBRITY_PROFILES


def _experts(*celeb_ids: str) -> list[dict[str, str]]:
    return [
        {
            "id": celeb_id,
            "name": CELEBRITY_PROFILES[celeb_id]["name"],
            "avatar_url": avatar_url(celeb_id),
        }
        for celeb_id in celeb_ids
    ]


DEMO_SCENES = [
    {
        "label": "Scene 01",
        "moment": "凌晨 02:13 · 父亲留下的办公室",
        "title": "真正让人失眠的，不是难题，是没有人一起承担判断。",
        "body": (
            "林夏刚接手家族工厂，订单连续下滑，团队等她在天亮前做决定。"
            "她不需要励志口号，她需要可以真正推敲的脑力陪伴。"
        ),
        "quote": "“我怕的不是亏钱，我怕是把一群相信我们的人，带错方向。”",
        "experts": _experts("buffett", "caodewang", "peter_drucker"),
        "question": "现金流只够 4 个月，我现在最先守住什么？",
        "answer": (
            "先守住信任和现金流。砍掉拖累毛利的非核心定制，"
            "把团队集中到能重复交付的一个拳头产品。"
        ),
        "outcome_label": "系统提炼",
        "outcome": "保命优先 / 聚焦单品 / 核心团队不散",
        "subtitle": "Digital Sage 把人物方法论变成可用的第一轮判断。",
        "theme": "nightfall",
        "narration": (
            "凌晨两点十三分，林夏坐在父亲留下的办公室里。"
            "现金流只够四个月，团队等她在天亮前做决定。"
            "她不是缺一句鼓励，她是缺一个能陪她把问题看清的脑力界面。"
        ),
    },
    {
        "label": "Scene 02",
        "moment": "凌晨 02:27 · 她开始从 100 位智者里挑选视角",
        "title": "同一个问题，不同大脑给出不同重心。",
        "body": (
            "她没有只问一个人。她同时拉来乔布斯看产品、芒格看误判、"
            "图灵看系统、巴菲特看资本纪律。冲突，不再是噪音，而是更完整的坐标。"
        ),
        "quote": "“我终于不是在盲选答案，而是在比较世界级思路的差异。”",
        "experts": _experts("steve_jobs", "charlie_munger", "alan_turing", "buffett"),
        "question": "如果只能保留一条产品线，我该怎么选？",
        "answer": (
            "别先看谁喊得最大声。看哪一条最让客户愿意反复回来，"
            "哪一条能让组织在一年后更简单、更强。"
        ),
        "outcome_label": "对比维度",
        "outcome": "复购强度 / 品牌记忆 / 组织复杂度",
        "subtitle": "100 位人物目录、方法论标签和焦点视角同时进入决策现场。",
        "theme": "constellation",
        "narration": (
            "于是她没有只问一个人。"
            "乔布斯盯产品，芒格盯误判，图灵盯系统，巴菲特盯资本纪律。"
            "同一个问题，在不同大脑里露出不同的重心。"
        ),
    },
    {
        "label": "Scene 03",
        "moment": "凌晨 02:46 · 对话开始收敛成行动",
        "title": "产品不是替你崇拜名人，而是把名人的思路翻译成下一步。",
        "body": (
            "系统把她的处境拆成现金流、组织、产品、长期信任四个变量，"
            "再把多位智者的回答归并成一份清晰动作板。复杂局面，第一次变得能执行。"
        ),
        "quote": "“原来最稀缺的不是答案，是有人帮我把局面拆开。”",
        "experts": _experts("peter_thiel", "alan_turing", "peter_drucker"),
        "question": "我需要一套明天就能执行的方案。",
        "answer": (
            "明天上午只做三件事：停掉最低毛利线；约谈前三大客户确认真实需求；"
            "用一页纸让团队知道为什么只做一件核心产品。"
        ),
        "outcome_label": "明早 09:00 前",
        "outcome": "停一条线 / 谈三位客户 / 发一封全员信",
        "subtitle": "从多智者对话，收敛成一份可执行的动作板。",
        "theme": "signal",
        "narration": (
            "Digital Sage 不替她崇拜名人。"
            "它把多位智者的判断拆成变量，再归并成一份明天就能执行的动作板。"
            "复杂局面，终于第一次落到了地上。"
        ),
    },
    {
        "label": "Scene 04",
        "moment": "清晨 05:11 · 她把决定发给团队",
        "title": "真正打动人的，是人在脆弱时终于有了可以站稳的依据。",
        "body": (
            "天快亮时，她删掉了三个分散注意力的项目，也把解释写得更诚恳。"
            "Digital Sage 没替她承担人生，但帮她把勇气落回证据和逻辑。"
        ),
        "quote": "“谢谢你们再给我三个月。我不会再让团队被摇摆的判断消耗。”",
        "experts": _experts("buffett", "caodewang", "peter_drucker"),
        "question": "我要怎么对团队说，才不只是命令？",
        "answer": (
            "先讲事实，再讲选择，最后讲承诺。人能承受困难，"
            "前提是看见方向，也看见你承担代价的姿态。"
        ),
        "outcome_label": "沟通原则",
        "outcome": "讲事实 / 讲选择 / 讲承诺",
        "subtitle": "产品体现的不只是智力，也包括表达、节奏与人的分量。",
        "theme": "sunrise",
        "narration": (
            "天快亮的时候，她删掉了三个分散注意力的项目。"
            "她也终于知道，要怎么把决定发给团队。"
            "不是命令，而是事实、选择，还有她愿意先承担的代价。"
        ),
    },
    {
        "label": "Scene 05",
        "moment": "一周后 · 她第一次没有靠运气做决定",
        "title": "当你一个人顶住局面时，世界级的大脑可以一起出现。",
        "body": (
            "这就是 Digital Sage 的价值。不是替代真实世界，不是神化名人，"
            "而是把长期方法论做成一个随时可调用的对话界面。关键节点，不必只剩自己和情绪。"
        ),
        "quote": "“有些决定还是得我来做，但我终于不是孤身在黑暗里做。”",
        "experts": _experts("buffett", "sam_altman", "albert_einstein", "zhongnanshan", "confucius", "zaha_hadid"),
        "question": "如果下一次我再陷入犹豫呢？",
        "answer": "回到变量、回到原则、回到长期。让最好的脑力先陪你把问题看清，再开始行动。",
        "outcome_label": "产品一句话",
        "outcome": "与全球最聪明的 100 个大脑对话，把复杂问题看清一层。",
        "subtitle": "剧情 Demo 结束后，用户可以继续在下方真实发问。",
        "theme": "daybreak",
        "narration": (
            "这就是 Digital Sage。"
            "不是替代真实世界，不是神化名人。"
            "而是让世界级的大脑，在你最需要判断的时候，一起出现。"
        ),
    },
]
