"""
Tests for the X-Remote-Authorization retry flow triggered by
403 REMOTE_PERMISSION_REQUIRED responses.

These tests are written against the *post-fix* behavior for PYSDK-230:
  1. Header format must be gated on multi_target_async_replication (8.4+).
     Pre-8.4 must use the legacy single-peer "Basic <b64>" form.
  2. When multiple related systems are registered, the peer whose
     credentials are sent must be resolved from the link/replica
     referenced in the request path -- not the first peer iterated.
"""

# pylint: disable=protected-access

from base64 import b64encode
from unittest.mock import MagicMock, Mock

import pytest
import responses

pytestmark = pytest.mark.timeout(10)

from infinisdk.core.exceptions import APICommandFailed, RelatedSystemNotFound
from infinisdk.infinibox.infinibox import InfiniBox

from ..mocks.mock_conftest import MOCKED_FEAUTES

BASE_HOST = "ibox3441"
BASE_URL = f"http://{BASE_HOST}:80/api/rest"
LOGIN_PAYLOAD = {
    "result": {
        "roles": ["ADMIN"],
        "name": "admin",
        "user_objects": [
            {
                "type": "Local",
                "id": -2,
                "role": "ADMIN",
                "name": "admin",
                "email": "dev.mgmt@infinidat.com",
                "password_digest_version": 1,
                "enabled": True,
                "is_digest_sufficient": True,
                "roles": ["ADMIN"],
            }
        ],
    }
}
SYSTEM_PAYLOAD = {"result": {"name": BASE_HOST, "version": "8.6.0"}}
REMOTE_FORBIDDEN = {
    "error": {
        "code": "REMOTE_PERMISSION_REQUIRED",
        "message": "remote permission required",
    }
}


def _b64(username, password):
    return b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")


def _add_bootstrap(mock):
    mock.add(responses.GET, f"{BASE_URL}/_features", json=MOCKED_FEAUTES, status=200)
    mock.add(responses.POST, f"{BASE_URL}/users/login", json=LOGIN_PAYLOAD, status=200)
    mock.add(responses.GET, f"{BASE_URL}/system", json=SYSTEM_PAYLOAD, status=200)


def _make_peer(name, creds):
    """Build a lightweight InfiniBox stand-in for use as a related system.

    Only api.get_auth() and the repr/str (used in the multi-peer header)
    are exercised by the retry path, so a real simulator isn't needed.
    """
    # MagicMock ignores direct __str__ assignment — configure via spec kwarg.
    peer = MagicMock(__str__=Mock(return_value=name))
    peer.api.get_auth.return_value = creds
    peer.get_name.return_value = name
    return peer


@pytest.fixture
def primary():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        _add_bootstrap(mock)
        box = InfiniBox(BASE_HOST, auth=("admin", "123456"))
        box.login()
        yield box, mock


def _force_compat(infinibox, multi_target):
    infinibox.compat.has_multi_target_async_replication = lambda: multi_target


def _register_peer(infinibox, peer):
    """Bypass register_related_system's type check by appending directly.

    iter_related_systems() walks self._related_systems (a list of
    weakrefs); we hold the peer alive in the caller's scope.
    """
    import weakref

    infinibox._related_systems.append(weakref.ref(peer))


def _add_403_then_200(mock, method, path, success_json=None):
    """First call returns 403 REMOTE_PERMISSION_REQUIRED, second returns 200."""
    url = f"{BASE_URL}/{path}"
    mock.add(method, url, json=REMOTE_FORBIDDEN, status=403)
    mock.add(method, url, json=success_json or {"result": []}, status=200)
    return url


def _last_remote_auth_header(mock):
    for call in reversed(mock.calls):
        if "X-Remote-Authorization" in call.request.headers:
            return call.request.headers["X-Remote-Authorization"]
    return None


# ---------------------------------------------------------------------------
# Bug 1: header format must be gated on multi_target_async_replication
# ---------------------------------------------------------------------------


def test_pre_8_4_uses_single_peer_basic_format(primary):
    """Bug 1: pre-8.4 systems only accept 'Basic <b64>', not the multi-peer form."""
    infinibox, mock = primary
    _force_compat(infinibox, multi_target=False)
    peer = _make_peer("peerA", ("userA", "passA"))
    _register_peer(infinibox, peer)

    _add_403_then_200(mock, responses.GET, "volumes")
    infinibox.api.get("volumes")

    header = _last_remote_auth_header(mock)
    assert header == f"Basic {_b64('userA', 'passA')}"
    assert "=" not in header.split(" ", 1)[1].rstrip("=")  # no sys=b64 form
    assert ";" not in header


def test_8_4_plus_uses_multi_peer_format(primary):
    """Regression guard: 8.4+ must keep emitting the multi-peer 'sys=b64;...' form."""
    infinibox, mock = primary
    _force_compat(infinibox, multi_target=True)
    peer_a = _make_peer("peerA", ("userA", "passA"))
    peer_b = _make_peer("peerB", ("userB", "passB"))
    _register_peer(infinibox, peer_a)
    _register_peer(infinibox, peer_b)

    _add_403_then_200(mock, responses.GET, "volumes")
    infinibox.api.get("volumes")

    header = _last_remote_auth_header(mock)
    assert header.startswith("Basic ")
    payload = header[len("Basic ") :]
    parts = payload.split(";")
    assert len(parts) == 2
    assert f"peerA={_b64('userA', 'passA')}" in parts
    assert f"peerB={_b64('userB', 'passB')}" in parts


# ---------------------------------------------------------------------------
# Bug 2: single-peer path must resolve the *right* peer from the URL
# ---------------------------------------------------------------------------


