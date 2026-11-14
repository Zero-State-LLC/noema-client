"""Credential destinations are checked without contacting a real server."""
import pytest

from noema_client.client import NoemaClient
from noema_client.config import StoredCredential, save_credential, load_credential
from noema_client.discovery import Discovery
from noema_client.errors import NoemaAuthError, NoemaProtocolError


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    monkeypatch.delenv("NOEMA_TOKEN", raising=False)
    monkeypatch.delenv("NOEMA_SERVER", raising=False)


def client(tmp_path, server="https://other.example", **kwargs):
    save_credential(StoredCredential("synthetic-access", server="https://origin.example", resume_token="synthetic-resume"), tmp_path)
    def http(*args):
        raise AssertionError("No HTTP credential should be sent")
    c = NoemaClient(server, config_home=tmp_path, http=http, **kwargs)
    c.discovery = Discovery(server, transports=["http"])
    return c


@pytest.mark.parametrize("server", ["https://other.example", "http://origin.example", "https://origin.example:444"])
@pytest.mark.parametrize("operation", ["connect", "observe"])
def test_stored_credential_rejects_other_origin(tmp_path, server, operation):
    c = client(tmp_path, server, transport="http")
    with pytest.raises(NoemaAuthError, match="origin"):
        c.connect(auto_enter=False) if operation == "connect" else c.observe()
    assert c._gateway is None


@pytest.mark.parametrize("server", ["HTTPS://ORIGIN.EXAMPLE:443", "https://origin.example/", "https://Origin.Example/path"])
def test_equivalent_origins_bind(tmp_path, server):
    c = client(tmp_path, server, transport="http")
    c.connect(auto_enter=False)
    assert c.session.connected


@pytest.mark.parametrize("endpoint", ["wss://other.example/ws", "ws://origin.example/ws", "wss://origin.example:444/ws", "//other.example/ws"])
@pytest.mark.parametrize("transport", ["auto", "websocket"])
def test_ws_destination_checked_before_resume_or_auth(tmp_path, endpoint, transport):
    opened = []
    c = client(tmp_path, "https://origin.example", transport=transport, ws_connect=lambda url: opened.append(url))
    c.discovery.websocket_uri = endpoint
    c.discovery.transports = ["websocket"]
    with pytest.raises(NoemaProtocolError, match="origin"):
        c.connect(auto_enter=False)
    assert opened == []


def test_environment_override_does_not_inherit_disk_metadata(tmp_path, monkeypatch):
    c = client(tmp_path)
    monkeypatch.setenv("NOEMA_TOKEN", "intentional-env-token")
    c = NoemaClient("https://selected.example", config_home=tmp_path, transport="http")
    c.discovery = Discovery(c.server, transports=["http"])
    c.connect(auto_enter=False)
    assert c._credential.server == c.server
    assert c._credential.resume_token is None
    assert c._credential.player_id is None
    assert load_credential(tmp_path).resume_token is None


@pytest.mark.parametrize("endpoint", ["wss://ORIGIN.EXAMPLE:443/protocol/v1/ws", "/protocol/v1/ws", "https://origin.example/protocol/v1/ws"])
def test_same_origin_websocket_preserves_resume(tmp_path, endpoint):
    from fake_ws import FakeWsServer
    ws = FakeWsServer()
    opened = []
    def connect(url):
        opened.append(url)
        return ws.connect(url)
    c = client(tmp_path, "https://origin.example", transport="websocket", ws_connect=connect)
    c.discovery.websocket_uri = endpoint
    c.seal = ws.accepted_seal
    c.connect(auto_enter=False)
    assert opened
    assert ws.frames[0]["body"]["resume_token"] == "synthetic-resume"
    assert any(frame["type"] == "AUTH" for frame in ws.frames)


def test_environment_server_does_not_rebind_legacy_disk_token(tmp_path, monkeypatch):
    from noema_client.config import credential_path, DEFAULT_SERVER
    credential_path(tmp_path).write_text('{"access_token": "legacy-synthetic"}')
    monkeypatch.setenv("NOEMA_SERVER", "https://other.example")
    assert load_credential(tmp_path).server == DEFAULT_SERVER
    c = NoemaClient(config_home=tmp_path, transport="http")
    c.discovery = Discovery(c.server, transports=["http"])
    with pytest.raises(NoemaAuthError, match="origin"):
        c.connect(auto_enter=False)


def test_force_enrollment_can_replace_other_origin(tmp_path, monkeypatch):
    c = client(tmp_path, transport="http")
    class Enrollment:
        def __init__(self, server, **kwargs):
            assert server == c.server
        def start(self):
            return {}
        def poll_until_ready(self):
            pass
        def reveal(self):
            return "new-synthetic-token"
    monkeypatch.setattr("noema_client.client.DeviceEnrollment", Enrollment)
    result = c.connect(force=True, auto_enter=False)
    assert result.server == c.server
    assert result.access_token == "new-synthetic-token"
    assert result.resume_token is None
