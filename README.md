# 智者 Digital Sage

与全球最聪明的 100 个大脑对话。

## 当前版本

- 100 位名人思想档案，覆盖商业、科技、科学、医学、思想、文化、治理、设计
- FastAPI 后端接口：`/api/celebrities`、`/api/chat`、`/api/expert-advice`
- 内置单页前端，可直接浏览名人目录、查看方法论并发起对话
- 无 `MIMO_API_KEY` 时自动切换到本地 fallback persona，方便演示和外网预览
- 已补充 `vercel.json` 与 `requirements.txt`，可直接部署到 Vercel

## 本地启动

```bash
python3 api/app.py
```

默认端口：`8103`

## 部署

项目可直接作为 Python Serverless 应用部署到 Vercel。
