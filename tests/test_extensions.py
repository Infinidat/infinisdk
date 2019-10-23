import itertools

import pytest
from infinisdk.core import extensions
from infinisdk.infinibox import InfiniBox
from infinisdk.infinibox.system_object import SystemObject
from infinisdk.infinibox.volume import Volume

# pylint: disable=unused-variable, unused-argument

def test_no_extensions_by_default():
    assert len(extensions.active) == 0


@pytest.mark.parametrize('different_name', [True, False])
def test_extending(infinibox, different_name):
    with pytest.raises(AttributeError):
        infinibox.new_method  # pylint: disable=pointless-statement

    if different_name:
        @extensions.add_method(InfiniBox, 'new_method')
        def some_other_name(self, a, b, c):
            return "{} {} {} {}".format(type(self).__name__, a, b, c)

    else:
        @extensions.add_method(InfiniBox)
        def new_method(self, a, b, c):
            return "{} {} {} {}".format(type(self).__name__, a, b, c)

    assert infinibox.new_method(1, 2, 3) == 'InfiniBox 1 2 3'
    assert infinibox.new_method.__self__ is infinibox
    assert infinibox.new_method.im_self is infinibox
    assert infinibox.new_method.im_class is type(infinibox)
    if different_name:
        assert infinibox.new_method.im_func is some_other_name
    else:
        assert infinibox.new_method.im_func is new_method


@pytest.mark.parametrize('different_name', [True, False])
def test_overriding(infinibox, different_name):
    original = type(infinibox).get_version
    if different_name:
        @extensions.wrap_method(InfiniBox, 'get_version')
        def some_other_name(self, _wrapped):
            assert _wrapped is original
            return 9999
    else:
        @extensions.wrap_method(InfiniBox)
        def get_version(self, _wrapped):
            assert _wrapped is original
            return 9999

    assert infinibox.get_version() == 9999
    assert infinibox.get_version.__self__ is infinibox
    assert infinibox.get_version.im_self is infinibox
    assert infinibox.get_version.im_class is type(infinibox)
    if different_name:
        assert infinibox.get_version.im_func is some_other_name
    else:
        assert infinibox.get_version.im_func is get_version


@pytest.mark.parametrize('different_name', [True, False])
def test_overriding_non_exiting(infinibox, different_name):
    with pytest.raises(RuntimeError):
        if different_name:
            @extensions.wrap_method(InfiniBox, 'get_version_ex')
            def some_other_name(self, _wrapped):
                assert _wrapped
                return 9999
        else:
            @extensions.wrap_method(InfiniBox)
            def get_version_ex(self, _wrapped):
                assert _wrapped
                return 9999


def test_add_attribute(infinibox):
    assert not hasattr(infinibox, 'attached')

    @extensions.add_attribute(type(infinibox))
    def attached(self):
        return 'value'

    assert infinibox.attached == 'value'


def test_add_attribute_computed_once(infinibox):
    assert not hasattr(infinibox, 'attached')
    counter = itertools.count()

    @extensions.add_attribute(type(infinibox))
    def attached(self):
        return next(counter)

    for i in range(3):
        assert infinibox.attached == 0

def test_add_attribute_for_class_with_multiple_instances(infinibox):
    assert not hasattr(infinibox, 'attached')
    Node = infinibox.components.nodes.object_type

    @extensions.add_attribute(Node)
    def attached(self):
        return self

    for node in infinibox.components.nodes:
        assert node.attached == node


def test_removing_extensions(infinibox):
    assert not hasattr(infinibox, 'new_method')

    @extensions.add_method(InfiniBox, 'new_method')
    def new_method(self, a, b, c):
        return True

    assert infinibox.new_method(1, 2, 3)

    new_method.__extension_deactivate__()

    assert not hasattr(infinibox, 'new_method')


def test_removing_extensions_twice(infinibox):
    @extensions.add_method(InfiniBox, 'new_method')
    def new_method(self, a, b, c):
        return True

    new_method.__extension_deactivate__()
    new_method.__extension_deactivate__()

    assert not hasattr(infinibox, 'new_method')


def test_extending_hierarchy(request, infinibox):

    Parent = SystemObject
    Child = Volume
    assert issubclass(Child, Parent)

    @extensions.add_method(Parent, 'method1')
    def method1(self):
        pass

    request.addfinalizer(method1.__extension_deactivate__)

    @extensions.add_method(Child, 'method1')
    def method1(self):  # pylint: disable=function-redefined
        pass

    request.addfinalizer(method1.__extension_deactivate__)


def test_extension_doc_and_name(request, infinibox_new_method):
    assert infinibox_new_method.__doc__ == 'new method doc'
    assert infinibox_new_method.__name__ == 'some_new_method'

def test_extension_repr(request, infinibox_new_method, bound, infinibox):
    repr_string = repr(infinibox_new_method)

    if bound:
        assert repr(infinibox) in repr_string

    assert 'InfiniBox.some_new_method' in repr_string


@pytest.fixture
def infinibox_new_method(infinibox, bound):

    @extensions.add_method(InfiniBox, name='some_new_method')
    def new_method(a, b, c):
        'new method doc'

    if bound:
        return infinibox.some_new_method
    else:
        return InfiniBox.some_new_method  # pylint: disable=no-member


@pytest.fixture(params=[True, False])
def bound(request):
    return request.param
