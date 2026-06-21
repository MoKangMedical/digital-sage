#!/bin/bash
# 智者 Digital Sage 一键部署脚本
PORT=${1:-8098}
echo "🧠 智者 Digital Sage 部署中..."
cd "$(dirname "$0")"
# Digital Sage 是前端项目，用vercel或静态服务
if command -v vercel &> /dev/null; then
    echo "   使用 Vercel 部署..."
    vercel --prod
else
    echo "   启动本地预览..."
    python3 -m http.server $PORT &
    echo "✅ 智者已启动: http://localhost:$PORT"
fi
