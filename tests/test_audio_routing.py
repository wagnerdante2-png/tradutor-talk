from tradutor_talk.audio.routing import (
    build_conversation_routes,
    parse_device_selector,
)


def test_parse_device_selector_supports_index_name_and_default() -> None:
    assert parse_device_selector(None) is None
    assert parse_device_selector("") is None
    assert parse_device_selector("  ") is None
    assert parse_device_selector("12") == 12
    assert parse_device_selector(8) == 8
    assert parse_device_selector("CABLE Output") == "CABLE Output"


def test_conversation_routes_cross_audio_to_opposite_side() -> None:
    routes = build_conversation_routes(
        local_input_device=1,
        remote_input_device=2,
        local_output_device=3,
        remote_output_device=4,
    )
    assert routes.local_to_remote.input_device == 1
    assert routes.local_to_remote.output_device == 4
    assert routes.remote_to_local.input_device == 2
    assert routes.remote_to_local.output_device == 3
