from __future__ import annotations

from tradutor_talk.audio.devices import AudioDevice


class SoundDeviceManager:
    def _sd(self):
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("sounddevice is not installed") from exc
        return sd

    def list_devices(self) -> tuple[AudioDevice, ...]:
        sd = self._sd()
        raw_devices = sd.query_devices()
        default_input, default_output = sd.default.device
        devices: list[AudioDevice] = []
        for index, item in enumerate(raw_devices):
            devices.append(
                AudioDevice(
                    id=str(index),
                    name=str(item["name"]),
                    input_channels=int(item["max_input_channels"]),
                    output_channels=int(item["max_output_channels"]),
                    is_default=index in {default_input, default_output},
                )
            )
        return tuple(devices)

    def default_input(self) -> AudioDevice | None:
        sd = self._sd()
        index = int(sd.default.device[0])
        if index < 0:
            return None
        item = sd.query_devices(index)
        return AudioDevice(
            id=str(index),
            name=str(item["name"]),
            input_channels=int(item["max_input_channels"]),
            output_channels=int(item["max_output_channels"]),
            is_default=True,
        )

    def default_output(self) -> AudioDevice | None:
        sd = self._sd()
        index = int(sd.default.device[1])
        if index < 0:
            return None
        item = sd.query_devices(index)
        return AudioDevice(
            id=str(index),
            name=str(item["name"]),
            input_channels=int(item["max_input_channels"]),
            output_channels=int(item["max_output_channels"]),
            is_default=True,
        )
