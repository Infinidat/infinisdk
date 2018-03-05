import pytest
import logbook
import random
from infinisdk import Q
from infinisdk.core.config import config
from infinisdk.core.exceptions import ObjectNotFound
from infinisdk.infinibox.components import Enclosure, Node

NO_OF_ENCLOSURES_DRIVES = config.get_path('infinibox.defaults.enlosure_drives.total_count.mock')

get_api_id = lambda obj: obj.get_api_id()
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
    sorting = enclosures.find().sort(+enclosures.object_type.fields.api_id)

    sorted_enclosures = sorted(enclosures.find(), key=get_api_id, reverse=False)
    assert sorted_enclosures == list(sorting)

def test_sort_results_desc(infinibox):
    enclosures = infinibox.components.enclosures
    sorting = enclosures.find().sort(-enclosures.object_type.fields.api_id)

    sorted_enclosures = sorted(enclosures.find(), key=get_api_id, reverse=True)
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

def test_filter_with_Q_predicates(infinibox):
    services = infinibox.components.services
    for service in services.find(Q.state == "ACTIVE"):
        assert service.get_state() == 'ACTIVE'

def test_filtering_by_special_operators(infinibox):
    query = infinibox.components.services.find(Q.name.like('cor'))
    with pytest.raises(NotImplementedError):
        list(query)

def test_get_length(infinibox):
    found_components = infinibox.components.find()
    assert len(found_components) == len(list(found_components))

def test_get_item_negative_path(infinibox):
    query = infinibox.components.enclosures.find()
    with pytest.raises(NotImplementedError):
        query[-4]  # pylint: disable=pointless-statement
    with pytest.raises(IndexError):
        query[1000]  # pylint: disable=pointless-statement

def test_get_item(infinibox):
    enclosures = infinibox.components.enclosures.get_all()[:]
    enc1 = random.choice(enclosures)
    enclosures.remove(enc1)
    enc2 = random.choice(enclosures)

    assert isinstance(enc1, Enclosure)
    assert isinstance(enc2, Enclosure)
    assert enc1 != enc2

def test_rack_refresh(infinibox):
    # pylint: disable=protected-access
    components = infinibox.components
    comp_no = len(components._components_by_id)
    rack_1 = components.get_rack_1()

    # Currently only Rack#1 & System Component
    assert comp_no == 2
    assert not any(isinstance(comp, (Node, Enclosure)) for comp in components._components_by_id)

    nodes_no = len(components.nodes)
    comp_with_nodes_no = len(components._components_by_id)
    assert comp_no + nodes_no < comp_with_nodes_no
    assert not any(isinstance(comp, Enclosure) for comp in components._components_by_id)

    rack_1.refresh_cache()
    assert comp_with_nodes_no < len(components._components_by_id)

@pytest.mark.parametrize('operation', [
    lambda infinibox: list(infinibox.components.nodes.find(state='fakeone')),
    lambda infinibox: infinibox.components.nodes.safe_get(state='fakeone')
])
def test_len_caching_on_empty_lists(infinibox, operation):
    with logbook.TestHandler() as handler:
        result = operation(infinibox)
        assert not result

    [r] = [record for record in handler.records if '<-- GET http://' in record.message] # pylint: disable=unused-variable

def test_system_component_find(infinibox):
    for component_type_name in infinibox.components.get_component_type_names():
        assert infinibox.components[component_type_name + "s"].find().to_list() == \
            infinibox.components.find(component_type=component_type_name).to_list()

def test_system_component_find_with_params(infinibox):
    assert infinibox.components.nodes.find(index=2).to_list() == \
        infinibox.components.find(component_type='node', index=2).to_list()

def test_system_component_find_no_type(infinibox):
    fetched_types = set(type(component) for component in infinibox.components.find())
    for component_type in infinibox.components.get_component_types():
        if component_type.get_type_name() == 'ib_port':
            if infinibox.compat.normalize_version_string('3.0') > infinibox.compat.get_parsed_system_version():
                continue
        assert(component_type in fetched_types)

@pytest.mark.parametrize('id_field', ['id', 'uid'])
def test_component_not_found(infinibox, id_field):
    rack_id = infinibox.components.get_rack_1().id
    with pytest.raises(ObjectNotFound) as caught:
        infinibox.components.fc_ports.get(Q.parent_id == rack_id, **{id_field: 'fake_id'})
    exc_msg = str(caught.value)
    assert '(uid=fake_id)' in exc_msg
    assert '(parent_id={})'.format(rack_id) in exc_msg


def test_component_sample(infinibox):
    nodes = infinibox.components.nodes.sample(Q.index != 1, sample_count=2)
    assert set(node.get_index() for node in nodes) == set([2, 3])
