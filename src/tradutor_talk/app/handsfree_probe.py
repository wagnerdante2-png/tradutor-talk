from __future__ import annotations

import argparse
import asyncio

from tradutor_talk.app.bootstrap import build_openai_app
from tradutor_talk.audio.capture import CaptureSettings
from tradutor_talk.audio.handsfree_capture import HandsFreeRecorder, HandsFreeSettings
from tradutor_talk.audio.playback import SoundDevicePlayer
from tradutor_talk.audio.routing import build_conversation_routes, parse_device_selector
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
            "Providers : "
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
    except Exception:
        if controller.state is SessionState.SESSION_ERROR:
            controller.recover()
        raise


def _recorder(config, *, device):
    capture_settings = CaptureSettings(
        sample_rate=config.audio.sample_rate,
        channels=config.audio.channels,
        block_ms=config.audio.block_ms,
        dtype=config.audio.dtype,
        device=device,
    )
    segmenter_settings = SegmenterConfig(
        block_ms=config.audio.block_ms,
        pre_roll_ms=config.vad.pre_roll_ms,
        start_speech_ms=config.vad.start_speech_ms,
        end_silence_ms=config.vad.end_silence_ms,
        wait_timeout_seconds=config.vad.wait_timeout_seconds,
        max_utterance_seconds=config.vad.max_utterance_seconds,
    )
    return HandsFreeRecorder(
        vad=WebRTCVAD(aggressiveness=config.vad.aggressiveness),
        settings=HandsFreeSettings(
            capture=capture_settings,
            segmenter=segmenter_settings,
        ),
    )


async def run_handsfree(
    *,
    local_language: str,
    remote_language: str,
    rounds: int,
    local_input_device=None,
    remote_input_device=None,
    local_output_device=None,
    remote_output_device=None,
) -> None:
    config = load_config("config/default.toml")
    controller = build_openai_app()

    routes = build_conversation_routes(
        local_input_device=local_input_device,
        remote_input_device=remote_input_device,
        local_output_device=local_output_device,
        remote_output_device=remote_output_device,
    )

    local_recorder = _recorder(
        config,
        device=routes.local_to_remote.input_device,
    )
    remote_recorder = _recorder(
        config,
        device=routes.remote_to_local.input_device,
    )
    local_player = SoundDevicePlayer(
        device=routes.remote_to_local.output_device,
    )
    remote_player = SoundDevicePlayer(
        device=routes.local_to_remote.output_device,
    )

    controller.start()

    print("Tradutor Talk — hands-free half-duplex roteado")
    print("As vozes reproduzidas são geradas por IA.")
    print(f"Você: {local_language} | Interlocutor: {remote_language}")
    print("Áudio em memória; nenhuma gravação é salva pelo aplicativo.")
    print(
        "REMOTO→LOCAL: "
        f"entrada={routes.remote_to_local.input_device!r} "
        f"saída={routes.remote_to_local.output_device!r}"
    )
    print(
        "LOCAL→REMOTO: "
        f"entrada={routes.local_to_remote.input_device!r} "
        f"saída={routes.local_to_remote.output_device!r}"
    )
    print("Pressione Ctrl+C para encerrar.")

    completed_rounds = 0
    try:
        while rounds == 0 or completed_rounds < rounds:
            await _listen_and_translate(
                label="INTERLOCUTOR",
                recorder=remote_recorder,
                player=local_player,
                controller=controller,
                direction=Direction.REMOTE_TO_LOCAL,
                source_language=remote_language,
                target_language=local_language,
            )

            await _listen_and_translate(
                label="VOCÊ",
                recorder=local_recorder,
                player=remote_player,
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
        description="Conversa hands-free alternada com VAD local e rotas de áudio"
    )
    parser.add_argument("--local-language", default="pt-BR")
    parser.add_argument("--remote-language", default="en-US")
    parser.add_argument(
        "--rounds",
        type=int,
        default=0,
        help="0 = contínuo; N = encerra após N rodadas completas",
    )
    parser.add_argument("--local-input-device", default=None)
    parser.add_argument("--remote-input-device", default=None)
    parser.add_argument("--local-output-device", default=None)
    parser.add_argument("--remote-output-device", default=None)
    args = parser.parse_args()

    if args.rounds < 0:
        parser.error("--rounds deve ser >= 0")

    try:
        asyncio.run(
            run_handsfree(
                local_language=args.local_language,
                remote_language=args.remote_language,
                rounds=args.rounds,
                local_input_device=parse_device_selector(args.local_input_device),
                remote_input_device=parse_device_selector(args.remote_input_device),
                local_output_device=parse_device_selector(args.local_output_device),
                remote_output_device=parse_device_selector(args.remote_output_device),
            )
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
