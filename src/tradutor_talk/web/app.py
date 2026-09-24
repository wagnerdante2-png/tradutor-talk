from __future__ import annotations

import asyncio
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request as FastAPIRequest
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

STATIC_DIR = Path(__file__).with_name("static")
LAB_TOKEN_PATH = Path("/tmp/tradutor-talk-lab-token")
GEMINI_LIVE_TRANSLATE_MODEL = "gemini-3.5-live-translate-preview"
LANGUAGE_CODE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
SUPPORTED_TARGET_LANGUAGES = {"pt-BR", "en", "es", "ja", "zh-Hans"}


def _load_lab_token() -> str:
    configured = os.getenv("TRADUTOR_TALK_LAB_TOKEN", "").strip()
    if configured:
        token = configured
    else:
        token = ""
        try:
            if LAB_TOKEN_PATH.exists():
                token = LAB_TOKEN_PATH.read_text(encoding="utf-8").strip()
        except OSError:
            token = ""
        if not token:
            token = secrets.token_urlsafe(32)

    try:
        LAB_TOKEN_PATH.write_text(token, encoding="utf-8")
        LAB_TOKEN_PATH.chmod(0o600)
    except OSError:
        pass
    return token


LAB_TOKEN = _load_lab_token()

app = FastAPI(
    title="Tradutor Talk Codespaces Lab",
    version="0.4.1",
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


def _read_attr(value, *names):
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return None


def _create_live_token_sync(api_key: str, target_language_code: str) -> dict:
    """Create the ephemeral Live token through Google's official SDK.

    The auth-token API is preview and its wire schema has changed. Delegating
    serialization to google-genai keeps this adapter aligned with the current
    API contract instead of hand-crafting preview JSON.
    """
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is not installed in this Codespace. "
            "Run: python -m pip install -e '.[dev,web]'"
        ) from exc

    now = datetime.now(timezone.utc)
    client = genai.Client(api_key=api_key)

    try:
        token = client.auth_tokens.create(
            config={
                "uses": 1,
                "expire_time": now + timedelta(minutes=30),
                "new_session_expire_time": now + timedelta(minutes=1),
                "live_connect_constraints": {
                    "model": GEMINI_LIVE_TRANSLATE_MODEL,
                    "config": {
                        "translation_config": {
                            "target_language_code": target_language_code,
                            "echo_target_language": True,
                        }
                    },
                },
            }
        )
    except Exception as exc:
        raise RuntimeError(
            f"Gemini token provisioning failed: {type(exc).__name__}: {exc}"
        ) from exc

    token_name = str(_read_attr(token, "name") or "").strip()
    if not token_name:
        raise RuntimeError("Gemini SDK did not return an ephemeral token name")

    expire_time = _read_attr(token, "expire_time", "expireTime")
    new_session_expire_time = _read_attr(
        token,
        "new_session_expire_time",
        "newSessionExpireTime",
    )

    return {
        "token": token_name,
        "expire_time": (
            expire_time.isoformat() if hasattr(expire_time, "isoformat") else expire_time
        ),
        "new_session_expire_time": (
            new_session_expire_time.isoformat()
            if hasattr(new_session_expire_time, "isoformat")
            else new_session_expire_time
        ),
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
    if target_language_code not in SUPPORTED_TARGET_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported target language code: {target_language_code}",
        )

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
