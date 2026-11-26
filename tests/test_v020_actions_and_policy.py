"""Wave 0 unit tests for noema-client v0.2.0 (RFC-0136..0144 actions, policy, observations)."""

from __future__ import annotations

import pytest

from noema_client import __version__
from noema_client.actions import resolve_visible_entity, validate_proposal
from noema_client.affordances import parse_affordances, proposal_from_affordance
from noema_client.errors import NoemaActionRejected
from noema_client.observations import prepare_context, to_observation
from noema_client.policy import ClientPolicy
from noema_client.types import ActionProposal, Observation


def test_version_is_0_2_0():
    assert __version__ == "0.2.0"


def test_direct_recharge_resolves_generator_and_carried_depleted_cell():
    obs = Observation(
        available_actions=["RECHARGE"],
        entities=[{"entity_id": "entity.gen-1", "label": "generator-1"}],
        inventory=[
            {
                "item_id": "item.cell-1",
                "archetype_id": "depleted_cell",
                "label": "depleted cell",
            }
        ],
    )
    gen = validate_proposal(
        ActionProposal(action="RECHARGE", target_id="generator-1"),
        obs,
        ClientPolicy(),
    )
    assert gen.command == "RECHARGE"
    assert gen.mutating is True
    assert gen.arguments["entity_id"] == "entity.gen-1"

    cell = validate_proposal(
        ActionProposal(action="RECHARGE", arguments={"item_id": "depleted cell"}),
        obs,
        ClientPolicy(),
    )
    assert cell.command == "RECHARGE"
    assert cell.arguments["entity_id"] == "item.cell-1"
    assert cell.arguments["item_id"] == "item.cell-1"


def test_build_contribute_routes_to_build_and_resolves_entity():
    obs = Observation(
        available_actions=["BUILD_CONTRIBUTE"],
        entities=[{"entity_id": "entity.stall-frame", "label": "barter-stall-frame"}],
    )
    validated = validate_proposal(
        ActionProposal(action="BUILD_CONTRIBUTE", target_id="barter-stall-frame"),
        obs,
        ClientPolicy(),
    )
    assert validated.command == "BUILD"
    assert validated.arguments["operation"] == "BUILD_CONTRIBUTE"
    assert validated.arguments["entity_id"] == "entity.stall-frame"


@pytest.mark.parametrize(
    "op,extra",
    [
        ("COMMEMORATE", {"target_ref": "entity.gen-1", "title": "First Kiln"}),
        ("REMEDIATE", {"scar_id": "scar.1"}),
        ("CONTRACT_POST", {"kind": "DELIVER_LOT", "target_material": "FERROUS_ORE", "target_count": 2}),
        ("CONTRACT_FULFILL", {"contract_id": "contract.1"}),
        ("CRAFT", {"recipe_id": "arc_welder"}),
        ("REFINE", {"material": "FERROUS_ORE"}),
        ("CONVERT", {"mode": "power"}),
        ("INVESTIGATE", {}),
        ("SANCTION", {"detection_id": "det.1"}),
        ("ORG_JOIN", {"org_id": "org.civic"}),
    ],
)
def test_new_commit_operations_validate(op, extra):
    obs = Observation(available_actions=[op])
    validated = validate_proposal(
        ActionProposal(action=op, arguments=dict(extra)),
        obs,
        ClientPolicy(),
    )
    assert validated.command == "COMMIT"
    assert validated.arguments["operation"] == op
    for key, val in extra.items():
        assert validated.arguments[key] == val


def test_carried_item_resolution_for_equip_unequip_use_scrap_and_repair():
    obs = Observation(
        available_actions=["EQUIP", "UNEQUIP", "USE_ITEM", "SCRAP_ITEM", "REPAIR"],
        inventory=[
            {"item_id": "item.welder-1", "label": "Arc Welder", "archetype_id": "arc_welder"},
            {"item_id": "item.cell-9", "label": "Power Cell", "archetype_id": "power_cell"},
        ],
        equipment={
            "TOOL_SLOT": {"item_id": "item.cutter-2", "label": "Plasma Cutter", "archetype_id": "plasma_cutter"}
        },
    )
    assert resolve_visible_entity(obs, "arc-welder").entity_id == "item.welder-1"
    assert resolve_visible_entity(obs, "plasma cutter").entity_id == "item.cutter-2"

    eq = validate_proposal(ActionProposal(action="EQUIP", target_id="arc welder"), obs, ClientPolicy())
    assert eq.command == "COMMIT"
    assert eq.arguments["operation"] == "EQUIP"
    assert eq.arguments["entity_id"] == "item.welder-1"

    uneq = validate_proposal(ActionProposal(action="UNEQUIP", target_id="plasma-cutter"), obs, ClientPolicy())
    assert uneq.arguments["entity_id"] == "item.cutter-2"

    used = validate_proposal(ActionProposal(action="USE_ITEM", arguments={"item_id": "power_cell"}), obs, ClientPolicy())
    assert used.arguments["item_id"] == "item.cell-9"
    assert used.arguments["entity_id"] == "item.cell-9"

    scrapped = validate_proposal(ActionProposal(action="SCRAP_ITEM", target_id="item.welder-1"), obs, ClientPolicy())
    assert scrapped.arguments["entity_id"] == "item.welder-1"

    repaired = validate_proposal(ActionProposal(action="REPAIR", target_id="plasma cutter"), obs, ClientPolicy())
    assert repaired.arguments["entity_id"] == "item.cutter-2"


