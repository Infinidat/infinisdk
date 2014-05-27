from ..utils import InfiniBoxTestCase
import random
from infinipy2.core.config import config

NO_OF_ENCLOSURES_DRIVES = config.get_path('infinibox.defaults.enlosure_drives.total_count.mock')

get_id = lambda obj: obj.get_id()
get_state = lambda obj: obj.get_state()

class ComponentsTest(InfiniBoxTestCase):
    def test_get_all_items_of_specific_component(self):
        enclosures = self.system.components.enclosures
        self.assertEquals(len(enclosures.find()), 8)
        self.assertEquals(set(enclosures.find()), set(enclosures.get_all()))

    def test_get_all_items_of_all_the_components(self):
        found_components = self.system.components.find()
        all_components = self.system.components.get_all()

        self.assertGreater(len(found_components), NO_OF_ENCLOSURES_DRIVES)
        self.assertGreater(len(all_components), NO_OF_ENCLOSURES_DRIVES)
        self.assertEqual(list(found_components), list(all_components))

    def test_sort_results_asc(self):
        enclosures = self.system.components.enclosures
        sorting = enclosures.find().sort(+enclosures.object_type.fields.id)

        sorted_enclosures = sorted(enclosures.find(), key=get_id, reverse=False)
        self.assertEqual(sorted_enclosures, list(sorting))

    def test_sort_results_desc(self):
        enclosures = self.system.components.enclosures
        sorting = enclosures.find().sort(-enclosures.object_type.fields.id)

        sorted_enclosures = sorted(enclosures.find(), key=get_id, reverse=True)
        self.assertEqual(sorted_enclosures, list(sorting))

    def test_sort_results_where_key_is_equal(self):
        enclosures = self.system.components.enclosures
        sorting = enclosures.find().sort(+enclosures.object_type.fields.state)

        sorted_enclosures = sorted(enclosures.find(), key=get_state)
        self.assertEqual(sorted_enclosures, list(sorting))

    def test_filter_with_predicates(self):
        services = self.system.components.services
        for service in services.find(services.fields.state == "ACTIVE"):
            self.assertEquals(service.get_state(), "ACTIVE")

    def test_filter_with_kw(self):
        services = self.system.components.services
        for service in services.find(state="ACTIVE"):
            self.assertEquals(service.get_state(), "ACTIVE")

    def test_get_length(self):
        found_components = self.system.components.find()
        self.assertEqual(len(found_components), len(list(found_components)))

    def test_get_item_negative_path(self):
        query = self.system.components.enclosures.find()
        with self.assertRaises(NotImplementedError):
            query[-4]
        with self.assertRaises(IndexError):
            query[1000]

    def test_get_item(self):
        enclosures = self.system.components.enclosures.get_all()[:]
        enc1 = random.choice(enclosures)
        enclosures.remove(enc1)
        enc2 = random.choice(enclosures)
        Enclosure = self.system.components.enclosures.object_type

        self.assertTrue(isinstance(enc1, Enclosure))
        self.assertTrue(isinstance(enc2, Enclosure))
        self.assertNotEqual(enc1, enc2)
