"""AI chat endpoint for study assistance."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from .. import auth as auth_module
from ..config import (
    CHAT_MAX_HISTORY_MESSAGES,
    CHAT_MAX_HISTORY_TOTAL_LENGTH,
    CHAT_MAX_MESSAGE_LENGTH,
    CHAT_RATE_LIMIT_PER_HOUR,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from ..models import User
from ..ratelimit import RateLimiter, get_limiter
from ..services.ai_client import get_chat_client

logger = logging.getLogger("xuexibao.chat")
router = APIRouter(prefix="/chat", tags=["chat"])


class HistoryMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("history role must be 'user' or 'assistant'")
        return v


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] | None = None


class ChatResponse(BaseModel):
    reply: str


SYSTEM_PROMPT = (
    "你是考试复习助手。请用中文回答，帮助用户拆解题目、总结考点、解释错题，"
    "回答要简洁清楚，优先给可直接记忆和复习的内容。"
)

# SSE 流式响应单 token 上限（与非流式端点一致）
_STREAM_MAX_TOKENS = 1200


def _extract_reply(completion) -> str:
    if not completion.choices:
        logger.warning("Upstream AI returned empty choices list")
        return ""
    message = completion.choices[0].message
    content = (message.content or "").strip()
    return content


def rate_limiter() -> RateLimiter:
    """FastAPI dependency returning the active rate limiter.

    Override this in tests via ``app.dependency_overrides[rate_limiter]``
    to inject a fake limiter without touching the global one.
    """
    return get_limiter()


def _validate_chat_request(req: ChatRequest, current_user: User, limiter: RateLimiter) -> list[dict]:
    """Shared request validation + message building for /chat/ and /chat/stream.

    Raises HTTPException on any validation/rate-limit failure.
    Returns the OpenAI ``messages`` list ready to send.
    """
    message_text = req.message.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="消息不能为空。")
    if len(message_text) > CHAT_MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"消息过长，单条消息不能超过 {CHAT_MAX_MESSAGE_LENGTH} 个字符。",
        )

    history = req.history or []
    if len(history) > CHAT_MAX_HISTORY_MESSAGES:
        raise HTTPException(
            status_code=400,
            detail=f"历史消息过多，最多允许 {CHAT_MAX_HISTORY_MESSAGES} 条。",
        )

    total_history_len = sum(len(m.content) for m in history)
    if total_history_len > CHAT_MAX_HISTORY_TOTAL_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"历史消息总长度超过限制（{CHAT_MAX_HISTORY_TOTAL_LENGTH} 字符）。",
        )

    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI 服务未配置，请先在 backend/.env 中设置 OPENAI_API_KEY。",
        )

    # Per-user fixed-window limit. Redis-backed when REDIS_URL is set.
    limiter.check(key=f"chat:user:{current_user.id}", limit=CHAT_RATE_LIMIT_PER_HOUR)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history:
        messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": message_text})
    return messages


def _sse(data: dict | str) -> str:
    """Format a single SSE frame. Pass a dict to JSON-encode, or '[DONE]'."""
    payload = "[DONE]" if data == "[DONE]" else json.dumps(data, ensure_ascii=False)
    return f"data: {payload}\n\n"


@router.post("/", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    current_user: User = Depends(auth_module.get_current_user),
    limiter: RateLimiter = Depends(rate_limiter),
):
    messages = _validate_chat_request(req, current_user, limiter)

    # Reuse the singleton client so the httpx connection pool persists.
    client = get_chat_client()

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            # Mimo reasoning models may spend many tokens before emitting content.
            max_tokens=1200,
            temperature=0.7,
        )
        reply = _extract_reply(completion)
    except Exception:
        logger.exception("Upstream AI call failed for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI 服务暂时不可用，请稍后重试。",
        )

    if not reply:
        logger.warning("Upstream AI returned empty content for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI 返回内容为空，请重试一次。",
        )

    return ChatResponse(reply=reply)


@router.post("/stream")
def chat_stream(
    req: ChatRequest,
    current_user: User = Depends(auth_module.get_current_user),
    limiter: RateLimiter = Depends(rate_limiter),
) -> StreamingResponse:
    """SSE streaming variant of POST /chat/.

    Streams AI deltas as ``data: {"delta": "..."}\\n\\n`` frames. The final
    frame is ``data: [DONE]\\n\\n``. On error, emits ``data: {"error": "..."}``
    so the frontend can surface it inline without losing partial text.

    Validation runs before opening the stream, so auth/rate-limit/length
    errors are still returned as normal HTTP error responses.
    """
    messages = _validate_chat_request(req, current_user, limiter)
    client = get_chat_client()
    user_id = current_user.id

    def event_stream():
        # Sync generator — Starlette runs it in a threadpool so the sync
        # OpenAI client doesn't block the event loop.
        try:
            stream = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=_STREAM_MAX_TOKENS,
                temperature=0.7,
                stream=True,
            )
            emitted_any = False
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                piece = getattr(delta, "content", None) or ""
                if piece:
                    emitted_any = True
                    yield _sse({"delta": piece})
                # finish_reason handling: OpenAI sends "stop" on the final chunk
                if getattr(chunk.choices[0], "finish_reason", None):
                    break
            if not emitted_any:
                yield _sse({"error": "AI 返回内容为空，请重试一次。"})
        except Exception:
            logger.exception("Upstream AI stream failed for user %s", user_id)
            yield _sse({"error": "AI 服务暂时不可用，请稍后重试。"})
        finally:
            yield _sse("[DONE]")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Disable nginx buffering so chunks flush to the client immediately.
            "X-Accel-Buffering": "no",
        },
    )
