

def test_get_last_events(system):
    events = system.events.get_last_events(1)
    assert len(events) == 1
    assert isinstance(events[0].get_id(), int)


def test_get_last_events_with_reversed_param(system):
    # Ensuring that there are at least 2 events
    event1 = system.events.create_custom_event(description='Custom 1')
    event2 = system.events.create_custom_event(description='Custom 2')

    regular_events = system.events.get_last_events(2, False)
    reversed_events = system.events.get_last_events(2, True)

    assert len(regular_events) == 2
    assert len(reversed_events) == 2
    assert event1['id'] == regular_events[0].id
    assert event2['id'] == regular_events[1].id
    assert regular_events[0] == reversed_events[1]
    assert regular_events[1] == reversed_events[0]


def test_get_events(system):
    custom_event = system.events.create_custom_event(description='')
    events = system.events.get_events(min_event_id=custom_event['id'] + 1)
    assert len(events) == 0

    events = system.events.get_events(min_event_id=custom_event['id'])
    assert len(events) == 1


def test_get_levels(system):
    assert 'CRITICAL' in system.events.get_levels()


def test_get_visibilities(system):
    expected = set(['CUSTOMER', 'INFINIDAT'])
    assert set(system.events.get_visibilities()) == expected


def test_get_reporters(system):
    assert len(system.events.get_reporters()) > 0


def test_between_operator(system):
    min_id, max_id = 1, 3
    id_field = system.events.fields.get('id')
    id_filter = id_field.__between__((min_id, max_id))
    events = list(system.events.find(id_filter))

    range_validator = lambda event: event.id <= max_id and event.id >= min_id

    assert len(events) <= ((max_id - min_id) + 1)
    assert all(range_validator(event) for event in events)


def test_complex_queries(system):
    min_index, max_index = 1, 2
    events = [system.events.create_custom_event() for _ in range(5)]

    id_field = system.events.fields.get('id')
    id_range = (events[min_index]['id'], events[max_index]['id'])
    id_filter = id_field.__between__(id_range)

    Event = system.events.object_type
    kwargs = dict(level=events[0]['level'],
                  reporter=events[0]['reporter'],
                  code=events[0]['code'])
    filtered_events = system.events.find(id_filter, **kwargs)
    results = list(filtered_events.sort(-Event.fields.id))

    assert len(results) == ((max_index - min_index) + 1)
    assert events[min_index]['id'] == results[(-1)].id
    assert events[max_index]['id'] == results[0].id


def test_events_types_caching(system, forge):
    mock = forge.replace(system.events, '_get_events_types_from_system')
    mock().and_return({'codes': [], 'levels': []})
    forge.replay()

    assert system.events._types is None  # pylint: disable=protected-access
    system.events.get_codes()

    assert system.events._types is not None  # pylint: disable=protected-access
    system.events.get_codes()
    system.events.get_levels()


def test_events_collection(system):
    event = system.events.get_last_event()
    assert event.get_collection() is system.events
    assert event.get_binder() is system.events
