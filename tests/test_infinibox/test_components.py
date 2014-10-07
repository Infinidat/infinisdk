import pytest

import waiting
from infinisdk._compat import string_types
from infinisdk.core.config import config
from infinibox_sysdefs import latest as defs
from infinisdk.infinibox.components import (Drive, Enclosure, FcPort, Node,
                                            Rack, Service, System, ServiceCluster)

NO_OF_ENCLOSURES_DRIVES = config.get_path('infinibox.defaults.enlosure_drives.total_count.simulator')


def test_component_id_field(infinibox, component_collection, component):
    assert isinstance(component.id, str)
    assert component.get_field('id') == component.id
    assert component_collection.get_by_id(component.id) is component


def _basic_check_for_component(infinibox, component_type, parent_type, check_sub_components):
    sys_components = infinibox.components
    from_types_list = getattr(sys_components.types, component_type.__name__)
    assert from_types_list is component_type

    assert component_type.fields.get('index') is not None

    collection = sys_components[component_type.get_plural_name()]
    component_instances = collection.get_all()

    is_component_instance = lambda obj: isinstance(obj, component_type)
    assert all(map(is_component_instance, component_instances))

    component_instance = collection.choose()

    if parent_type:
        parent_obj = component_instance.get_parent()
        assert isinstance(parent_obj, parent_type)

    if check_sub_components:
        sub_components = component_instance.get_sub_components()
        is_sub_component = lambda obj: is_component_instance(obj.get_parent())
        assert all(map(is_sub_component, sub_components))

def test_system_component_does_not_perform_api_get(infinibox):
    infinibox.api = None
    system_component = infinibox.components.system_component
    assert system_component.get_index() == 0

def test_system_component(infinibox):
    _basic_check_for_component(infinibox, System, None, False)
    system_component = infinibox.components.system_component
    assert system_component is infinibox.components.systems.get()
    assert isinstance(system_component.get_state(), string_types)

def test_rack_component(infinibox):
    _basic_check_for_component(infinibox, Rack, None, True)

def test_enclosure_component(infinibox):
    _basic_check_for_component(infinibox, Enclosure, Rack, True)
    enc = infinibox.components.enclosures.choose()
    assert isinstance(enc.get_state(), string_types)

def test_drive_component(infinibox):
    _basic_check_for_component(infinibox, Drive, Enclosure, False)
    all_drives = infinibox.components.drives.find()
    assert len(all_drives) == NO_OF_ENCLOSURES_DRIVES

def test_fc_port_component(infinibox):
    _basic_check_for_component(infinibox, FcPort, Node, False)

def test_node_component(infinibox):
    _basic_check_for_component(infinibox, Node, Rack, True)
    node = infinibox.components.nodes.choose()
    assert isinstance(node.get_state(), string_types)
    assert all(isinstance(service, Service) for service in node.get_services())
    assert [node.get_service('core')] == [service for service in node.get_services() if service.get_name() == 'core']

def test_service_component(infinibox):
    _basic_check_for_component(infinibox, Service, Node, False)

def test_service_cluster(infinibox):
    _basic_check_for_component(infinibox, ServiceCluster, None, False)
    service_cluster = infinibox.components.service_clusters.choose()
    assert isinstance(service_cluster.get_state(from_cache=False), string_types)
    service = infinibox.components.services.choose(name=service_cluster.get_name())
    assert service.get_service_cluster() is service_cluster
    assert service in service_cluster.get_services()
    assert all(isinstance(service, Service) for service in service_cluster.get_services())

def test_node_phase(infinibox):
    node = infinibox.components.nodes.choose()
    node.phase_out()
    waiting.wait(lambda: node.get_state() == defs.enums.nodes.states.ready)
    node.phase_in()
    waiting.wait(lambda: node.get_state() == defs.enums.nodes.states.active)

def test_get_all_first_drives(infinibox):
    drives_list = infinibox.components.drives.find(index=1)
    enclosures = infinibox.components.enclosures
    assert len(drives_list) == len(enclosures.get_all())
    get_expected_drive_id = lambda enc: 'system:0_rack:1_enclosure:{0}_drive:1'.format(enc.get_index())
    assert set(get_expected_drive_id(enc) for enc in enclosures) == set(drive.get_id() for drive in drives_list)

def test_get_index(infinibox):
    node = infinibox.components.nodes.get(index=3)
    assert node.get_index() == 3
    assert node.get_id() == 'system:0_rack:1_node:3'


@pytest.fixture(params=['racks', 'nodes', 'enclosures'])
def component_collection(request, infinibox):
    return getattr(infinibox.components, request.param)

@pytest.fixture
def component(infinibox, component_collection):
    return list(component_collection)[0]
