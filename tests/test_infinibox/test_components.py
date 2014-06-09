import pytest
from infinipy2._compat import string_types
from infinipy2.core.config import config
from infinipy2.infinibox.components import (Drive, Enclosure, FcPort, Node,
                                            Rack, Service, System)

NO_OF_ENCLOSURES_DRIVES = config.get_path('infinibox.defaults.enlosure_drives.total_count.simulator')


def _basic_check_for_component(infinibox, component_type, parent_type, check_sub_components):
    sys_components = infinibox.components
    from_types_list = getattr(sys_components.types, component_type.__name__)
    assert from_types_list is component_type

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

def test_get_component_by_id_lazily(infinibox):
    rack_1_id = ('system', 0, 'rack', 1)
    with pytest.raises(NotImplementedError):
        infinibox.components.get_by_id_lazy(rack_1_id)
    infinibox.components.enclosures.choose()  # Initializing components...

    component = infinibox.components.get_by_id_lazy(rack_1_id)
    assert component.get_index() == 1
    assert component.get_type_name() == 'rack'

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

def test_service_component(infinibox):
    _basic_check_for_component(infinibox, Service, Node, False)
