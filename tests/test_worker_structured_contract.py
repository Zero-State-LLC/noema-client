"""Representative structured rows from Noema 5ed9635 actions.ts.

Display text is not an executable protocol. Preserve IDs and arguments even
when the display command changes, and keep these templates classified.
"""
import json
from pathlib import Path

import pytest

from noema_client.actions import validate_proposal
from noema_client.affordances import parse_affordances, proposal_from_affordance
from noema_client.policy import ClientPolicy
from noema_client.types import Observation

FIXTURE = json.loads((Path(__file__).parent / "fixtures/worker_affordance_cmds.json").read_text())
CASES = [
    (
        "contest ${formCmd} ${cmdTarget} stake=${contestStakeLine(stake)}",
        "contest disruption relay-7 stake=energy:10,influence:6,compute:2",
        {"operation": "CONTEST_DECLARE", "contest_form": "INFRASTRUCTURE_DISRUPTION",
         "target": {"kind": "ENTITY", "entity_id": "entity.relay-7"},
         "stake": {"energy": 10, "influence": 6, "compute": 2}},
    ),
    (
        "defend ${c.contest_id} stake=${contestStakeLine(stake)}",
        "defend contest.example stake=energy:10,influence:6,compute:2",
        {"operation": "CONTEST_DEFEND", "contest_id": "contest.example",
         "contest_form": "INFRASTRUCTURE_DISRUPTION",
         "stake": {"energy": 10, "influence": 6, "compute": 2}},
    ),
    (
        "reconstruct publish ${rec.reconstruction_id} public",
        "reconstruct publish reconstruction.example public",
        {"operation": "RECONSTRUCT_PUBLISH", "reconstruction_id": "reconstruction.example",
         "subject_ref": "entity.relay-7", "visibility": "PUBLIC"},
    ),
    (
        "succession ${office.office_id} ${handle}",
        "succession office.example successor",
        {"operation": "ORG_SUCCESSION_DESIGNATE", "office_id": "office.example",
         "player_id": "player.successor", "successors": ["player.successor"]},
    ),
]


@pytest.mark.parametrize("template,cmd,args", CASES, ids=[case[2]["operation"] for case in CASES])
def test_current_worker_structured_templates_preserve_canonical_arguments(template, cmd, args):
    assert template in FIXTURE["structured_only"]
    row = {"action": args["operation"], "verb": "COMMIT", "available": True, "cmd": cmd, **args}
    if args["operation"] == "ORG_SUCCESSION_DESIGNATE":
        row["target_id"] = args["office_id"]
    obs = Observation(
        available_actions=[args["operation"]],
        affordances=parse_affordances([row]),
        entities=[{"entity_id": "entity.relay-7"}],
    )
    validated = validate_proposal(proposal_from_affordance(row), obs, ClientPolicy())
    assert validated.command == "COMMIT"
    for key, value in args.items():
        assert validated.arguments[key] == value
    assert "line" not in validated.arguments
    assert "cmd" not in validated.arguments

    # A display-only change must not alter canonical submission.
    changed = {**row, "cmd": "display text is deliberately not a command"}
    assert proposal_from_affordance(changed) == proposal_from_affordance(row)
