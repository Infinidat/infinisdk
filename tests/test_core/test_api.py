import logbook
import pytest
from infinisdk.core.api import Autogenerate, OMIT
from infinisdk.core.config import config
from infinisdk.core.exceptions import APICommandFailed, ObjectNotFound
from infinisdk._compat import httplib
from ..conftest import no_op_context

from urlobject import URLObject as URL


def test_data_none(infinibox):
    resp = infinibox.api.post('/api/infinisim/echo', data=None)
    assert resp.get_result() is None

@pytest.fixture
def capture(request):
    handler = logbook.TestHandler(level=logbook.TRACE)
    handler.push_application()

    @request.addfinalizer
    def pop():
        handler.pop_application()
    return handler

@pytest.fixture(params=[True, False])
def toggle_pretty_response(request, backup_config):
    config.root.api.log.pretty_json = request.param

def test_no_response_logs(toggle_pretty_response, infinibox, capture):
    with infinibox.api.get_no_response_logs_context():
        infinibox.api.get('system')
    assert len(capture.records) == 3
    assert '<-- GET' in capture.records[0].message  # Request log message
    assert '--> 200 OK' in capture.records[1].message  # Response status log message
    assert capture.records[2].message.endswith('...')  # Response data log message


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


def test_url_params(izbox):
    params = {'a': 'b', 'c': 2, 'd': OMIT, 'e': Autogenerate('param_{ordinal}'), 'f': True}
    expected = {'a': 'b', 'c': '2', 'e': 'param_1', 'f': 'True'}
    resp = izbox.api.post("/api/izsim/echo_post", params=params)
    url = URL(resp.response.request.url)
    encoded = url.query_dict
    encoded.pop('approved', None)
    assert expected == encoded


@pytest.mark.parametrize('should_failed', [True, False])
def test_auto_retry(system, should_failed):
    url = "/api/rest/system"
    retry_count = 2
    fault_count = retry_count+1 if should_failed else retry_count
    system.get_simulator().api.inject_fault(url, 500, count=fault_count)
    retry_predicate = lambda exc: isinstance(exc, APICommandFailed)
    system.api.add_auto_retry(retry_predicate, retry_count)
    context = pytest.raises if should_failed else no_op_context
    with context(APICommandFailed):
        system.api.get(url)
    system.api.remove_auto_retry(retry_predicate)


@pytest.fixture(scope='module', params=['', 'prefix'])
def set_autogenerate(request):
    old_prefix = Autogenerate.get_prefix()
    Autogenerate.set_prefix(request.param)
    @request.addfinalizer
    def restore():
        Autogenerate._ORDINALS = {}
        Autogenerate.set_prefix(old_prefix)


def test_autogenerate_fields(izbox):
    responses = [
        izbox.api.post(
            "/api/izsim/echo_post",
            data={"a":
                  {"b":
                   {"name": Autogenerate("{prefix}-obj-{ordinal}-{time}-{timestamp}-{uuid}")}}})
        for i in range(2)]
    jsons = [r.get_result() for r in responses]
    for index, json in enumerate(jsons):
        name = json["a"]["b"]["name"]
        prefix, obj, ordinal, time, timestamp, uuid = name.split("-")
        assert prefix == Autogenerate.get_prefix()
        assert (int(ordinal) - 1) == index
        assert abs((float(timestamp) / 1000.0) - float(time)) < 0.01
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



def test_set_source_identifier(system):
    res = system.api.get("/api/rest/system")
    assert res.response.request.headers['User-Agent'].startswith('python')

    system.api.set_source_identifier('MyUserAgent')
    res = system.api.get("/api/rest/system")
    assert res.response.request.headers['User-Agent'] == 'MyUserAgent'


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
        assert exception.value.response.url.query_dict['approved'] == 'false'
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
            assert exception.value.error_code == exception.value.response.get_error()['code']

        with pytest.raises(ObjectNotFound) as caught:
            infinibox.pools.get(id=p.id)
        exc_msg = str(caught.value)
        assert 'pools' in exc_msg
        assert str(p.id) in exc_msg

    p2 = infinibox.pools.get(id=p.id)
    assert p == p2


def test_query_preprocessor_context_exception(infinibox):
    # pylint: disable=protected-access
    class SomeException(Exception):
        pass

    def preprocessor(_):
        pass

    assert not infinibox.api._preprocessors

    with pytest.raises(SomeException):
        with infinibox.api.query_preprocessor(preprocessor):
            assert infinibox.api._preprocessors == [preprocessor]
            raise SomeException()

    assert not infinibox.api._preprocessors


def test_set_cookie(infinibox):
    # pylint: disable=protected-access
    infinibox.api.set_cookie('x', 'y')
    assert infinibox.api._session.cookies['x'] == 'y'


def test_get_cookie(infinibox):
    infinibox.api.set_cookie('x', 'y')
    assert infinibox.api.get_cookie('x') == 'y'

def test_delete_cookie(infinibox):
    # pylint: disable=protected-access
    infinibox.api.set_cookie('x', 'y')
    infinibox.api.delete_cookie('x')
    assert 'x' not in infinibox.api._session.cookies
