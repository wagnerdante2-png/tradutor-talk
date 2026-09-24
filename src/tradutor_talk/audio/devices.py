from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, frozen=True)
class AudioDevice:
    id: str
    name: str
    input_channels: int
    output_channels: int
    is_default: bool = False


class AudioDeviceManager(Protocol):
    def list_devices(self) -> tuple[AudioDevice, ...]:
        ...

    def default_input(self) -> AudioDevice | None:
        ...

    def default_output(self) -> AudioDevice | None:
        ...
