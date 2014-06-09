
from infinipy2._compat import string_types


def test_is_mock(izbox):
    assert (not izbox.is_mock())


def test_is_virtual(izbox):
    assert (not izbox.is_virtual())


def test_is_simulator(izbox):
    assert izbox.is_simulator()


def test_get_serial(izbox):
    assert izbox.get_serial() == 25001


def test_get_state(izbox):
    assert izbox.get_state() == 'online'


def test_get_model(izbox):
    assert izbox.get_model() == 'G3200'


def test_get_version(izbox):
    assert isinstance(izbox.get_version(), string_types)
