import forge
import gossip
from capacity import GB
from infinipy2.core.api import OMIT
from infinipy2.core.exceptions import APICommandFailed

from ..utils import TestCase

class SystemObjectHooksTest(TestCase):

    def setUp(self):
        super(SystemObjectHooksTest, self).setUp()
        self.forge = forge.Forge()
        self.pre_object_creation_hook = self.forge.create_wildcard_function_stub(name="pre")
        self.post_object_creation_hook = self.forge.create_wildcard_function_stub(name="post")
        self.object_operation_failure_hook = self.forge.create_wildcard_function_stub(name="fail")
        self.identifier = object()
        self.addCleanup(self._unregister)
        gossip.register(self.pre_object_creation_hook, 'pre_object_creation', self.identifier)
        gossip.register(self.post_object_creation_hook, 'post_object_creation', self.identifier)
        gossip.register(self.object_operation_failure_hook, 'object_operation_failure', self.identifier)

    def _unregister(self):
        gossip.unregister_token(self.identifier)

    def tearDown(self):
        self.forge.verify()
        super(SystemObjectHooksTest, self).tearDown()

    def test_creation_hook(self):
        self.pre_object_creation_hook(
            system=forge.Is(self.system),
            data=forge.HasKeyValue("name", "test_fs"),
            cls=self.system.objects.filesystems.object_type
            )
        self.post_object_creation_hook(
            obj=forge.And(forge.IsA(self.system.objects.filesystems.object_type),
                             forge.HasAttributeValue("system", self.system)),
            data=forge.HasKeyValue("name", "test_fs"),
            )
        self.forge.replay()
        self.system.objects.filesystems.create(name="test_fs", quota=GB)

    def test_creation_hook_failure(self):
        self.pre_object_creation_hook(
            system=forge.Is(self.system),
            data=forge.HasKeyValue("name", "test_fs"),
            cls=self.system.objects.filesystems.object_type
            )
        self.object_operation_failure_hook()
        self.forge.replay()
        with self.assertRaises(APICommandFailed):
            self.system.objects.filesystems.create(name="test_fs", quota=OMIT)
