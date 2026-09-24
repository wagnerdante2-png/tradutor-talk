from __future__ import annotations

import argparse
import asyncio

from tradutor_talk.app.bootstrap import build_openai_app
from tradutor_talk.audio.capture import CaptureSettings
from tradutor_talk.audio.handsfree_capture import (
    HandsFreeRecorder,
    HandsFreeSettings,
)
from tradutor_talk.audio.playback import SoundDevicePlayer
from tradutor_talk.audio.segmenter import SegmenterConfig, SpeechStartTimeout
from tradutor_talk.audio.webrtc_vad import WebRTCVAD
from tradutor_talk.core.models import Direction, SessionState
from tradutor_talk.infrastructure.config import load_config


async def _listen_and_translate(
    *,
    label: str,
    recorder: HandsFreeRecorder,
    player: SoundDevicePlayer,
    controller,
    direction: Direction,
    source_language: str,
    target_language: str,
) -> None:
    while True:
        print(f"\n[{label}] ouvindo...")

        try:
            wav = await recorder.wait_for_utterance_wav()
            break
        except SpeechStartTimeout:
            print("Nenhuma fala detectada; mantendo o mesmo lado em escuta.")

    print("Fala encerrada. Reconhecendo, traduzindo e gerando voz...")

    try:
        result = await controller.process_audio(
            audio=wav,
            direction=direction,
            source_language=source_language,
            target_language=target_language,
        )

        utterance = result.utterance
        print(f"Original : {utterance.original_text}")
        print(f"Tradução : {utterance.translated_text}")
        print(
            "Latência  : "
            f"STT {utterance.stage_latency_ms.get('stt', 0):.0f} ms | "
            f"TR {utterance.stage_latency_ms.get('translation', 0):.0f} ms | "
            f"TTS {utterance.stage_latency_ms.get('tts', 0):.0f} ms | "
            f"total {utterance.total_latency_ms:.0f} ms"
        )

        await player.play_wav(result.speech.audio)

    except Exception:
        if controller.state is SessionState.SESSION_ERROR:
            controller.recover()
        raise


async def _run(
    *,
    local_language: str,
    remote_language: str,
    rounds: int,
) -> None:
    config = load_config("config/default.toml")
    controller = build_openai_app()

    capture_settings = CaptureSettings(
        sample_rate=config.audio.sample_rate,
        channels=config.audio.channels,
        block_ms=config.audio.block_ms,
        dtype=config.audio.dtype,
    )
    segmenter_settings = SegmenterConfig(
        block_ms=config.audio.block_ms,
        pre_roll_ms=config.vad.pre_roll_ms,
        start_speech_ms=config.vad.start_speech_ms,
        end_silence_ms=config.vad.end_silence_ms,
        wait_timeout_seconds=config.vad.wait_timeout_seconds,
        max_utterance_seconds=config.vad.max_utterance_seconds,
    )

    recorder = HandsFreeRecorder(
        vad=WebRTCVAD(aggressiveness=config.vad.aggressiveness),
        settings=HandsFreeSettings(
            capture=capture_settings,
            segmenter=segmenter_settings,
        ),
    )
    player = SoundDevicePlayer()

    controller.start()

    print("Tradutor Talk — hands-free half-duplex")
    print("As vozes reproduzidas são geradas por IA.")
    print(f"Você: {local_language} | Interlocutor: {remote_language}")
    print("Áudio em memória; nenhuma gravação é salva pelo aplicativo.")
    print("Pressione Ctrl+C para encerrar.")

    completed_rounds = 0

    try:
        while rounds == 0 or completed_rounds < rounds:
            await _listen_and_translate(
                label="INTERLOCUTOR",
                recorder=recorder,
                player=player,
                controller=controller,
                direction=Direction.REMOTE_TO_LOCAL,
                source_language=remote_language,
                target_language=local_language,
            )

            await _listen_and_translate(
                label="VOCÊ",
                recorder=recorder,
                player=player,
                controller=controller,
                direction=Direction.LOCAL_TO_REMOTE,
                source_language=local_language,
                target_language=remote_language,
            )

            completed_rounds += 1

    finally:
        controller.stop()
        print("\nConversa encerrada.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Conversa hands-free alternada com VAD local"
    )
    parser.add_argument("--local-language", default="pt-BR")
    parser.add_argument("--remote-language", default="en-US")
    parser.add_argument(
        "--rounds",
        type=int,
        default=0,
        help="0 = contínuo; N = encerra após N rodadas completas",
    )
    args = parser.parse_args()

    if args.rounds < 0:
        parser.error("--rounds deve ser >= 0")

    try:
        asyncio.run(
            _run(
                local_language=args.local_language,
                remote_language=args.remote_language,
                rounds=args.rounds,
            )
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
