from __future__ import annotations

import base64
import hmac
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tradutor_talk.audio.playback import AudioPlaybackError, inspect_wav
from tradutor_talk.core.models import Direction
from tradutor_talk.web.session import (
    BrowserConversationSession,
    BrowserPlaybackError,
    BrowserSessionBusyError,
)

STATIC_DIR = Path(__file__).with_name("static")
MAX_AUDIO_BYTES = 12 * 1024 * 1024
MAX_AUDIO_SECONDS = 30.0
LAB_TOKEN_PATH = Path("/tmp/tradutor-talk-lab-token")


def _load_lab_token() -> str:
    configured = os.getenv("TRADUTOR_TALK_LAB_TOKEN", "").strip()
    token = configured or secrets.token_urlsafe(32)
    try:
        LAB_TOKEN_PATH.write_text(token, encoding="utf-8")
        LAB_TOKEN_PATH.chmod(0o600)
    except OSError:
        pass
    return token


LAB_TOKEN = _load_lab_token()

app = FastAPI(
    title="Tradutor Talk Codespaces Lab",
    version="0.3.1",
    docs_url=None,
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
session = BrowserConversationSession()


class PlaybackPayload(BaseModel):
    utterance_id: str


class SessionKeyPayload(BaseModel):
    api_key: str


def _require_lab_token(request: Request) -> None:
    supplied = request.headers.get("X-Tradutor-Token", "")
    if not supplied or not hmac.compare_digest(supplied, LAB_TOKEN):
        raise HTTPException(status_code=401, detail="invalid laboratory token")


@app.on_event("startup")
async def _announce_lab_token() -> None:
    print("")
    print("=" * 72)
    print("TRADUTOR TALK — CODESPACES LAB")
    print("=" * 72)
    print(f"Token do laboratório: {LAB_TOKEN}")
    print(f"Arquivo do token      : {LAB_TOKEN_PATH}")
    print("Use a porta pública apenas durante o teste e mantenha este token privado.")
    print("=" * 72)
    print("")


@app.get("/")
async def index():
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/public-health")
async def public_health():
    return {
        "ok": True,
        "auth_required": True,
        "service": "tradutor-talk-codespaces-lab",
    }


@app.get("/api/health")
async def health(request: Request):
    _require_lab_token(request)
    return {
        "ok": True,
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "state": session.state,
        "pending_utterance_id": session.pending_utterance_id,
        "context_turns": session.context_turns,
    }


@app.post("/api/session-key")
async def set_session_key(payload: SessionKeyPayload, request: Request):
    _require_lab_token(request)

    key = payload.api_key.strip()
    if hmac.compare_digest(key, LAB_TOKEN):
        raise HTTPException(
            status_code=400,
            detail="Você colou o token do laboratório. Aqui deve entrar uma OPENAI_API_KEY real.",
        )
    if len(key) < 20:
        raise HTTPException(status_code=400, detail="API key appears invalid")

    os.environ["OPENAI_API_KEY"] = key
    await session.hard_reset()
    return {"ok": True, "api_key_configured": True}


@app.post("/api/turn")
async def process_turn(
    request: Request,
    direction: Direction = Query(...),
    source_language: str = Query(..., min_length=2, max_length=16),
    target_language: str = Query(..., min_length=2, max_length=16),
):
    _require_lab_token(request)

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured in this Codespace session",
        )

    audio = await request.body()
    if not audio:
        raise HTTPException(status_code=400, detail="audio body is empty")
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="audio body is too large")

    try:
        info = inspect_wav(audio)
    except (ValueError, AudioPlaybackError) as exc:
        raise HTTPException(status_code=400, detail=f"invalid WAV: {exc}") from exc

    duration_seconds = info.frames / info.sample_rate if info.sample_rate else 0.0
    if duration_seconds <= 0:
        raise HTTPException(status_code=400, detail="WAV has no audio frames")
    if duration_seconds > MAX_AUDIO_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"turn exceeds {MAX_AUDIO_SECONDS:.0f}s limit",
        )

    try:
        result = await session.process_turn(
            audio=audio,
            direction=direction,
            source_language=source_language,
            target_language=target_language,
        )
    except BrowserSessionBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        if session.state == "session_error":
            await session.reset(clear_context=False)
        raise HTTPException(
            status_code=502,
            detail=f"{type(exc).__name__}: {exc}",
        ) from exc

    utterance = result.utterance
    return {
        "ok": True,
        "utterance_id": utterance.id,
        "direction": utterance.direction.value,
        "original_text": utterance.original_text,
        "translated_text": utterance.translated_text,
        "detected_language": utterance.detected_language,
        "stage_latency_ms": utterance.stage_latency_ms,
        "processing_ms": utterance.total_latency_ms,
        "audio_media_type": result.speech.media_type,
        "audio_base64": base64.b64encode(result.speech.audio).decode("ascii"),
        "input_duration_seconds": duration_seconds,
        "state": session.state,
    }


@app.post("/api/playback-finished")
async def playback_finished(payload: PlaybackPayload, request: Request):
    _require_lab_token(request)
    try:
        await session.finish_playback(payload.utterance_id)
    except BrowserPlaybackError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"ok": True, "state": session.state}


@app.post("/api/playback-failed")
async def playback_failed(payload: PlaybackPayload, request: Request):
    _require_lab_token(request)
    try:
        await session.fail_playback(payload.utterance_id)
    except BrowserPlaybackError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"ok": True, "state": session.state}


@app.post("/api/reset")
async def reset(request: Request):
    _require_lab_token(request)
    await session.reset(clear_context=True)
    return {"ok": True, "state": session.state, "context_turns": 0}
