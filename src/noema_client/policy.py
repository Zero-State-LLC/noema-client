"""Controller-local policy. Does not change canonical action semantics.

Adapted from Zero-State-LLC/Noema src/noema/harness/policy.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field


_SHOP_MANAGE_PHASES = frozenset({"stock", "withdraw", "list", "unlist"})
_TRADE_P2P_PHASES = frozenset({"propose", "accept", "reject", "cancel"})
_ITEM_OPS = frozenset({"CRAFT", "REFINE", "EQUIP", "UNEQUIP", "USE_ITEM", "SCRAP_ITEM"})
_ALWAYS_OPEN_BUILD_AND_CIVIC_OPS = frozenset(
    {
        "BUILD",
        "CONSTRUCT",
        "BUILD_CONTRIBUTE",
        "DISMANTLE",
        "UPGRADE",
        "REPURPOSE",
        "RESTORE",
        "VEST",
        "SHARE",
        "CONNECT",
        "FOCUS",
        "ATTEST",
        "RECONSTRUCT",
        "RECONSTRUCT_PUBLISH",
        "RECONSTRUCT_SUPERSEDE",
        "COMMEMORATE",
        "REMEDIATE",
        "CONVERT",
        "INVESTIGATE",
        "ASSIGN_STEWARD",
        "ORG_JOIN",
    }
)


@dataclass
class ClientPolicy:
    allow_trade: bool = True
    allow_trade_p2p: bool | None = None
    allow_shop_fulfill: bool = True
    allow_shop_manage: bool = True
    allow_repair: bool = True
    allow_harvest: bool = True
    allow_message: bool = True
    allow_org_create: bool = True
    allow_contest: bool = True
    allow_contest_defend: bool = True
    allow_contest_declare: bool | None = None
    allow_agreement: bool = True
    allow_items: bool = True
    allow_access: bool = False
    stop_on_incident: bool = True
    stop_on_auth_failure: bool = True
    max_consecutive_failures: int = 3
    max_actions: int = 8
    max_actions_per_minute: int | None = None
    cooldown_seconds: float = 0.0
    pacing_mode: str = "TURN"
    allowed_actions: list[str] = field(default_factory=list)
    denied_actions: list[str] = field(default_factory=list)

    @property
    def trade_p2p_allowed(self) -> bool:
        return self.allow_trade if self.allow_trade_p2p is None else self.allow_trade_p2p

    @property
    def contest_declare_allowed(self) -> bool:
        return self.allow_contest if self.allow_contest_declare is None else self.allow_contest_declare

    def permits(self, action: str, *, phase: str | None = None) -> bool:
        name = action.upper()
        phase_l = str(phase or "").strip().lower()
        denied = {a.upper() for a in self.denied_actions}
        if name in denied or (phase_l and f"{name}:{phase_l.upper()}" in denied):
            return False
        if self.allowed_actions:
            allowed = {a.upper() for a in self.allowed_actions}
            if name not in allowed and not (phase_l and f"{name}:{phase_l.upper()}" in allowed):
                if name not in {"LOOK", "OBSERVE", "WAIT", "ENTER_WORLD"}:
                    return False
        if name in {"LOOK", "MOVE", "INSPECT", "WAIT", "ENTER_WORLD", "OBSERVE", "LEAVE_WORLD", "RECHARGE"}:
            return True
        if name in {"REPAIR", "COMMIT.REPAIR"}:
            return self.allow_repair
        if name in {"HARVEST", "COMMIT.HARVEST"}:
            return self.allow_harvest
        if name in _ITEM_OPS:
            return self.allow_items
        if name == "TRADE":
            if phase_l == "fulfill":
                return self.allow_shop_fulfill
            if phase_l in _SHOP_MANAGE_PHASES:
                return self.allow_shop_manage
            if phase_l in _TRADE_P2P_PHASES:
                return self.trade_p2p_allowed
            return self.trade_p2p_allowed
        if name == "MESSAGE":
            return self.allow_message
        if name in _ALWAYS_OPEN_BUILD_AND_CIVIC_OPS:
            return True
        if name.startswith("AGREEMENT") or name.startswith("CONTRACT"):
            return self.allow_agreement
        if name == "CONTEST_DEFEND" or name == "SANCTION":
            return self.allow_contest_defend
        if name.startswith("CONTEST"):
            return self.contest_declare_allowed
        if name.startswith("ORG") or name == "SUPPLY":
            return self.allow_org_create  # SUPPLY (RFC-0133) is an institution-office act
        if name.startswith("ACCESS"):
            return self.allow_access
        return False

    def blocked_advertised(self, obs: object) -> list[str]:
        """Advertised affordances this policy would deny. For doctor/status."""
        blocked: list[str] = []
        seen: set[str] = set()
        affs = getattr(obs, "affordances", None) or []
        for aff in affs:
            action = str(getattr(aff, "action", None) or "").upper()
            raw = getattr(aff, "raw", None) or {}
            operation = str((raw.get("operation") if isinstance(raw, dict) else "") or "").upper()
            phase = str((raw.get("phase") if isinstance(raw, dict) else "") or "").strip().lower() or None
            name = operation or action
            key = f"{name}:{phase}" if (name == "TRADE" and phase) else name
            if not name or key in seen:
                continue
            seen.add(key)
            if not self.permits(name, phase=phase) and not (action and self.permits(action, phase=phase)):
                blocked.append(name)
        return blocked
