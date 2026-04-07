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
