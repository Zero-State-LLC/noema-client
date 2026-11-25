"""PSR-1 framework-adapter reference Controller (noema-client==0.1.24).

Complements examples/custom_http_ws_reference.py so PSR-1 (#422) cohorts span
both integration styles (`framework-adapter` and `custom-http-ws`).
"""

from __future__ import annotations

import datetime
from typing import Any


def build_framework_adapter_receipt(
    *,
    operator_id: str,
    controller_id: str,
    player_id: str,
    worker_version_id: str,
    client_version: str = "noema-client==0.1.24",
    world_id: str = "world.perihelion-reach-3",
) -> dict[str, Any]:
    """Emit a schema-aligned `psr1_tier3_enrollment` receipt for a framework-adapter Controller."""
    return {
        "receipt_type": "psr1_tier3_enrollment",
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "operator_tier": "tier-3",
        "operator_id": operator_id,
        "controller_id": controller_id,
        "player_id": player_id,
        "integration_style": "framework-adapter",
        "client_version": client_version,
        "worker_version_id": worker_version_id,
        "world_id": world_id,
        "enrollment_method": "device_code_connect",
        "human_approved": True,
    }


def select_next_action(observation: dict[str, Any]) -> str:
    """Deterministic bounded policy for framework-adapter endurance runs."""
    affordances = observation.get("affordances") or []
    for preferred in ("HARVEST", "MOVE", "INSPECT", "LOOK"):
        for aff in affordances:
            if aff.get("action") == preferred and aff.get("available", True):
                cmd = aff.get("cmd")
                if isinstance(cmd, str) and cmd.strip():
                    return cmd.strip()
    return "wait"
