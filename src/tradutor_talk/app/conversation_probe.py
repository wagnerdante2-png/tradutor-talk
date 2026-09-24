from __future__ import annotations

import argparse
import asyncio

from tradutor_talk.app.bootstrap import build_openai_app
from tradutor_talk.audio.capture import CaptureSettings, SoundDeviceRecorder
from tradutor_talk.audio.playback import SoundDevicePlayer
from tradutor_talk.core.models import Direction, SessionState
from tradutor_talk.infrastructure.config import load_config


async def _prompt(message: str) -> str:
    return (await asyncio.to_thread(input, message)).strip().lower()


async def _perform_turn(
    *,
    label: str,
    recorder: SoundDeviceRecorder,
    player: SoundDevicePlayer,
    controller,
    seconds: float,
    direction: Direction,
    source_language: str,
    target_language: str,
) -> bool:
    command = await _prompt(
        f"\n[{label}] ENTER para gravar {seconds:.1f}s ou Q para encerrar: "
    )
    if command == "q":
        return False

    try:
        print("Gravando...")
        wav = await recorder.record_wav(seconds)

        print("Reconhecendo, traduzindo e gerando voz...")
        result = await controller.process_audio(
            audio=wav,
            direction=direction,
            source_language=source_language,
            target_language=target_language,
        )

        utterance = result.utterance
        print(f"Original   : {utterance.original_text}")
        print(f"Tradução   : {utterance.translated_text}")
        print(
            "Latência providers: "
            f"STT {utterance.stage_latency_ms.get('stt', 0):.0f} ms | "
            f"TR {utterance.stage_latency_ms.get('translation', 0):.0f} ms | "
            f"TTS {utterance.stage_latency_ms.get('tts', 0):.0f} ms"
        )

        try:
            controller.begin_playback(utterance)
            await player.play_wav(result.speech.audio)
            controller.finish_playback(utterance)
        except Exception:
            if controller.state in {SessionState.SYNTHESIZING, SessionState.PLAYING}:
                controller.fail_playback(utterance)
            raise

        print(
            f"Playback {utterance.stage_latency_ms.get('playback', 0):.0f} ms | "
            f"turno total {utterance.total_latency_ms:.0f} ms"
        )
        return True

    except Exception as exc:
        print(f"ERRO: {type(exc).__name__}: {exc}")
        if controller.state is SessionState.SESSION_ERROR:
            controller.recover()
            print("Sessão recuperada; você pode tentar novamente.")
        return True


async def _run(
    *,
    seconds: float,
    local_language: str,
    remote_language: str,
) -> None:
    config = load_config("config/default.toml")
    controller = build_openai_app()
    recorder = SoundDeviceRecorder(
        CaptureSettings(
            sample_rate=config.audio.sample_rate,
            channels=config.audio.channels,
            block_ms=config.audio.block_ms,
            dtype=config.audio.dtype,
        )
    )
    player = SoundDevicePlayer()

    controller.start()

    print("Tradutor Talk — prova ponta a ponta PT-BR ⇄ idioma remoto")
    print("As vozes reproduzidas são geradas por IA.")
    print(f"Você: {local_language} | Interlocutor: {remote_language}")
    print("O áudio é processado em memória e não é salvo pelo aplicativo.")

    try:
        while True:
            keep_running = await _perform_turn(
                label="INTERLOCUTOR",
                recorder=recorder,
                player=player,
                controller=controller,
                seconds=seconds,
                direction=Direction.REMOTE_TO_LOCAL,
                source_language=remote_language,
                target_language=local_language,
            )
            if not keep_running:
                break

            keep_running = await _perform_turn(
                label="VOCÊ",
                recorder=recorder,
                player=player,
                controller=controller,
                seconds=seconds,
                direction=Direction.LOCAL_TO_REMOTE,
                source_language=local_language,
                target_language=remote_language,
            )
            if not keep_running:
                break
    finally:
        controller.stop()
        print("\nConversa encerrada.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prova controlada de tradução bidirecional"
    )
    parser.add_argument("--seconds", type=float, default=4.0)
    parser.add_argument("--local-language", default="pt-BR")
    parser.add_argument("--remote-language", default="en-US")
    args = parser.parse_args()

    if args.seconds <= 0 or args.seconds > 30:
        parser.error("--seconds deve estar entre 0 e 30")

    asyncio.run(
        _run(
            seconds=args.seconds,
            local_language=args.local_language,
            remote_language=args.remote_language,
        )
    )


if __name__ == "__main__":
    main()
