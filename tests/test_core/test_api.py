import requests

import pytest
from infinipy2.core.api import Autogenerate, OMIT
from infinipy2.core.exceptions import APICommandFailed, APITransportFailure


def test_omit_fields(izbox):
    resp = izbox.api.post("/api/izsim/echo_post", data={"a": "b"})
    assert resp.get_result() == {'a': 'b'}

    resp = izbox.api.post("/api/izsim/echo_post",
                          data={"a": "b", "c": {"d": {"e": OMIT}}})
    assert resp.get_result() == {'a': 'b', 'c': {'d': {}}}


def test_error_response(izbox):
    with pytest.raises(APICommandFailed) as caught:
        izbox.api.post("/api/izsim/echo_error", data={'a': 1})

    exception_response = caught.value.response
    assert exception_response.get_error() is None


def test_autogenerate_fields(izbox):
    responses = [
        izbox.api.post(
            "/api/izsim/echo_post",
            data={"a":
                  {"b":
                   {"name": Autogenerate("obj-{ordinal}-{time}-{timestamp}-{uuid}")}}})
        for i in range(2)]
    jsons = [r.get_result() for r in responses]
    for index, json in enumerate(jsons):
        name = json["a"]["b"]["name"]
        obj, ordinal, time, timestamp, uuid = name.split("-")
        assert (int(ordinal) - 1) == index
        assert (int(timestamp) // 1000) == int(float(time))
        assert uuid
        assert len(set(uuid)) > 1


def test_specific_address(izbox, izbox_simulator):
    with pytest.raises(APICommandFailed):
        izbox.api.get("/api/rest/system",
                      address=izbox_simulator.get_inactive_node_address())


def test_specific_address_doesnt_change_active_url(izbox, izbox_simulator):
    izbox.api.get("/api/rest/system")
    new_url = izbox.api._active_url = "http://blap.com/a/b/c"
    izbox.api.get("/api/rest/system",
                  address=izbox_simulator.get_active_node_address())
    assert izbox.api._active_url == new_url


def test_api_transport_error(izbox, request):
    def fake_request(api_obj, *args, **kwargs):
        raise requests.exceptions.ConnectionError('FakeConnectionError')

    def set_request(new_request):
        curr_val = izbox.api._request
        izbox.api._request = new_request
        return curr_val

    orig_request = set_request(fake_request)

    @request.addfinalizer
    def cleanup():
        set_request(orig_request)

    with pytest.raises(APITransportFailure):
        izbox.api.post("/api/izbox_simulator/echo_post")


def test_relative_api(system):
    system.api.get("system")


def test_absolute_api(system):
    system.api.get("/api/rest/system")


def test_normalize_addresses(system):
    get_normalized = system._normalize_addresses
    assert get_normalized('1.2.3.4', use_ssl=False) == [('1.2.3.4', 80)]
    assert get_normalized('1.2.3.4', use_ssl=True) == [('1.2.3.4', 443)]

    with pytest.raises(ValueError):
        get_normalized(('1.2.3.4', 80, 20), use_ssl=True)


def test_approval_context(system):
    with system.api.get_unapproved_context():
        assert not system.api._approved

        with system.api.get_approved_context():
            assert system.api._approved

        assert not system.api._approved
