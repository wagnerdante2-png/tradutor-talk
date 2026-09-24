from __future__ import annotations

from dataclasses import dataclass

DeviceSelector = int | str | None


def parse_device_selector(value: str | int | None) -> DeviceSelector:
    """Normalize a CLI/config device selector for sounddevice."""
    if value is None or isinstance(value, int):
        return value
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.isdigit():
        return int(normalized)
    return normalized


@dataclass(slots=True, frozen=True)
class AudioRoute:
    input_device: DeviceSelector
    output_device: DeviceSelector


@dataclass(slots=True, frozen=True)
class ConversationRoutes:
    local_to_remote: AudioRoute
    remote_to_local: AudioRoute


def build_conversation_routes(
    *,
    local_input_device: DeviceSelector = None,
    remote_input_device: DeviceSelector = None,
    local_output_device: DeviceSelector = None,
    remote_output_device: DeviceSelector = None,
) -> ConversationRoutes:
    return ConversationRoutes(
        local_to_remote=AudioRoute(
            input_device=local_input_device,
            output_device=remote_output_device,
        ),
        remote_to_local=AudioRoute(
            input_device=remote_input_device,
            output_device=local_output_device,
        ),
    )
