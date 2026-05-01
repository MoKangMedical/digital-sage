# 🧠 Digital Sage — 数字智者

> 与全球最聪明的100个大脑对话

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)

Digital Sage 让你与苏格拉底、爱因斯坦、达芬奇等100位历史智者进行深度AI对话。不是简单的角色扮演，而是基于每位智者的思想体系、说话风格和人格特质，还原真实的对话体验。

---

## ✨ 功能特色

| 特性 | 描述 |
|------|------|
| 🏛️ **100位智者** | 涵盖哲学家、科学家、企业家、艺术家、政治家、中国思想家 |
| 🎭 **人格引擎** | 基于核心思想、名言、性格特质生成真实对话风格 |
| 🤔 **苏格拉底式对话** | 不只是回答问题，而是引导你思考 |
| 🌍 **跨时空对话** | 让牛顿和爱因斯坦讨论相对论，让孔子和苏格拉底论道 |
| 📚 **学习模式** | 选择一位智者作为长期导师，持续学习 |
| 🎨 **Streamlit界面** | 简洁美观的Web对话界面 |
| 🔌 **API接口** | FastAPI后端，支持第三方集成 |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────┐
│           Streamlit Frontend            │
│         (src/app.py — 对话界面)          │
├─────────────────────────────────────────┤
│          Persona Engine 人格引擎         │
│    (src/persona_engine.py — 提示词生成)   │
├─────────────────────────────────────────┤
│        Philosophers Database            │
│      (data/philosophers.json — 100人)    │
├─────────────────────────────────────────┤
│          AI Model Layer                 │
│   (OpenAI / Claude / 本地模型 可切换)     │
└─────────────────────────────────────────┘
```

- **前端**：Streamlit — 快速原型，零前端代码
- **后端**：FastAPI — 高性能API，支持异步
- **AI模型**：支持 OpenAI GPT-4、Claude、本地LLM（通过环境变量切换）
- **数据**：JSON格式，易于扩展和维护

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/MoKangMedical/digital-sage.git
cd digital-sage
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 4. 启动 Streamlit 界面

```bash
streamlit run src/app.py
```

浏览器打开 `http://localhost:8501` 即可开始对话。

### 5. 启动 API 服务（可选）

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

---

## 📋 智者名单

### 🏛️ 哲学家（22位）

| # | 名字 | 中文名 | 时代 | 国家 | 核心思想 |
|---|------|--------|------|------|----------|
| 1 | Socrates | 苏格拉底 | 古希腊 | 希腊 | 无知之知、苏格拉底式问答 |
| 2 | Plato | 柏拉图 | 古希腊 | 希腊 | 理念论、理想国 |
| 3 | Aristotle | 亚里士多德 | 古希腊 | 希腊 | 逻辑学、中庸之道 |
| 4 | Immanuel Kant | 康德 | 18世纪 | 德国 | 先验哲学、绝对命令 |
| 5 | Friedrich Nietzsche | 尼采 | 19世纪 | 德国 | 超人哲学、权力意志 |
| 6 | Georg Hegel | 黑格尔 | 19世纪 | 德国 | 辩证法、绝对精神 |
| 7 | René Descartes | 笛卡尔 | 17世纪 | 法国 | 我思故我在 |
| 8 | David Hume | 休谟 | 18世纪 | 英国 | 经验主义、因果怀疑 |
| 9 | Baruch Spinoza | 斯宾诺莎 | 17世纪 | 荷兰 | 泛神论、理性伦理 |
| 10 | Gottfried Leibniz | 莱布尼茨 | 17世纪 | 德国 | 单子论、预定和谐 |
| 11 | Ludwig Wittgenstein | 维特根斯坦 | 20世纪 | 奥地利 | 语言哲学、逻辑原子论 |
| 12 | Martin Heidegger | 海德格尔 | 20世纪 | 德国 | 存在与时间、此在 |
| 13 | Jean-Paul Sartre | 萨特 | 20世纪 | 法国 | 存在主义、自由选择 |
| 14 | Albert Camus | 加缪 | 20世纪 | 法国 | 荒诞哲学、反抗精神 |
| 15 | Zhuangzi | 庄子 | 战国 | 中国 | 逍遥游、齐物论 |
| 16 | Laozi | 老子 | 春秋 | 中国 | 道德经、无为而治 |
| 17 | Confucius | 孔子 | 春秋 | 中国 | 仁义礼智信 |
| 18 | Mencius | 孟子 | 战国 | 中国 | 性善论、仁政 |
| 19 | Xunzi | 荀子 | 战国 | 中国 | 性恶论、礼法并重 |
| 20 | Mozi | 墨子 | 战国 | 中国 | 兼爱非攻 |
| 21 | Wang Yangming | 王阳明 | 明代 | 中国 | 知行合一、心学 |
| 22 | Zhu Xi | 朱熹 | 南宋 | 中国 | 理学、格物致知 |

