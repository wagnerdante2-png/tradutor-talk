from __future__ import annotations

import asyncio
import hmac
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException, Query, Request as FastAPIRequest
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

STATIC_DIR = Path(__file__).with_name("static")
LAB_TOKEN_PATH = Path("/tmp/tradutor-talk-lab-token")
GEMINI_AUTH_TOKEN_URL = "https://generativelanguage.googleapis.com/v1beta/auth_tokens"
GEMINI_LIVE_TRANSLATE_MODEL = "gemini-3.5-live-translate-preview"
LANGUAGE_CODE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")


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
    version="0.4.0",
    docs_url=None,
    redoc_url=None,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class GeminiKeyPayload(BaseModel):
    api_key: str


def _require_lab_token(request: FastAPIRequest) -> None:
    supplied = request.headers.get("X-Tradutor-Token", "")
    if not supplied or not hmac.compare_digest(supplied, LAB_TOKEN):
        raise HTTPException(status_code=401, detail="invalid laboratory token")


def _gemini_api_key() -> str:
    return (
        os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GOOGLE_API_KEY", "").strip()
    )


def _create_live_token_sync(api_key: str, target_language_code: str) -> dict:
    now = datetime.now(timezone.utc)
    body = {
        "uses": 1,
        "expireTime": (now + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        "newSessionExpireTime": (now + timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "liveConnectConstraints": {
            "model": f"models/{GEMINI_LIVE_TRANSLATE_MODEL}",
            "config": {
                "responseModalities": ["AUDIO"],
                "inputAudioTranscription": {},
                "outputAudioTranscription": {},
                "translationConfig": {
                    "targetLanguageCode": target_language_code,
                    "echoTargetLanguage": True,
                },
            },
        },
    }
    payload = json.dumps(body).encode("utf-8")
    request = Request(
        GEMINI_AUTH_TOKEN_URL,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(payload)),
            "x-goog-api-key": api_key,
        },
    )

    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read(512_000)
    except HTTPError as exc:
        raw = exc.read(64_000)
        message = f"Gemini HTTP {exc.code}"
        try:
            parsed = json.loads(raw.decode("utf-8", errors="replace"))
            api_message = (
                parsed.get("error", {}).get("message")
                if isinstance(parsed, dict)
                else None
            )
            if api_message:
                message += f": {api_message}"
        except Exception:
            pass
        raise RuntimeError(message) from exc
    except URLError as exc:
        raise RuntimeError(f"Gemini connection failed: {exc.reason}") from exc

    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini returned an invalid auth-token response") from exc

    token = str(parsed.get("name", "")).strip()
    if not token:
        raise RuntimeError("Gemini did not return an ephemeral token")

    return {
        "token": token,
        "expire_time": parsed.get("expireTime"),
        "new_session_expire_time": parsed.get("newSessionExpireTime"),
    }


@app.on_event("startup")
async def _announce_lab_token() -> None:
    print("")
    print("=" * 72)
    print("TRADUTOR TALK — GEMINI LIVE TRANSLATE LAB")
    print("=" * 72)
    print(f"Token do laboratório: {LAB_TOKEN}")
    print(f"Arquivo do token      : {LAB_TOKEN_PATH}")
    print(f"Gemini configurado    : {bool(_gemini_api_key())}")
    print("A chave Gemini nunca é enviada ao navegador.")
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
        "service": "tradutor-talk-gemini-live-lab",
        "model": GEMINI_LIVE_TRANSLATE_MODEL,
    }


@app.get("/api/health")
async def health(request: FastAPIRequest):
    _require_lab_token(request)
    return {
        "ok": True,
        "gemini_key_configured": bool(_gemini_api_key()),
        "model": GEMINI_LIVE_TRANSLATE_MODEL,
        "mode": "gemini-live-translate",
    }


@app.post("/api/gemini-key")
async def set_gemini_key(payload: GeminiKeyPayload, request: FastAPIRequest):
    _require_lab_token(request)

    key = payload.api_key.strip()
    if hmac.compare_digest(key, LAB_TOKEN):
        raise HTTPException(
            status_code=400,
            detail="Você colou o token do laboratório. Aqui deve entrar a GEMINI_API_KEY.",
        )
    if len(key) < 20:
        raise HTTPException(status_code=400, detail="Gemini API key appears invalid")

    os.environ["GEMINI_API_KEY"] = key
    os.environ.pop("GOOGLE_API_KEY", None)
    return {"ok": True, "gemini_key_configured": True}


@app.post("/api/gemini-live-token")
async def create_gemini_live_token(
    request: FastAPIRequest,
    target_language_code: str = Query(..., min_length=2, max_length=16),
):
    _require_lab_token(request)

    if not LANGUAGE_CODE_RE.fullmatch(target_language_code):
        raise HTTPException(status_code=400, detail="invalid target language code")

    api_key = _gemini_api_key()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured in this Codespace session",
        )

    try:
        token_data = await asyncio.to_thread(
            _create_live_token_sync,
            api_key,
            target_language_code,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "ok": True,
        "model": GEMINI_LIVE_TRANSLATE_MODEL,
        "target_language_code": target_language_code,
        **token_data,
    }
