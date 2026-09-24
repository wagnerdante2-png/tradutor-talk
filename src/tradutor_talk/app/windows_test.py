from __future__ import annotations

import asyncio
import getpass
import os
import sys

from tradutor_talk.app.handsfree_probe import run_handsfree
from tradutor_talk.audio.routing import parse_device_selector
from tradutor_talk.audio.sounddevice_manager import SoundDeviceManager


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def _print_devices() -> None:
    manager = SoundDeviceManager()
    devices = manager.list_devices()
    default_input = manager.default_input()
    default_output = manager.default_output()
    default_input_id = default_input.id if default_input else None
    default_output_id = default_output.id if default_output else None

    print("\nDISPOSITIVOS DE ÁUDIO")
    print("ID | IN | OUT | PADRÃO | NOME")
    print("---+----+-----+--------+----------------------------------------")
    for device in devices:
        flags = []
        if device.id == default_input_id:
            flags.append("IN")
        if device.id == default_output_id:
            flags.append("OUT")
        print(
            f"{device.id:>2} | "
            f"{device.input_channels:>2} | "
            f"{device.output_channels:>3} | "
            f"{','.join(flags) or '-':>6} | "
            f"{device.name}"
        )


def _ensure_api_key() -> None:
    if os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY encontrada no ambiente.")
        return

    print("\nA chave será usada somente neste processo e não será salva pelo Tradutor Talk.")
    key = getpass.getpass("Cole sua OPENAI_API_KEY: ").strip()
    if not key:
        raise SystemExit("Teste cancelado: OPENAI_API_KEY não informada.")
    os.environ["OPENAI_API_KEY"] = key


def _tabletop_setup() -> dict:
    print("\nMODO MESA")
    print("Mesmo microfone e mesma saída nos dois sentidos.")
    input_device = parse_device_selector(_ask("ID do microfone (vazio = padrão)"))
    output_device = parse_device_selector(_ask("ID do fone/alto-falante (vazio = padrão)"))
    return {
        "local_input_device": input_device,
        "remote_input_device": input_device,
        "local_output_device": output_device,
        "remote_output_device": output_device,
    }


def _routed_setup() -> dict:
    print("\nMODO CHAMADA ROTEADA")
    print("REMOTO→LOCAL: entrada da chamada/virtual cable → seu fone.")
    print("LOCAL→REMOTO: seu microfone → saída virtual usada como microfone na chamada.")
    return {
        "local_input_device": parse_device_selector(
            _ask("ID do SEU microfone (vazio = padrão)")
        ),
        "remote_input_device": parse_device_selector(
            _ask("ID da ENTRADA do áudio remoto/virtual")
        ),
        "local_output_device": parse_device_selector(
            _ask("ID do SEU fone (vazio = padrão)")
        ),
        "remote_output_device": parse_device_selector(
            _ask("ID da SAÍDA virtual usada como microfone da chamada")
        ),
    }


async def _run() -> None:
    print("=" * 64)
    print("TRADUTOR TALK — TESTE WINDOWS")
    print("=" * 64)

    if sys.platform != "win32":
        print("AVISO: este assistente foi desenhado para Windows 10/11.")

    _ensure_api_key()
    _print_devices()

    print("\n1 - Teste de mesa (mais rápido)")
    print("2 - Teste de chamada roteada")
    mode = _ask("Escolha", "1")
    devices = _routed_setup() if mode == "2" else _tabletop_setup()

    local_language = _ask("Seu idioma", "pt-BR")
    remote_language = _ask("Idioma do interlocutor", "en-US")
    rounds_raw = _ask("Rodadas completas (0 = contínuo)", "1")
    try:
        rounds = int(rounds_raw)
    except ValueError as exc:
        raise SystemExit("Rodadas deve ser um número inteiro.") from exc
    if rounds < 0:
        raise SystemExit("Rodadas deve ser >= 0.")

    print("\nIniciando half-duplex alternado.")
    await run_handsfree(
        local_language=local_language,
        remote_language=remote_language,
        rounds=rounds,
        **devices,
    )


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print("\nTeste encerrado pelo usuário.")


if __name__ == "__main__":
    main()
