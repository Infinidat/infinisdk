import itertools

import pytest
from infinisdk.core import extensions
from infinisdk.infinibox import InfiniBox
from infinisdk.infinibox.system_object import SystemObject
from infinisdk.infinibox.volume import Volume


def test_no_extensions_by_default():
    assert len(extensions.active) == 0


@pytest.mark.parametrize('different_name', [True, False])
def test_extending(infinibox, different_name):
    with pytest.raises(AttributeError):
        infinibox.new_method

    if different_name:
        @extensions.add_method(InfiniBox, 'new_method')
        def some_other_name(self, a, b, c):
            return "{0} {1} {2} {3}".format(type(self).__name__, a, b, c)

    else:
        @extensions.add_method(InfiniBox)
        def new_method(self, a, b, c):
            return "{0} {1} {2} {3}".format(type(self).__name__, a, b, c)

    assert infinibox.new_method(1, 2, 3) == 'InfiniBox 1 2 3'
    assert infinibox.new_method.__self__ is infinibox
    assert infinibox.new_method.im_self is infinibox
    assert infinibox.new_method.im_class is type(infinibox)
    if different_name:
        assert infinibox.new_method.im_func is some_other_name
    else:
        assert infinibox.new_method.im_func is new_method


def test_cannot_attach_existing_methods(infinibox, volume):
    assert hasattr(volume, 'update_name')
    with pytest.raises(RuntimeError):
        @extensions.add_method(type(volume), 'update_name')
        def set_name(self, new_name):
            raise NotImplementedError()  # pragma: no cover


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
    def method1(self):
        pass

    request.addfinalizer(method1.__extension_deactivate__)
