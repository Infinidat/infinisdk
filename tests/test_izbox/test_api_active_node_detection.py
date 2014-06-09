import pytest
from infinisdk.core.exceptions import APICommandFailed
from infinisdk.izbox import IZBox


def test_fails_if_no_alternative_node(izbox_simulator):
    system = IZBox(izbox_simulator.get_inactive_node_address())
    with pytest.raises(APICommandFailed):
        system.api.get("system")

def test_detect_active_node(izbox_simulator):
    system = IZBox([izbox_simulator.get_inactive_node_address(), izbox_simulator.get_active_node_address()])
    api_result = system.api.get("system")
    assert api_result.url.hostname == izbox_simulator.active_node_url.hostname
    assert (api_result.url.port or 80) == (izbox_simulator.active_node_url.port or 80)
