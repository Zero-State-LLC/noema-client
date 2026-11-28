"""A world rejection inside an ACT_RESULT frame is a failed command, not a success.

The Worker answers a rejected action with HTTP 200 and the CommandResult body, so the
WebSocket reply is an ACT_RESULT frame whose body says ``ok: false`` and carries an
``error`` and a fresh observation (``failedAction`` attaches one so the Player sees what
did not happen). The observation must not turn that rejection into ``ok=True``.
"""

from __future__ import annotations

from noema_client.protocol import WebSocketGateway
from noema_client.types import FailureClass


def _gateway() -> WebSocketGateway:
    return WebSocketGateway.__new__(WebSocketGateway)


def _act_result(body: dict) -> dict:
    return {"protocol": "agent-protocol/v1", "type": "ACT_RESULT", "request_id": "req.1", "body": body}


def test_rejected_action_with_observation_is_not_ok():
    payload = _act_result({
        "ok": False,
        "request_id": "req.1",
        "error": {"code": "INVALID_REQUEST", "message": "recipient_id and text required"},
        "observation": {"play_text": "Name a recipient and write a message. Nothing changes."},
    })
    result = _gateway()._result(payload, "idem.1", "req.1")
    assert result.ok is False
    assert result.failure == FailureClass.ACTION_REJECTED
    assert result.error == {"code": "INVALID_REQUEST", "message": "recipient_id and text required"}
    assert result.observation == {"play_text": "Name a recipient and write a message. Nothing changes."}


def test_rejected_world_incident_is_classified():
    payload = _act_result({
        "ok": False,
        "error": {"code": "WORLD_INCIDENT", "message": "world is in incident"},
        "observation": {"play_text": "The world is holding still."},
    })
    result = _gateway()._result(payload, "idem.2", "req.2")
    assert result.ok is False
    assert result.failure == FailureClass.WORLD_INCIDENT


def test_accepted_action_stays_ok():
    payload = _act_result({"ok": True, "observation": {"play_text": "You wait."}, "settled": True})
    result = _gateway()._result(payload, "idem.3", "req.3")
    assert result.ok is True
    assert result.failure is None
    assert result.settled is True


def test_observation_without_ok_flag_stays_ok():
    """OBSERVE replies carry an observation and no ok flag; they are successes."""
    payload = {"protocol": "agent-protocol/v1", "type": "OBSERVE", "request_id": "req.4",
               "body": {"observation": {"play_text": "You take in the room."}}}
    result = _gateway()._result(payload, "idem.4", "req.4")
    assert result.ok is True


def test_error_without_ok_flag_is_not_ok():
    """A body that names an error but omits ok is not a success either."""
    payload = _act_result({"error": {"code": "NOT_FOUND", "message": "You do not see that here."},
                           "observation": {"play_text": "Nothing changes."}})
    result = _gateway()._result(payload, "idem.5", "req.5")
    assert result.ok is False
    assert result.failure == FailureClass.ACTION_REJECTED
