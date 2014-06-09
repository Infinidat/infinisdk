import pytest
import random
from infinisdk.core.config import config

NO_OF_ENCLOSURES_DRIVES = config.get_path('infinibox.defaults.enlosure_drives.total_count.mock')

get_id = lambda obj: obj.get_id()
get_state = lambda obj: obj.get_state()

def test_get_all_items_of_specific_component(infinibox):
    enclosures = infinibox.components.enclosures
    assert len(enclosures.find()) == 8
    assert set(enclosures.find()) == set(enclosures.get_all())

def test_get_all_items_of_all_the_components(infinibox):
    found_components = infinibox.components.find()
    all_components = infinibox.components.get_all()

    assert len(found_components) > NO_OF_ENCLOSURES_DRIVES
    assert len(all_components) > NO_OF_ENCLOSURES_DRIVES
    assert list(found_components) == list(all_components)

def test_sort_results_asc(infinibox):
    enclosures = infinibox.components.enclosures
    sorting = enclosures.find().sort(+enclosures.object_type.fields.id)

    sorted_enclosures = sorted(enclosures.find(), key=get_id, reverse=False)
    assert sorted_enclosures == list(sorting)

def test_sort_results_desc(infinibox):
    enclosures = infinibox.components.enclosures
    sorting = enclosures.find().sort(-enclosures.object_type.fields.id)

    sorted_enclosures = sorted(enclosures.find(), key=get_id, reverse=True)
    assert sorted_enclosures == list(sorting)

def test_sort_results_where_key_is_equal(infinibox):
    enclosures = infinibox.components.enclosures
    sorting = enclosures.find().sort(+enclosures.object_type.fields.state)

    sorted_enclosures = sorted(enclosures.find(), key=get_state)
    assert sorted_enclosures == list(sorting)

def test_filter_with_predicates(infinibox):
    services = infinibox.components.services
    for service in services.find(services.fields.state == "ACTIVE"):
        assert service.get_state() == 'ACTIVE'

def test_filter_with_kw(infinibox):
    services = infinibox.components.services
    for service in services.find(state="ACTIVE"):
        assert service.get_state() == 'ACTIVE'

def test_get_length(infinibox):
    found_components = infinibox.components.find()
    assert len(found_components) == len(list(found_components))

def test_get_item_negative_path(infinibox):
    query = infinibox.components.enclosures.find()
    with pytest.raises(NotImplementedError):
        query[-4]
    with pytest.raises(IndexError):
        query[1000]

def test_get_item(infinibox):
    enclosures = infinibox.components.enclosures.get_all()[:]
    enc1 = random.choice(enclosures)
    enclosures.remove(enc1)
    enc2 = random.choice(enclosures)
    Enclosure = infinibox.components.enclosures.object_type

    assert isinstance(enc1, Enclosure)
    assert isinstance(enc2, Enclosure)
    assert enc1 != enc2
