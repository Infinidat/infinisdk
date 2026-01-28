import responses

from tests.test_infinibox.mock_infinibox.mock_initiator import (
    MOCK_GET_COMPONENTS,
    MOCK_GET_INITIATOR_BY_ADDRESS,
    MOCK_GET_INITIATOR_NOT_FOUND,
)


def test_initiators_sanity(infinibox):
    assert isinstance(infinibox.initiators.to_list(), list)


def test_mocked_get_initiator_by_address(mocked_infinibox_api, mocked_infinibox):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.GET,
        url="http://ibox3441:80/api/rest/initiators/iqn.1993-08.org.debian%3A01%3A515ccce1836",
        json=MOCK_GET_INITIATOR_BY_ADDRESS,
    )
    add_mock(
        method=responses.GET,
        url="http://ibox3441:80/api/rest/components?fields=rack%2Cnodes%2Cups%2Cpdus",
        json=MOCK_GET_COMPONENTS,
    )

    initiator = mocked_infinibox.initiators.get_by_address(
        "iqn.1993-08.org.debian:01:515ccce1836"
    )

    assert initiator.get_address() == "iqn.1993-08.org.debian:01:515ccce1836"


def test_mocked_get_initiator_get_by_id(mocked_infinibox_api, mocked_infinibox):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.GET,
        url="http://ibox3441:80/api/rest/initiators/iqn.1993-08.org.debian%3A01%3A515ccce1836",
        json=MOCK_GET_INITIATOR_BY_ADDRESS,
    )
    add_mock(
        method=responses.GET,
        url="http://ibox3441:80/api/rest/components?fields=rack%2Cnodes%2Cups%2Cpdus",
        json=MOCK_GET_COMPONENTS,
    )

    initiator = mocked_infinibox.initiators.get_by_id(
        "iqn.1993-08.org.debian:01:515ccce1836"
    )

    assert initiator.get_address() == "iqn.1993-08.org.debian:01:515ccce1836"


def test_mocked_get_initiator_safe_get_by_id(mocked_infinibox_api, mocked_infinibox):
    add_mock, _ = mocked_infinibox_api
    add_mock(
        method=responses.GET,
        url="http://ibox3441:80/api/rest/initiators/iqn.1993-08.org.debian%3A01%3A515ccce183611",
        json=MOCK_GET_INITIATOR_NOT_FOUND,
        status=400,
    )

    initiator = mocked_infinibox.initiators.safe_get_by_id(
        "iqn.1993-08.org.debian:01:515ccce183611"
    )

    assert initiator == None
