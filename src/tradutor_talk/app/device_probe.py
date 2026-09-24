from __future__ import annotations

from tradutor_talk.audio.sounddevice_manager import SoundDeviceManager


def main() -> None:
    manager = SoundDeviceManager()
    devices = manager.list_devices()
    default_input = manager.default_input()
    default_output = manager.default_output()
    default_input_id = default_input.id if default_input else None
    default_output_id = default_output.id if default_output else None

    print("Tradutor Talk — dispositivos de áudio")
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

    print("\nIN/OUT em PADRÃO indicam os dispositivos padrão do Windows.")


if __name__ == "__main__":
    main()
