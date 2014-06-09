from infinipy2._compat import xrange


def test_create_custom_event(izbox):
    description = 'test events'
    event_from_post = izbox.events.create_custom_event(
        description=description)
    event_from_list = izbox.events.get_last_events(1)[0].get_fields()
    assert event_from_post['description'] == description
    assert event_from_list['description'] == description
    assert event_from_list['code'] == 'CUSTOM_EVENT_INFO'


def test_create_custom_event_with_data(izbox):
    description = 'test events - {param}'
    data = dict(param=10)
    event_from_post = izbox.events.create_custom_event(
        description=description, data=data)
    actual_data = event_from_post['data'][0]
    assert actual_data['name'] == 'param'
    assert actual_data['value'] == 10
    assert actual_data['type'] in 'int'


def test_get_event_by_uuid(izbox):
    custom_event = izbox.events.create_custom_event(
        description='test event')
    event = izbox.events.get_event_by_uuid(custom_event['uuid'])
    assert event['uuid'] == custom_event['uuid']


def test_event_fields_operators(izbox):
    for index in xrange(5):
        custom_event = izbox.events.create_custom_event(
            description='test event')
    event = izbox.events.get_last_event()

    # Test: get_last_event & __getitem__
    assert event['uuid'] == custom_event['uuid']
    assert 'uuid' in event
    assert 'fake_field_name' not in event
    keys = event.keys()
    assert len(event), len(keys)
    assert set(keys) == set((k for k in event))


def test_codes(izbox):
    codes = izbox.events.get_codes()
    assert len(codes) > 0

    codes_list = izbox.events.get_codes_list()
    assert any(('USER_CREATED' == code for code in codes_list))


def test_get_codes_description_list(izbox):
    codes_description_list = izbox.events.get_codes_description_list()
    assert len(codes_description_list) > 0
