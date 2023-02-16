import pytest
from infinisdk.infinibox.scsi_serial import SCSISerial

_SERIAL_STR = '742B0F000004e48000000000000014a'


@pytest.fixture
def scsi_serial_1() -> SCSISerial:
    return SCSISerial('742B0F000004e48000000000000014a')


@pytest.fixture
def scsi_serial_2() -> SCSISerial:
    return SCSISerial('742B0F000004e48000000000000014b')


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


def test_eq(scsi_serial_1, scsi_serial_2):
    s1_2 = SCSISerial(scsi_serial_1.serial)
    assert scsi_serial_1 == scsi_serial_1.serial
    assert not (scsi_serial_1 != scsi_serial_1.serial)  # pylint: disable=superfluous-parens
    assert scsi_serial_1 == s1_2
    assert not (scsi_serial_1 != s1_2)  # pylint: disable=superfluous-parens
    assert scsi_serial_2 != scsi_serial_1
    assert scsi_serial_2 != s1_2
    assert not (scsi_serial_2 == scsi_serial_1)  # pylint: disable=superfluous-parens
    assert not (scsi_serial_2 == s1_2)  # pylint: disable=superfluous-parens

def test_comparison(scsi_serial_1, scsi_serial_2) -> None:
    assert scsi_serial_1 > 0x14a
    assert scsi_serial_1 < 0x7f2B0F000004e4ffffffffffffff14f
    assert scsi_serial_1 >= 0x14a
    assert scsi_serial_1 <= 0x7f2B0F000004e4ffffffffffffff14f
    assert scsi_serial_1 < scsi_serial_2
    assert scsi_serial_2 > scsi_serial_1
    assert scsi_serial_1 <= scsi_serial_2
    assert scsi_serial_2 >= scsi_serial_1

def test_hashing(serial):
    assert hash(serial) == hash(serial.serial)


@pytest.fixture
def serial():
    return SCSISerial(_SERIAL_STR)
