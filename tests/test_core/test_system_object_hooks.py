from forge import And, HasKeyValue, Is, IsA, HasAttributeValue

import gossip
import pytest
from infinisdk.core.api import OMIT
from infinisdk.core.exceptions import APICommandFailed

# pylint: disable=redefined-outer-name

@pytest.fixture
def hooks(forge, request):

    class Hooks(object):
        pass

    identifier = object()

    returned = Hooks()
    returned.pre_object_creation_hook = forge.create_wildcard_function_stub(
        name="pre_hook")
    returned.post_object_creation_hook = forge.create_wildcard_function_stub(
        name="post_hook")
    returned.object_operation_failure_hook = forge.create_wildcard_function_stub(
        name="fail_hook")

    gossip.register(returned.pre_object_creation_hook,
                    'infinidat.sdk.pre_object_creation', identifier)
    gossip.register(returned.post_object_creation_hook,
                    'infinidat.sdk.post_object_creation', identifier)
    gossip.register(returned.object_operation_failure_hook,
                    'infinidat.sdk.object_operation_failure', identifier)

    @request.addfinalizer
    def cleanup():
        gossip.unregister_token(identifier)

    return returned


def test_creation_hook(hooks, forge, infinibox):
    hooks.pre_object_creation_hook(
        system=Is(infinibox),
        data=HasKeyValue("name", "test_pool"),
        cls=infinibox.pools.object_type
    )
    hooks.post_object_creation_hook(
        obj=And(
            IsA(infinibox.pools.object_type),
            HasAttributeValue("system", infinibox)),
        data=HasKeyValue("name", "test_pool"),
        response_dict=HasKeyValue("name", "test_pool"),
    )
    forge.replay()
    infinibox.pools.create(name="test_pool")


def test_creation_hook_failure(hooks, forge, infinibox):
    failure_hook_kwargs = {}

    hooks.pre_object_creation_hook(
        system=Is(infinibox),
        data=HasKeyValue("name", "test_pool"),
        cls=infinibox.pools.object_type
    )
    hooks.object_operation_failure_hook(exception=IsA(APICommandFailed)).\
        and_call_with_args(failure_hook_kwargs.update)

    forge.replay()
    with pytest.raises(APICommandFailed) as caught:
        infinibox.pools.create(name="test_pool", capacity=OMIT)

    assert caught.value is failure_hook_kwargs['exception']
