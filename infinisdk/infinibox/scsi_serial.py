import struct


class SCSISerial(object):

    # Composed of:
    # IEEE_company_id - 24bit,
    # reserved-20bit,
    # system_id-16bit
    # volume_id-64bit

    def __init__(self, serial):
        super(SCSISerial, self).__init__()
        self.serial = serial
        self._decode()

    def _decode(self):
        try:
            self.ieee_company_id = _parse_hex_long(self.serial[:6])
            self.reserved = _parse_hex_long(self.serial[6:11])
            self.system_id = _parse_hex_long(self.serial[11:15])
            self.volume_id = _parse_hex_long(self.serial[15:])
        except (TypeError,):
            self.ieee_company_id = self.reserved = self.system_id = self.volume_id = None

    def __repr__(self):
        return self.serial

    def __eq__(self, other):
        if type(other) != SCSISerial:
            return self.serial == other
        return self.serial == other.serial

    def __ne__(self, other):
        if type(other) != SCSISerial:
            return self.serial != other
        return self.serial != other.serial

    def __hash__(self):
        return hash(self.serial)


def _parse_hex_long(s):
    min_size = struct.calcsize('>Q') * 2
    if len(s) < min_size:
        s = s.rjust(min_size, '0')
    elif len(s) % 2 != 0:
        s = '0{0}'.format(s)
    return struct.unpack('>Q', s.decode('hex'))[0]
