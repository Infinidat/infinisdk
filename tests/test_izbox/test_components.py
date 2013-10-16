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
        from infinipy2.core.system_component import System, Enclosure
        self.assertIs(self.system.components.types.System, System)
        self.assertIs(self.system.components.types.Enclosure, Enclosure)

    def test_system_component(self):
        system_component = self.system.components.systems.get()

    def test_cannot_get_system_component_by_id_lazily(self):
        with self.assertRaises(NotImplementedError):
            self.system.components.get_by_id_lazy(1)
