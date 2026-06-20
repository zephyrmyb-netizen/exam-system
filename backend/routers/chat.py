"""Chat endpoint — AI-powered conversation for study assistance.

Uses OpenAI-compatible API (requires OPENAI_API_KEY in config).
Login is optional; the user's identity is passed along if available.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAI
from pydantic import BaseModel

from .. import auth as auth_module
from ..config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from ..models import User

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    context: str | None = None


class ChatResponse(BaseModel):
    reply: str


SYSTEM_PROMPT = (
    "你是考试复习助手，帮助用户拆解题目、总结重点、用问答方式复习知识。"
    "请用中文回答，简洁清晰，每次回复控制在 200 字以内。"
)


@router.post("/", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    current_user: User | None = Depends(auth_module.get_current_user_optional),
):
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI 服务未配置（缺少 OPENAI_API_KEY），请联系管理员设置。",
        )

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if req.context:
        messages.append({"role": "user", "content": f"[上下文]{req.context}"})

    messages.append({"role": "user", "content": req.message})

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        reply = completion.choices[0].message.content or ""
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 服务响应异常：{str(e)}",
        )

    return ChatResponse(reply=reply)
