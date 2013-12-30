from ..utils import InfiniBoxTestCase
from infinipy2._compat import iteritems
from logbook import Logger

_logger = Logger(__name__)


class InfiniBoxSystemTest(InfiniBoxTestCase):

    def test_get_api_auth(self):
        self.assertEqual(self.system.get_api_auth(), ('infinidat', '123456'))

    def test_get_api_timeout(self):
        self.assertEqual(self.system.get_api_timeout(), 30)

    def test_multiple_metadata_creation(self):
        volume = self._create_volume()
        metadata_d = {'some_key':  'some_value',
                      'other_key': 'other_value',
                      'last_key':  'last_value'}
        for k, v in iteritems(metadata_d):
            volume.set_metadata(k, v)

        all_metadata = volume.get_all_metadata()
        self.assertEqual(len(all_metadata), len(metadata_d))
        self.assertEqual(all_metadata, metadata_d)

        metadata_val = volume.get_metadata_value('other_key')
        self.assertEqual(metadata_val, 'other_value')

        volume.unset_metadata('some_key')
        all_metadata = volume.get_all_metadata()
        self.assertEqual(len(all_metadata), len(metadata_d)-1)
        metadata_d.pop('some_key')
        self.assertEqual(all_metadata, metadata_d)

        volume.clear_metadata()
        self.assertEqual(len(volume.get_all_metadata()), 0)

    def _validate_single_metadata_support(self, obj):
        _logger.debug("Validating {0}'s metadata support", type(obj).__name__)
        key, value = 'some_key', 'some_value'
        obj.set_metadata(key, value)
        all_metadata = obj.get_all_metadata()

        self.assertEqual(len(all_metadata), 1)
        self.assertEqual(all_metadata, {key: value})
        self.assertEqual(obj.get_metadata_value(key), value)
        obj.unset_metadata(key)
        self.assertEqual(len(obj.get_all_metadata()), 0)

    def test_single_metadata_creation_on_all_infinibox_objects(self):
        ignore_types = ['volumes', 'users']

        type_classes = [obj_type for obj_type in self.system.OBJECT_TYPES
                        if obj_type.get_plural_name() not in ignore_types]

        vol = self._create_volume()
        self._validate_single_metadata_support(vol)

        for type_class in type_classes:
            obj = type_class.create(self.system)
            self._validate_single_metadata_support(obj)
