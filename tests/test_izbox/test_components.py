import pytest
from infinisdk._compat import string_types
from ..conftest import disable_api_context


def test_components_find(izbox):
    assert len(izbox.components.enclosures.find()) == 8

    assert 0 == len(izbox.components.enclosures.find(
        izbox.components.enclosures.fields.status != 'OK'))


def test_component_is_always_same_object(izbox):
    enclosures = izbox.components.enclosures
    candidates = [
        enclosures.get_by_id_lazy(102000),
        enclosures.get_by_id_lazy(102000),
        enclosures.get(id=102000),
        enclosures.get(id=102000),
        enclosures.safe_get(id=102000),
    ]
    assert len(set((id(x) for x in candidates))
               ) == 1, 'Objects are unexpectedly recreated for each fetch'


def test_component_types(izbox):
    from infinisdk.izbox.components import System, Enclosure, EnclosureDrive
    assert izbox.components.types.System is System
    assert izbox.components.types.Enclosure is Enclosure
    assert izbox.components.types.EnclosureDrive is EnclosureDrive


def test_components_getitem(izbox):
    assert izbox.components['nodes'] is izbox.components.nodes
    assert izbox.components[
        izbox.components.types.Node] is izbox.components['nodes']
    with pytest.raises(KeyError):
        izbox.components['fake_component']


def test_components_choose(izbox):
    enc = izbox.components.enclosures.choose()
    node = izbox.components.nodes.choose()
    assert enc.is_ok()
    assert node.is_ok()


def test_enclosure_drives(izbox):
    # capped for scenario maintainability
    assert len(izbox.components.enclosure_drives.find()) == 480


def test_find_all_components(izbox):
    assert len(izbox.components.find()) > 480


def test_system_component(izbox):
    system_component = izbox.components.systems.get()
    assert system_component is izbox.components.system_component
    assert 'system_serial' in system_component.get_additional_data()


def test_system_component_does_not_perform_api_get(izbox):
    with disable_api_context(izbox):
        system_component = izbox.components.system_component
        assert system_component.id == 0


def test_system_get_primary_secondary_nodes(izbox):
    assert izbox.components.system_component.get_primary_node() is izbox.components.nodes.get(index=1)
    assert izbox.components.system_component.get_secondary_node() is izbox.components.nodes.get(index=2)

    for is_primary, node in [
            (True, izbox.components.system_component.get_primary_node()),
            (False, izbox.components.system_component.get_secondary_node())
    ]:
        assert is_primary == node.is_primary()
        assert (not is_primary) == node.is_secondary()


def test_cannot_get_system_component_by_id_lazily(izbox):
    with pytest.raises(NotImplementedError):
        izbox.components.get_by_id_lazy(1)


def test_get_alert_types(izbox):
    alert_types = izbox.components.get_alert_types()
    assert isinstance(alert_types, list)
    assert alert_types[0].get('code') is not None


def test_get_component_alert(izbox):
    node = izbox.components.nodes.choose()
    alerts = node.get_alerts()
    assert alerts == []


def test_get_data(izbox):
    node = izbox.components.nodes.choose()
    data = node.get_data()
    assert data == {}


def test_get_type_info_from_system(izbox):
    type_info = izbox.components.get_type_infos_from_system()
    assert 'node' in type_info


def test_get_parent_and_sub_components(izbox):
    enc = izbox.components.enclosures.choose()
    with pytest.raises(NotImplementedError):
        enc.get_parent()

    rack_1 = izbox.components.racks.choose()
    enc_parent = enc.get_parent()
    assert rack_1 == enc_parent
    assert enc in rack_1.get_sub_components()


def test_get_node_address(izbox):
    node = izbox.components.nodes.choose()
    node_address = node.get_address()
    assert isinstance(node_address, string_types)


def test_service(izbox):
    service = izbox.components.services.choose()
    assert isinstance(service.get_name(), string_types)
