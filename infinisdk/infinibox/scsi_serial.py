import binascii
import struct


class SCSISerial:

    def __init__(self, serial):
        super(SCSISerial, self).__init__()
        #: the string representation (hexadecimal) of the serial number
        self.serial = serial

        try:
            #: the IEEE company id (24 bits)
            self.ieee_company_id = _parse_hex_long(self.serial[:6])
            # 20 bits
            self.reserved = _parse_hex_long(self.serial[6:11])
            #: unique system id (16 bits)
            self.system_id = _parse_hex_long(self.serial[11:15])
            #: the volume id (64 bits)
            self.volume_id = _parse_hex_long(self.serial[15:])
        except (TypeError, binascii.Error):
            self.ieee_company_id = self.reserved = self.system_id = self.volume_id = None

    def __repr__(self):
        return self.serial

    def __eq__(self, other):
        if not isinstance(other, SCSISerial):
            return self.serial == other
        return self.serial == other.serial

    def __ne__(self, other):
        if not isinstance(other, SCSISerial):
            return self.serial != other
        return self.serial != other.serial

    def __hash__(self):
        return hash(self.serial)


def _parse_hex_long(s):
    min_size = struct.calcsize('>Q') * 2
    if len(s) < min_size:
        s = s.rjust(min_size, '0')
    elif len(s) % 2 != 0:
        s = '0{}'.format(s)
    return struct.unpack('>Q', binascii.a2b_hex(s))[0]
