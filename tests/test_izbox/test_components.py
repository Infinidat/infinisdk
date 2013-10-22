from ..utils import TestCase

class ComponentsTest(TestCase):

    API_SCENARIOS = ["izbox_component_queries"]

    def test_components_find(self):
        self.assertEquals(len(self.system.components.enclosures.find()), 8)

        self.assertEquals(0, len(self.system.components.enclosures.find(self.system.components.enclosures.fields.status != "OK")))

    def test_component_is_always_same_object(self):
        enclosures = self.system.components.enclosures
        candidates = [
            enclosures.get_by_id_lazy(102000),
            enclosures.get_by_id_lazy(102000),
            enclosures.get(id=102000),
            enclosures.get(id=102000),
            enclosures.safe_get(id=102000),
            ]
        self.assertEquals(
            len({id(x) for x in candidates}), 1,
            "Objects are unexpectedly recreated for each fetch"
        )

    def test_component_types(self):
        from infinipy2.izbox.components import System, Enclosure, EnclosureDrive
        self.assertIs(self.system.components.types.System, System)
        self.assertIs(self.system.components.types.Enclosure, Enclosure)
        self.assertIs(self.system.components.types.EnclosureDrive, EnclosureDrive)

    def test_components_choose(self):
        self.system.components.enclosures.choose()
        self.system.components.nodes.choose()

    def test_enclosure_drives(self):
        self.assertEquals(len(self.system.components.enclosure_drives.find()), 480) #capped for scenario maintainability

    def test_find_all_components(self):
        self.assertEquals(len(self.system.components.find()), 523)

    def test_system_component(self):
        system_component = self.system.components.systems.get()
        self.assertIs(system_component, self.system.components.system_component)

    def test_system_component_does_not_perform_api_get(self):
        self.system.api = None
        system_component = self.system.components.system_component
        self.assertEquals(system_component.id, 0)

    def test_system_get_primary_secondary_nodes(self):
        self.assertIs(self.system.components.system_component.get_primary_node(), self.system.components.nodes.get(index=1))
        self.assertIs(self.system.components.system_component.get_secondary_node(), self.system.components.nodes.get(index=2))

        for is_primary, node in [
                (True, self.system.components.system_component.get_primary_node()),
                (False, self.system.components.system_component.get_secondary_node())
        ]:
            self.assertEquals(is_primary, node.is_primary())
            self.assertEquals(not is_primary, node.is_secondary())

    def test_cannot_get_system_component_by_id_lazily(self):
        with self.assertRaises(NotImplementedError):
            self.system.components.get_by_id_lazy(1)
