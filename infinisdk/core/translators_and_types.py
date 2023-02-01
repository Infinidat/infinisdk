from __future__ import absolute_import

from datetime import timedelta

import arrow
import munch
from api_object_schema import TypeInfo, ValueTranslator
from capacity import Capacity, byte
from infi.dtypes.iqn import iSCSIName, make_iscsi_name
from infi.dtypes.nqn import NQN
from infi.dtypes.wwn import WWN


class CapacityTranslator(ValueTranslator):
    def _to_api(self, value):
        if value is None:
            return value
        if value == 0:
            return 0
        if not isinstance(value, Capacity):
            raise TypeError("Capacity must be specified using a Capacity object")
        return int(value // byte)

    def _from_api(self, value):
        if value is None:
            return value
        return int(value) * byte


CapacityType = TypeInfo(type=Capacity, api_type=int, translator=CapacityTranslator())


class MunchTranslator(ValueTranslator):
    def _to_api(self, value):
        if isinstance(value, munch.Munch):
            return value.toDict()
        return value

    def _from_api(self, value):
        return munch.munchify(value)


class MunchListTranslator(ValueTranslator):
    def __init__(self, *args, **kwargs):
        super(MunchListTranslator, self).__init__(*args, **kwargs)
        self._translator = MunchTranslator()

    def _to_api(self, value):
        # pylint: disable=protected-access
        return [self._translator._to_api(single_value) for single_value in value]

    def _from_api(self, value):
        # pylint: disable=protected-access
        return [self._translator._from_api(single_value) for single_value in value]


MunchType = TypeInfo(type=munch.Munch, api_type=dict, translator=MunchTranslator())
MunchListType = TypeInfo(type=list, api_type=list, translator=MunchListTranslator())


class MillisecondsDatetimeTranslator(ValueTranslator):
    def _to_api(self, value):
        if value is None:
            return None
        return int(round(value.float_timestamp * 1000.0))

    def _from_api(self, value):
        if value is None:
            return None
        return arrow.get(value / 1000.0)


MillisecondsDatetimeType = TypeInfo(
    type=arrow.Arrow, api_type=int, translator=MillisecondsDatetimeTranslator()
)


class SecondsDatetimeTranslator(ValueTranslator):
    def _to_api(self, value):
        if value is None:
            return None
        return int(round(value.float_timestamp))

    def _from_api(self, value):
        if value is None:
            return None
        return arrow.get(value)


SecondsDatetimeType = TypeInfo(
    type=arrow.Arrow, api_type=int, translator=SecondsDatetimeTranslator()
)


class MillisecondsDeltaTranslator(ValueTranslator):
    def _to_api(self, value):
        if value == 0:
            return 0
        # for python 2.6 compatibility...
        total_seconds = (
            value.microseconds + (value.seconds + value.days * 24 * 3600) * 10 ** 6
        ) / 10 ** 6
        return int(total_seconds * 1000.0)

    def _from_api(self, value):
        if value is None:
            return None
        value /= 1000.0
        return timedelta(
            seconds=int(value), microseconds=int((value - int(value)) * 1000)
        )


MillisecondsDeltaType = TypeInfo(
    type=timedelta, api_type=int, translator=MillisecondsDeltaTranslator()
)


class SecondsDeltaTranslator(ValueTranslator):
    def _to_api(self, value):
        if value == 0:
            return 0
        return int(value.total_seconds())

    def _from_api(self, value):
        if value is None:
            return None
        return timedelta(seconds=int(value))


SecondsDeltaType = TypeInfo(
    type=timedelta, api_type=int, translator=SecondsDeltaTranslator()
)

WWNType = TypeInfo(type=WWN, api_type=str)


def host_port_to_api(value):
    if isinstance(value, WWN):
        port_type = "fc"
    elif isinstance(value, (str, bytes)):
        port_type = "fc"
        value = WWN(value)
    elif isinstance(value, iSCSIName):
        port_type = "iscsi"
    elif isinstance(value, NQN):
        port_type = "NVME"
    else:
        assert False, "Unknown type of {}".format(value)
    return {"type": port_type, "address": str(value)}


def address_type_factory(type_):
    _TYPES = {"fc": WWN, "iscsi": make_iscsi_name, "nvme": NQN}
    return _TYPES[type_.lower()]


def host_port_from_api(value):
    return address_type_factory(value["type"])(value["address"])


class HostPortListTranslator(ValueTranslator):
    def _to_api(self, value):
        return [host_port_to_api(v) for v in value]

    def _from_api(self, value):
        return [host_port_from_api(v) for v in value]


HostPortListType = TypeInfo(
    type=list, api_type=list, translator=HostPortListTranslator()
)