def test_decoupled_client_policy_flags():
    # Agreements & contracts are no longer blocked when allow_contest=False
    p = ClientPolicy(
        allow_trade=False,
        allow_shop_fulfill=True,
        allow_shop_manage=False,
        allow_contest=False,
        allow_contest_defend=True,
        allow_agreement=True,
        allow_items=False,
    )
    assert p.permits("AGREEMENT_FORM") is True
    assert p.permits("CONTRACT_POST") is True
    assert p.permits("CONTRACT_FULFILL") is True
    assert p.permits("CONTEST_DECLARE") is False
    assert p.permits("CONTEST_WITHDRAW") is False
    assert p.permits("CONTEST_DEFEND") is True
    assert p.permits("SANCTION") is True
    assert p.permits("TRADE", phase="propose") is False
    assert p.permits("TRADE", phase="accept") is False
    assert p.permits("TRADE", phase="stock") is False
    assert p.permits("TRADE", phase="fulfill") is True
    assert p.permits("CRAFT") is False
    assert p.permits("EQUIP") is False


def test_trade_phases_validation_and_policy_routing():
    obs = Observation(available_actions=["TRADE"])
    policy = ClientPolicy(allow_trade=False, allow_shop_fulfill=True, allow_shop_manage=False)

    fulfill = validate_proposal(
        ActionProposal(action="TRADE", arguments={"phase": "fulfill", "listing_id": "listing.1"}),
        obs,
        policy,
    )
    assert fulfill.command == "TRADE"
    assert fulfill.arguments["phase"] == "fulfill"

    with pytest.raises(NoemaActionRejected) as exc_manage:
        validate_proposal(
            ActionProposal(action="TRADE", arguments={"phase": "stock", "stall_id": "entity.stall-1"}),
            obs,
            policy,
        )
    assert exc_manage.value.code == "POLICY_DENIED"

    with pytest.raises(NoemaActionRejected) as exc_p2p:
        validate_proposal(
            ActionProposal(action="TRADE", arguments={"phase": "propose", "counterparty_id": "player.b"}),
            obs,
            policy,
        )
    assert exc_p2p.value.code == "POLICY_DENIED"

    with pytest.raises(NoemaActionRejected) as exc_bad:
        validate_proposal(
            ActionProposal(action="TRADE", arguments={"phase": "bogus"}),
            obs,
            ClientPolicy(),
        )
    assert exc_bad.value.code == "INVALID_PROPOSAL"


def test_observations_expose_v020_fields():
    obs = to_observation(
        {
            "world": "perihelion-reach",
            "cycle": 42,
            "sequence": 100,
            "player_id": "player.m02",
            "inventory": [{"item_id": "item.1", "archetype_id": "arc_welder"}],
            "equipment": {"TOOL_SLOT": {"item_id": "item.1"}},
            "material_lots": [{"material": "FERROUS_ORE", "grade": "SOUND", "amount": 3}],
            "shop_listings": [{"listing_id": "list.1", "listing_kind": "SELL_OFFER"}],
            "open_contracts": [{"contract_id": "ctr.1", "kind": "DELIVER_LOT"}],
            "unlocked_affordances": [{"operation": "CRAFT", "unlocked_by": "infra:workshop"}],
        }
    )
    assert obs.inventory[0]["item_id"] == "item.1"
    assert obs.equipment["TOOL_SLOT"]["item_id"] == "item.1"
    assert obs.material_lots[0]["material"] == "FERROUS_ORE"
    assert obs.shop_listings[0]["listing_id"] == "list.1"
    assert obs.open_contracts[0]["contract_id"] == "ctr.1"
    assert obs.unlocked_affordances[0]["operation"] == "CRAFT"

    ctx = prepare_context(obs, [], ClientPolicy(allow_contest_declare=False, allow_contest_defend=True))
    assert ctx["canonical"]["inventory"] == obs.inventory
    assert ctx["canonical"]["equipment"] == obs.equipment
    assert ctx["canonical"]["material_lots"] == obs.material_lots
    assert ctx["canonical"]["shop_listings"] == obs.shop_listings
    assert ctx["canonical"]["open_contracts"] == obs.open_contracts
    assert ctx["canonical"]["unlocked_affordances"] == obs.unlocked_affordances
    assert ctx["system"]["permits"]["contest_declare"] is False
    assert ctx["system"]["permits"]["contest_defend"] is True
    assert ctx["system"]["permits"]["shop_fulfill"] is True


def test_affordance_copies_shop_and_item_fields():
    row = {
        "action": "TRADE",
        "phase": "fulfill",
        "stall_id": "entity.stall-1",
        "listing_id": "listing.1",
        "available": True,
    }
    p = proposal_from_affordance(row)
    assert p is not None
    assert p.action == "TRADE"
    assert p.arguments["phase"] == "fulfill"
    assert p.arguments["stall_id"] == "entity.stall-1"
    assert p.arguments["listing_id"] == "listing.1"
    obs = Observation(available_actions=["TRADE"], affordances=parse_affordances([row]))
    v = validate_proposal(p, obs, ClientPolicy(allow_trade=False, allow_shop_fulfill=True))
    assert v.command == "TRADE"
    assert v.arguments["listing_id"] == "listing.1"
