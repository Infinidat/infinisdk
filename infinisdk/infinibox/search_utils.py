from infinisdk.core.object_query import LazyQuery
from urlobject import URLObject

_type_map = {'cg': 'cons_group',
             'cluster': 'host_cluster',
             'interfaces': 'network_interface',
             'ipd': 'network_space',
             'links': 'link',
             'notification_smtp_target': 'notificationtarget',
             'notification_snap_target': 'notificationtarget',
             'notification_syslog_target': 'notificationtarget',
             'qos': 'qos_policy',
             'replicas': 'replica',
             'switch': 'fc_switch',
             'users_repository': 'ldapconfig'}


class UnknownSearchObject(object):
    def __init__(self, system, construct_data):
        self.system = system
        self.id = construct_data['id']
        self._type_name = construct_data['type_name']
        self._cache = construct_data

    def get_fields(self):
        return self._cache

    def get_field(self, field):
        return self._cache[field]

    def get_id(self):
        return self.id

    def get_system(self):
        return self.system

    def get_type_name(self):
        return self._type_name

    def __repr__(self):
        return '<{}:UnknownSearchObject id={} type_name={}>'.format(self.system.get_name(), self.id, self._type_name)


def object_factory(system, received_item):
    received_type = received_item['type']
    binder = system.objects.get_binder_by_type_name(_type_map.get(received_type, received_type))
    construct_data = received_item.get('properties', {})

    if binder:
        object_type = binder.object_type
        construct_data[object_type.fields.id.api_name] = received_item['id']
        factory = object_type.construct

    else:
        factory = UnknownSearchObject
        construct_data.update({'id': received_item['id'], 'type_name': received_type})

    return factory(system, construct_data)


def get_search_query_object(system):
    return LazyQuery(system, URLObject('search'), object_factory)