def _stub_link_resolution(infinibox, segment, obj_id, target_peer):  # pylint: disable=unused-argument
    """Option B: stub system.<segment>.get_by_id_lazy to return a fake object
    whose get_linked_system(safe=True) points at target_peer.

    For 'links' the returned object itself is the link; for 'replicas' and
    'rg_replicas' the code calls .get_link() first, so we emulate both.
    """
    fake_link = MagicMock()
    fake_link.get_linked_system.return_value = target_peer

    if segment == "links":
        holder = fake_link
    else:
        holder = MagicMock()
        holder.get_link.return_value = fake_link

    binder = getattr(infinibox, segment)
    binder.get_by_id_lazy = MagicMock(return_value=holder)


def test_credentials_resolved_from_link_in_path(primary):
    """Bug 2: request path /links/<id>/... must use the linked peer's creds,
    not the first peer yielded by iter_related_systems()."""
    infinibox, mock = primary
    _force_compat(infinibox, multi_target=False)

    peer_a = _make_peer("peerA", ("userA", "passA"))
    peer_b = _make_peer("peerB", ("userB", "passB"))
    _register_peer(infinibox, peer_a)  # iterated first -> would be wrong
    _register_peer(infinibox, peer_b)

    _stub_link_resolution(infinibox, "links", 42, target_peer=peer_b)
    _add_403_then_200(mock, responses.GET, "links/42")

    infinibox.api.get("links/42")

    header = _last_remote_auth_header(mock)
    assert header == f"Basic {_b64('userB', 'passB')}"


@pytest.mark.parametrize("segment", ["replicas", "rg_replicas"])
def test_credentials_resolved_from_replica_in_path(primary, segment):
    """Same as links, for replicas and rg_replicas segments."""
    infinibox, mock = primary
    _force_compat(infinibox, multi_target=False)

    peer_a = _make_peer("peerA", ("userA", "passA"))
    peer_b = _make_peer("peerB", ("userB", "passB"))
    _register_peer(infinibox, peer_a)
    _register_peer(infinibox, peer_b)

    _stub_link_resolution(infinibox, segment, 7, target_peer=peer_b)
    _add_403_then_200(mock, responses.GET, f"{segment}/7")

    infinibox.api.get(f"{segment}/7")

    header = _last_remote_auth_header(mock)
    assert header == f"Basic {_b64('userB', 'passB')}"


# ---------------------------------------------------------------------------
# Retry loop-protection and regression guards
# ---------------------------------------------------------------------------


@pytest.mark.timeout(10)
def test_remote_auth_retry_does_not_loop(primary):
    """If the header we're about to set equals the one already on the
    session, we must raise instead of retrying forever."""
    infinibox, mock = primary
    _force_compat(infinibox, multi_target=False)
    peer = _make_peer("peerA", ("userA", "passA"))
    _register_peer(infinibox, peer)

    infinibox.api._session.headers["X-Remote-Authorization"] = (
        f"Basic {_b64('userA', 'passA')}"
    )

    url = f"{BASE_URL}/volumes"
    mock.add(responses.GET, url, json=REMOTE_FORBIDDEN, status=403)
    mock.add(responses.GET, url, json=REMOTE_FORBIDDEN, status=403)

    with pytest.raises(APICommandFailed) as caught:
        infinibox.api.get("volumes")
    assert caught.value.error_code == "REMOTE_PERMISSION_REQUIRED"


def test_no_related_systems_raises(primary):
    """Regression guard: 403 REMOTE_PERMISSION_REQUIRED with no peers
    registered must raise RelatedSystemNotFound."""
    infinibox, mock = primary
    _force_compat(infinibox, multi_target=False)

    mock.add(responses.GET, f"{BASE_URL}/volumes", json=REMOTE_FORBIDDEN, status=403)

    with pytest.raises(RelatedSystemNotFound):
        infinibox.api.get("volumes")


# ---------------------------------------------------------------------------
# Direct unit tests for the path->peer resolver helper (post-fix only)
# ---------------------------------------------------------------------------


class TestGetRelatedSystemAuthForPath:
    """Isolated tests for API._get_related_system_auth_for_path."""

    def _call(self, infinibox, path):
        return infinibox.api._get_related_system_auth_for_path(path)

    def test_returns_linked_peer_auth(self, primary):
        infinibox, _ = primary
        peer = _make_peer("peerB", ("userB", "passB"))
        _stub_link_resolution(infinibox, "links", 42, target_peer=peer)
        assert self._call(infinibox, "links/42") == ("userB", "passB")

    def test_non_link_bearing_path_returns_none(self, primary):
        infinibox, _ = primary
        assert self._call(infinibox, "volumes/12/metadata") is None

    def test_non_integer_id_returns_none(self, primary):
        infinibox, _ = primary
        assert self._call(infinibox, "links/not-an-id") is None

    def test_querystring_is_ignored(self, primary):
        infinibox, _ = primary
        peer = _make_peer("peerB", ("userB", "passB"))
        _stub_link_resolution(infinibox, "links", 42, target_peer=peer)
        assert self._call(infinibox, "links/42?foo=bar") == ("userB", "passB")

    def test_missing_id_segment_returns_none(self, primary):
        infinibox, _ = primary
        assert self._call(infinibox, "links") is None

    def test_unresolvable_link_returns_none(self, primary):
        """Link exists but get_linked_system returns None (peer gone)."""
        infinibox, _ = primary
        holder = MagicMock()
        holder.get_linked_system.return_value = None
        infinibox.links.get_by_id_lazy = MagicMock(return_value=holder)
        assert self._call(infinibox, "links/42") is None