### 🔬 科学家（15位）

| # | 名字 | 中文名 | 时代 | 国家 | 核心贡献 |
|---|------|--------|------|------|----------|
| 1 | Isaac Newton | 牛顿 | 17世纪 | 英国 | 经典力学、万有引力 |
| 2 | Albert Einstein | 爱因斯坦 | 20世纪 | 德国/美国 | 相对论、质能方程 |
| 3 | Charles Darwin | 达尔文 | 19世纪 | 英国 | 进化论、自然选择 |
| 4 | Galileo Galilei | 伽利略 | 16世纪 | 意大利 | 现代物理学之父 |
| 5 | Nicolaus Copernicus | 哥白尼 | 16世纪 | 波兰 | 日心说 |
| 6 | James Maxwell | 麦克斯韦 | 19世纪 | 英国 | 电磁场理论 |
| 7 | Michael Faraday | 法拉第 | 19世纪 | 英国 | 电磁感应 |
| 8 | Marie Curie | 居里夫人 | 19-20世纪 | 波兰/法国 | 放射性研究 |
| 9 | Alan Turing | 图灵 | 20世纪 | 英国 | 计算机科学之父 |
| 10 | John von Neumann | 冯诺依曼 | 20世纪 | 匈牙利/美国 | 博弈论、计算机架构 |
| 11 | Richard Feynman | 费曼 | 20世纪 | 美国 | 量子电动力学 |
| 12 | Stephen Hawking | 霍金 | 20世纪 | 英国 | 黑洞理论、时间简史 |
| 13 | Erwin Schrödinger | 薛定谔 | 20世纪 | 奥地利 | 量子力学波动方程 |
| 14 | Niels Bohr | 玻尔 | 20世纪 | 丹麦 | 原子模型、互补原理 |
| 15 | Werner Heisenberg | 海森堡 | 20世纪 | 德国 | 不确定性原理 |

### 💼 企业家（12位）

| # | 名字 | 中文名 | 时代 | 公司 | 核心理念 |
|---|------|--------|------|------|----------|
| 1 | Steve Jobs | 乔布斯 | 20世纪 | Apple | 极简设计、用户体验 |
| 2 | Elon Musk | 马斯克 | 21世纪 | Tesla/SpaceX | 第一性原理、火星殖民 |
| 3 | Jeff Bezos | 贝索斯 | 21世纪 | Amazon | 客户至上、长期主义 |
| 4 | Mark Zuckerberg | 扎克伯格 | 21世纪 | Meta | 连接世界、快速迭代 |
| 5 | Bill Gates | 比尔盖茨 | 20-21世纪 | Microsoft | 软件改变世界 |
| 6 | Warren Buffett | 巴菲特 | 20-21世纪 | Berkshire | 价值投资、护城河 |
| 7 | Charlie Munger | 芒格 | 20-21世纪 | Berkshire | 多元思维模型 |
| 8 | Sam Walton | 山姆沃尔顿 | 20世纪 | Walmart | 效率零售、服务顾客 |
| 9 | Lei Jun | 雷军 | 21世纪 | 小米 | 性价比、互联网思维 |
| 10 | Jack Ma | 马云 | 21世纪 | 阿里巴巴 | 让天下没有难做的生意 |
| 11 | Ren Zhengfei | 任正非 | 21世纪 | 华为 | 狼性文化、自主研发 |
| 12 | Zhang Yiming | 张一鸣 | 21世纪 | 字节跳动 | 算法推荐、全球化 |

### 🎨 艺术家（7位）

| # | 名字 | 中文名 | 时代 | 国家 | 代表作 |
|---|------|--------|------|------|--------|
| 1 | Leonardo da Vinci | 达芬奇 | 文艺复兴 | 意大利 | 蒙娜丽莎、最后的晚餐 |
| 2 | Michelangelo | 米开朗基罗 | 文艺复兴 | 意大利 | 大卫像、西斯廷天顶画 |
| 3 | Wolfgang Mozart | 莫扎特 | 18世纪 | 奥地利 | 安魂曲、费加罗的婚礼 |
| 4 | Ludwig van Beethoven | 贝多芬 | 18-19世纪 | 德国 | 第九交响曲、月光奏鸣曲 |
| 5 | William Shakespeare | 莎士比亚 | 16-17世纪 | 英国 | 哈姆雷特、罗密欧与朱丽叶 |
| 6 | Pablo Picasso | 毕加索 | 20世纪 | 西班牙 | 格尔尼卡、亚维农少女 |
| 7 | Vincent van Gogh | 梵高 | 19世纪 | 荷兰 | 星空、向日葵 |

