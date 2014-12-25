import pytest
from infinisdk.core.api import Autogenerate, OMIT
from infinisdk.core.exceptions import APICommandFailed, APITransportFailure, ObjectNotFound
from infinisdk._compat import httplib


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


def test_api_transport_error(system):
    url = '/some/fake/path'
    with pytest.raises(APITransportFailure) as e:
        system.api.get(url, address=('fake_domain_address', 12345))
    transport_repr = repr(e.value)
    assert url in transport_repr
    assert 'get' in transport_repr


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


def test_unapproved_context(infinibox):
    with infinibox.api.get_unapproved_context():
        p = infinibox.pools.create()
        with pytest.raises(APICommandFailed) as exception:
            p.delete()

        assert exception.value.status_code == httplib.FORBIDDEN
    p.delete()


def test_query_preprocessor_context(infinibox):
    def bad_param(request):
        request.url = request.url.set_query_param('evilmonkey', 'true')

    def wrong_id(request):
        request.url = request.url.set_query_param('id', 'eq:99999')

    p = infinibox.pools.create()
    with infinibox.api.query_preprocessor(wrong_id):
        with infinibox.api.query_preprocessor(bad_param):
            with pytest.raises(APICommandFailed) as exception:
                infinibox.pools.get(id=p.id)

            assert exception.value.status_code == httplib.BAD_REQUEST

        with pytest.raises(ObjectNotFound):
            infinibox.pools.get(id=p.id)

    p2 = infinibox.pools.get(id=p.id)
    assert p == p2

