import pytest


def test_create_custom_event(infinibox):
    description = 'test events'
    event_from_post = infinibox.events.create_custom_event(
        description=description)
    event_from_list = infinibox.events.get_last_events(1)[0].get_fields()
    assert event_from_post['description'] == description
    assert event_from_list['description'] == description
    assert event_from_list['code'] == 'CUSTOM_INFO_EVENT'


def test_create_custom_event_with_data(infinibox):
    description = 'test events - {param}'
    event_data = dict(name='param', value='bla', type="string")
    event_from_post = infinibox.events.create_custom_event(
        description=description,
        data=[event_data])

    data_from_post = event_from_post['data'][0]
    assert event_data['name'] == data_from_post['name']
    assert event_data['type'] == data_from_post['type']
    assert event_data['value'] == data_from_post['value']

    event_from_list = infinibox.events.get_last_event().get_fields()
    description = description.replace("{param}", event_data["value"])
    assert event_from_post['description'] == description
    assert event_from_list['description'] == description
    assert event_from_list['code'] == 'CUSTOM_INFO_EVENT'


def test_get_name(infinibox, rule):
    assert rule.get_name().startswith('rule_')


def test_get_all(infinibox, rule):
    assert rule in infinibox.emailrules.get_all()


@pytest.fixture
def rule(request, infinibox):
    returned = infinibox.emailrules.create()
    request.addfinalizer(returned.delete)
    return returned