### 👑 政治家/思想家（7位）

| # | 名字 | 中文名 | 时代 | 国家 | 核心遗产 |
|---|------|--------|------|------|----------|
| 1 | Alexander the Great | 亚历山大 | 古希腊 | 马其顿 | 征服与文化传播 |
| 2 | Julius Caesar | 凯撒 | 古罗马 | 罗马 | 共和国终结者 |
| 3 | Napoleon Bonaparte | 拿破仑 | 18-19世纪 | 法国 | 法典与军事天才 |
| 4 | Winston Churchill | 丘吉尔 | 20世纪 | 英国 | 战时领袖、演讲家 |
| 5 | Abraham Lincoln | 林肯 | 19世纪 | 美国 | 废奴、联邦统一 |
| 6 | Mao Zedong | 毛泽东 | 20世纪 | 中国 | 革命与建国 |
| 7 | Sun Yat-sen | 孙中山 | 19-20世纪 | 中国 | 三民主义、辛亥革命 |

### ⚔️ 战略/其他思想家（4位）

| # | 名字 | 中文名 | 时代 | 国家 | 核心思想 |
|---|------|--------|------|------|----------|
| 1 | Sun Tzu | 孙子 | 春秋 | 中国 | 孙子兵法、不战而胜 |
| 2 | Guiguzi | 鬼谷子 | 战国 | 中国 | 纵横术、揣摩之术 |
| 3 | Han Fei | 韩非子 | 战国 | 中国 | 法家、法术势 |
| 4 | Niccolò Machiavelli | 马基雅维利 | 16世纪 | 意大利 | 君主论、政治现实主义 |

---

## 📡 API 文档

### 对话接口

```http
POST /api/chat
Content-Type: application/json

{
  "sage": "socrates",
  "message": "什么是正义？",
  "history": []
}
```

**响应：**
```json
{
  "reply": "你问我什么是正义，但你是否先想过……",
  "sage": "Socrates",
  "sage_cn": "苏格拉底"
}
```

### 获取智者列表

```http
GET /api/sages
```

### 获取智者详情

```http
GET /api/sages/{sage_id}
```

### 跨时空对话

```http
POST /api/debate
{
  "sages": ["socrates", "confucius"],
  "topic": "什么是美德？"
}
```

---

## 🛠️ 部署指南

### Docker 部署

```bash
docker build -t digital-sage .
docker run -p 8501:8501 --env-file .env digital-sage
```

### Vercel 部署

```bash
vercel --prod
```

### 服务器部署

```bash
# 使用 systemd
sudo cp deploy/digital-sage.service /etc/systemd/system/
sudo systemctl enable digital-sage
sudo systemctl start digital-sage
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | - |
| `AI_MODEL` | 使用的模型 | `gpt-4` |
| `AI_PROVIDER` | AI提供商 | `openai` |
| `MAX_TOKENS` | 最大token数 | `2048` |
| `TEMPERATURE` | 创造性参数 | `0.8` |
| `APP_PORT` | 服务端口 | `8501` |

---

## 🤝 贡献指南

欢迎贡献新的智者数据、功能改进或Bug修复！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/new-sage`
3. 提交更改：`git commit -m "feat: 添加新智者 xxx"`
4. 推送分支：`git push origin feature/new-sage`
5. 创建 Pull Request

### 添加新智者

在 `data/philosophers.json` 中添加条目：

```json
{
  "id": "new_sage",
  "name": "New Sage",
  "name_cn": "新智者",
  "era": "19世纪",
  "category": "philosopher",
  "country": "Germany",
  "core_ideas": ["核心思想1", "核心思想2"],
  "famous_quotes": ["名言1", "名言2"],
  "personality_traits": ["特质1", "特质2"],
  "speaking_style": "说话风格描述"
}
```

---

## 📄 License

MIT License — 详见 [LICENSE](LICENSE)

---

<p align="center">
  🧠 Digital Sage — 让历史智者的声音在AI时代重新响起
</p>
