import pytest
from infinisdk.infinibox.scsi_serial import SCSISerial

_SERIAL_STR = '742B0F000004e48000000000000014a'


def test_serial_str(serial):
    assert str(serial) == repr(serial) == _SERIAL_STR


def test_company_id(serial):
    assert serial.ieee_company_id == 0x742B0F


def test_system_id(serial):
    assert serial.system_id == 0x4e48


def test_reserved(serial):
    assert serial.reserved == 0


def test_volume_id(serial):
    assert serial.volume_id == 0x14a


def test_invalid_serial():
    s = SCSISerial('invalid')
    assert str(s) == repr(s) == 'invalid'
    assert s.ieee_company_id is None
    assert s.reserved is None
    assert s.system_id is None
    assert s.volume_id is None


def test_eq():
    s1_1 = SCSISerial('742B0F000004e48000000000000014a')
    s1_2 = SCSISerial(s1_1.serial)
    s2 = SCSISerial('742B0F000004e48000000000000014b')
    assert s1_1 == s1_1.serial
    assert not (s1_1 != s1_1.serial)  # pylint: disable=superfluous-parens
    assert s1_1 == s1_2
    assert not (s1_1 != s1_2)  # pylint: disable=superfluous-parens
    assert s2 != s1_1
    assert s2 != s1_2
    assert not (s2 == s1_1)  # pylint: disable=superfluous-parens
    assert not (s2 == s1_2)  # pylint: disable=superfluous-parens


def test_hashing(serial):
    assert hash(serial) == hash(serial.serial)


@pytest.fixture
def serial():
    return SCSISerial(_SERIAL_STR)
