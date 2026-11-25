from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_example(name: str):
    path = Path(__file__).resolve().parent.parent / "examples" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_framework_adapter_receipt_shape_and_policy() -> None:
    mod = _load_example("framework_adapter_reference")
    receipt = mod.build_framework_adapter_receipt(
        operator_id="tier3-op-1",
        controller_id="ctrl-fw-1",
        player_id="player.fw1",
        worker_version_id="6a94f045-77e8-4957-9393-e56a071040b5",
    )
    assert receipt["receipt_type"] == "psr1_tier3_enrollment"
    assert receipt["integration_style"] == "framework-adapter"
    assert receipt["operator_tier"] == "tier-3"
    assert receipt["human_approved"] is True

    cmd = mod.select_next_action(
        {
            "affordances": [
                {"action": "WAIT", "cmd": "wait", "available": True},
                {"action": "MOVE", "cmd": "move east", "available": True},
            ]
        }
    )
    assert cmd == "move east"
    assert mod.select_next_action({"affordances": []}) == "wait"
