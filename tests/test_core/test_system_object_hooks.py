from capacity import GB
from forge import And, HasKeyValue, Is, IsA, HasAttributeValue

import gossip
import pytest
from infinipy2.core.api import OMIT
from infinipy2.core.exceptions import APICommandFailed


@pytest.fixture
def hooks(forge, request):

    class Hooks(object):
        pass

    identifier = object()

    returned = Hooks()
    returned.pre_object_creation_hook = forge.create_wildcard_function_stub(
        name="pre")
    returned.post_object_creation_hook = forge.create_wildcard_function_stub(
        name="post")
    returned.object_operation_failure_hook = forge.create_wildcard_function_stub(
        name="fail")

    gossip.register(returned.pre_object_creation_hook,
                    'infinidat.pre_object_creation', identifier)
    gossip.register(returned.post_object_creation_hook,
                    'infinidat.post_object_creation', identifier)
    gossip.register(returned.object_operation_failure_hook,
                    'infinidat.object_operation_failure', identifier)

    @request.addfinalizer
    def cleanup():
        gossip.unregister_token(identifier)

    return returned


def test_creation_hook(hooks, forge, izbox):
    hooks.pre_object_creation_hook(
        system=Is(izbox),
        data=HasKeyValue("name", "test_fs"),
        cls=izbox.objects.filesystems.object_type
    )
    hooks.post_object_creation_hook(
        obj=And(
            IsA(izbox.objects.filesystems.object_type),
            HasAttributeValue("system", izbox)),
        data=HasKeyValue("name", "test_fs"),
    )
    forge.replay()
    izbox.objects.filesystems.create(name="test_fs", quota=GB)

def test_creation_hook_failure(hooks, forge, izbox):
    hooks.pre_object_creation_hook(
        system=Is(izbox),
        data=HasKeyValue("name", "test_fs"),
        cls=izbox.objects.filesystems.object_type
    )
    hooks.object_operation_failure_hook()
    forge.replay()
    with pytest.raises(APICommandFailed):
        izbox.objects.filesystems.create(name="test_fs", quota=OMIT)
