# 智者 Digital Sage

与全球最聪明的 100 个大脑对话。

正式产品入口：[https://www.digitalsage.cloud](https://www.digitalsage.cloud)

数字人控制台：[https://www.digitalsage.cloud/console](https://www.digitalsage.cloud/console)

产品定位：一个让用户与全球 100 位顶级思想家、科学家、企业家与治理者进行文本、语音、视频对话的数字智者平台。

## 当前版本

- 100 位名人思想档案，覆盖商业、科技、科学、医学、思想、文化、治理、设计
- FastAPI 后端接口：`/api/celebrities`、`/api/chat`、`/api/expert-advice`
- 新增商业化与知识库接口：`/api/business-model`、`/api/knowledge-library`、`/api/knowledge-library/{celeb_id}`
- 新增数字人控制台：`/console`
- 新增数字人 API：`/api/digital-humans`、`/api/digital-humans/{celeb_id}`
- 新增数字人分身对话 API：`/api/digital-humans/{celeb_id}/sessions`、`/api/digital-dialogue/{session_id}/messages`
- 新增电话桥接 API：`/api/phone-bridge`、`/api/phone-bridge/outbound`
- 内置单页前端，可直接浏览名人目录、查看方法论并发起对话
- 首页已加入通话定价矩阵、现金流场景和知识库 / Skill 训练蓝图
- 控制台可视化人格卡、声音画像、视觉画像、片段库，并可直接发起主动外呼
- 无 `MIMO_API_KEY` 时自动切换到本地 fallback persona，方便演示和外网预览
- 语音分身、电话播报、成片旁白统一走小米 `mimo-v2-tts`
- 已补充 `vercel.json` 与 `requirements.txt`，可直接部署到 Vercel

## 商业化与知识库蓝图

详细方案见：

- `docs/revenue-knowledge-blueprint.md`

## 本地启动

```bash
python3 api/app.py
```

默认端口：`8103`

## 数字人控制台

打开：

- `http://127.0.0.1:8103/console`

当前控制台能力：

- 浏览 100 位数字人及其 readiness
- 查看人格卡、声音画像、视觉画像、片段库
- 直接在控制台里和某个智者的分身持续对话
- 自动生成带口型同步的 `mp4` 视频分身片段
- 发起主动外呼任务
- 查看电话桥 provider 状态与最近外呼任务

电话桥默认使用 `mock` 模式；配置 Twilio 后可直接主动外呼。

相关环境变量：

- `DIGITAL_SAGE_PHONE_PROVIDER=mock|twilio`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `APP_BASE_URL`

## MIMO 媒体链路

当前媒体接入策略：

- 文本互动：`mimo-v2-pro`
- 语音分身 / 电话播报 / Demo 旁白：`mimo-v2-tts`
- 视频成片：画面继续本地渲染与 ffmpeg 封装，语音与文案链路统一走 MIMO

相关环境变量：

- `MIMO_API_BASE`: 默认 `https://api.xiaomimimo.com/v1`
- `MIMO_API_KEY`
- `MIMO_TTS_VOICE`: 默认 `default_zh`
- `MIMO_FILM_TTS_VOICE`: 可选，单独覆盖成片旁白 voice

新增视频分身接口：

- `POST /api/digital-dialogue/{session_id}/video-last`
- `GET /api/avatar-video/{video_id}.mp4`
- `GET /api/avatar-video/{video_id}.jpg`

电话 webhook：

- `POST /api/phone-bridge/twiml/{job_id}/answer`
- `POST /api/phone-bridge/twiml/{job_id}/gather`
- `POST /api/phone-bridge/status/{job_id}`

## 部署

项目可直接作为 Python Serverless 应用部署到 Vercel。

也支持直接部署到 Linux 服务器。

### 自托管到 `43.134.3.158`

仓库内已包含以下部署文件：

- `deploy/digital-sage.service`
- `deploy/digitalsage.cloud.conf`
- `tools/deploy_server.sh`

脚本会做这些事情：

- 上传当前项目到 `/srv/digital-sage/current`
- 在服务器创建 Python 虚拟环境并安装依赖
- 写入运行时 `.env`
- 安装 `systemd` 服务
- 安装 `nginx` 反向代理配置并重载

启动方式：

```bash
SSH_KEY=~/.ssh/digital_sage_deploy ./tools/deploy_server.sh
```

前提：

- 服务器已允许该 SSH 私钥登录
- 域名 `digitalsage.cloud` 和 `www.digitalsage.cloud` 已指向服务器
- `.env.local` 中已配置 `MIMO_API_KEY`

### GitHub 自动发布

仓库已包含 GitHub Actions 工作流：

- `.github/workflows/deploy-production.yml`

当 `main` 分支有新提交，或手动触发 `workflow_dispatch` 时，会自动：

- 编译校验 Python 入口文件
- 校验部署脚本
- 用 SSH 连到生产服务器
- 执行 `tools/deploy_server.sh`

需要在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 中配置这些 secrets：

- `DEPLOY_HOST`: `43.134.3.158`
- `DEPLOY_USER`: `root`
- `DEPLOY_SSH_KEY`: 生产服务器允许登录的私钥全文
- `MIMO_API_KEY`: 小米 MIMO API key
- `MIMO_API_BASE`: 可选，默认 `https://api.xiaomimimo.com/v1`

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=MoKangMedical/digital-sage&type=Date)](https://star-history.com/#MoKangMedical/digital-sage&Date)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License
