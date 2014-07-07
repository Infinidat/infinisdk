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


def test_removing_extensions(infinibox):
    assert not hasattr(infinibox, 'new_method')

    @extensions.add_method(InfiniBox, 'new_method')
    def new_method(self, a, b, c):
        return True

    assert infinibox.new_method(1, 2, 3)

    new_method.deactivate()

    assert not hasattr(infinibox, 'new_method')


def test_removing_extensions_twice(infinibox):
    @extensions.add_method(InfiniBox, 'new_method')
    def new_method(self, a, b, c):
        return True

    new_method.deactivate()
    new_method.deactivate()

    assert not hasattr(infinibox, 'new_method')


def test_extending_hierarchy(request, infinibox):

    Parent = SystemObject
    Child = Volume
    assert issubclass(Child, Parent)

    @extensions.add_method(Parent, 'method1')
    def method1(self):
        pass

    request.addfinalizer(method1.deactivate)

    @extensions.add_method(Child, 'method1')
    def method1(self):
        pass

    request.addfinalizer(method1.deactivate)
