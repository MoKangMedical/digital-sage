"""
🧠 智者 Digital Sage — API服务
与全球最聪明的100个大脑对话
"""
import os
import sys
import json
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.thought_profiles import (
    CELEBRITY_PROFILES, get_profile, get_all_celebrities, build_chat_prompt
)

app = FastAPI(
    title="智者 Digital Sage API",
    description="与全球最聪明的100个大脑对话",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MIMO_API_BASE = os.getenv("MIMO_API_BASE", "https://api.xiaomimimo.com/v1")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")

# ===== 数据模型 =====
class ChatRequest(BaseModel):
    celebrity_id: str
    message: str
    topic: Optional[str] = "general"

class ChatResponse(BaseModel):
    celebrity_id: str
    celebrity_name: str
    response: str
    disclaimer: str = "⚠️ 这是AI模拟的回答，基于该名人公开可获取的素材训练，不代表本人观点"

class ExpertAdviceRequest(BaseModel):
    celebrity_id: str
    situation: str
    category: str  # investment/career/health/technology

# ===== API端点 =====

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "智者 Digital Sage",
        "version": "1.0.0",
        "celebrities_loaded": len(CELEBRITY_PROFILES)
    }

@app.get("/api/celebrities")
async def list_celebrities():
    """获取所有名人列表"""
    return get_all_celebrities()

@app.get("/api/celebrities/{celeb_id}")
async def get_celebrity(celeb_id: str):
    """获取名人详细档案"""
    profile = get_profile(celeb_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    return profile

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_celebrity(req: ChatRequest):
    """与名人AI克隆对话"""
    profile = get_profile(req.celebrity_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    
    # 构建提示词
    prompt = build_chat_prompt(req.celebrity_id, req.message, req.topic)
    
    # 调用MIMO API
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{MIMO_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {MIMO_API_KEY}"},
                json={
                    "model": "mimo-v2-pro",
                    "messages": [
                        {"role": "system", "content": f"你是{profile['name']}，{profile['title']}。请用{profile['name']}的思维方式和说话风格回答所有问题。保持人格一致性。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800
                }
            )
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
    except Exception as e:
        ai_response = f"（{profile['name']}暂时不能回答，请稍后再试）"
    
    return ChatResponse(
        celebrity_id=req.celebrity_id,
        celebrity_name=profile["name"],
        response=ai_response
    )

@app.post("/api/expert-advice")
async def get_expert_advice(req: ExpertAdviceRequest):
    """获取专家建议"""
    profile = get_profile(req.celebrity_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    
    prompt = f"""你正在以{profile['name']}的身份给用户提供建议。

背景信息：
{profile['name']}的核心价值观：
{chr(10).join('- ' + v for v in profile['core_values'])}

判断框架：
{json.dumps(profile.get('judgment_framework', {}), ensure_ascii=False, indent=2)}

用户的情况：
{req.situation}

请以{profile['name']}的思维方式分析这个情况，并给出具体建议。
用{profile['speaking_style']['tone']}的风格表达。"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{MIMO_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {MIMO_API_KEY}"},
                json={
                    "model": "mimo-v2-pro",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.6,
                    "max_tokens": 1000
                }
            )
            result = response.json()
            advice = result["choices"][0]["message"]["content"]
    except Exception as e:
        advice = f"（{profile['name']}暂时不能提供建议）"
    
    return {
        "celebrity_id": req.celebrity_id,
        "celebrity_name": profile["name"],
        "category": req.category,
        "advice": advice,
        "framework_used": profile.get("judgment_framework", {}),
        "disclaimer": "⚠️ 这是AI模拟的建议，仅供参考，不构成任何投资/医疗/法律建议"
    }

@app.get("/api/positions/{celeb_id}")
async def get_positions(celeb_id: str):
    """获取名人的立场"""
    profile = get_profile(celeb_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    
    return {
        "celebrity": profile["name"],
        "positions": profile.get("positions", {}),
        "core_values": profile["core_values"]
    }

@app.get("/api/speaking-style/{celeb_id}")
async def get_speaking_style(celeb_id: str):
    """获取名人的说话风格"""
    profile = get_profile(celeb_id)
    if not profile:
        raise HTTPException(status_code=404, detail="未找到该名人")
    
    return {
        "celebrity": profile["name"],
        "speaking_style": profile["speaking_style"]
    }

if __name__ == "__main__":
    import uvicorn
    print("🧠 智者 Digital Sage 启动中...")
    uvicorn.run(app, host="0.0.0.0", port=8103)
