"""Voice input via Whisper — Groq API."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import httpx
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """حوّل الصوت لنص عبر Groq Whisper."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(500, "GROQ_API_KEY مش موجود")

    # اقرأ الملف
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:  # 25 MB limit
        raise HTTPException(413, "الملف كبير جدًا (max 25MB)")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            files = {
                "file": (file.filename or "audio.webm", content, file.content_type or "audio/webm"),
                "model": (None, "whisper-large-v3"),
                "language": (None, "ar"),
                "response_format": (None, "json"),
            }
            r = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
            )

            if r.status_code != 200:
                logger.error("voice.transcribe_failed", status=r.status_code, body=r.text[:200])
                raise HTTPException(r.status_code, f"فشل التحويل: {r.text[:100]}")

            data = r.json()
            text = data.get("text", "").strip()

            return JSONResponse({
                "success": True,
                "text": text,
                "duration": data.get("duration"),
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("voice.error", error=str(e)[:200])
        raise HTTPException(500, "معلش، حصلت مشكلة في معالجة الصوت")
