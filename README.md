# 智者 Digital Sage

与全球最聪明的100个大脑对话

## 一句话定义

Digital Sage 让你与苏格拉底、爱因斯坦、达芬奇等120位历史智者进行AI对话。不是简单的角色扮演，而是深度还原每位智者的思维方式和知识体系。

## 核心能力

- 120+智者: 哲学家/科学家/艺术家/领袖
- 思维还原: 基于原著+研究训练的对话模型
- 跨时空对话: 让牛顿和爱因斯坦讨论相对论
- 学习模式: 选择一位智者作为导师
- 商业闭环: 小红书/抖音/数字人宣传 → 免费试用 → 语音/视频下单 → 记忆订阅

## 正式入口

- 官网: https://www.digitalsage.cloud/
- 增长落地控制台: https://www.digitalsage.cloud/growth
- 下单预约页: https://www.digitalsage.cloud/checkout
- 课程体系: https://www.digitalsage.cloud/courses/

## 支付与部署配置

订单页支持 Stripe Checkout、Creem Checkout 和人工确认。没有配置支付密钥时会自动降级为人工跟进，不影响用户提交订单。

必填运行变量：

- `DEEPSEEK_API_KEY`: 智者对话模型密钥
- `DEEPSEEK_API_BASE`: 默认 `https://api.deepseek.com`
- `DEEPSEEK_MODEL`: 默认 `deepseek-v4-pro`
- `DEEPSEEK_FALLBACK_MODEL`: 默认 `deepseek-chat`

可选收款变量：

- `PUBLIC_BASE_URL`: 默认 `https://www.digitalsage.cloud`
- `STRIPE_SECRET_KEY`: Stripe 服务端密钥
- `STRIPE_CURRENCY`: 默认 `cny`
- `CREEM_API_KEY`: Creem API key
- `CREEM_API_BASE`: 默认 `https://api.creem.io`
- `CREEM_PRODUCT_VOICE_10`
- `CREEM_PRODUCT_VOICE_20`
- `CREEM_PRODUCT_VIDEO_30`
- `CREEM_PRODUCT_STRATEGY_60`
- `CREEM_PRODUCT_MEMORY_SUBSCRIPTION`

## 快速开始

    git clone https://github.com/MoKangMedical/digital-sage.git
    cd digital-sage
    pip install -r requirements.txt
    python src/main.py --sage socrates

MIT License
