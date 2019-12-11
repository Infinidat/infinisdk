from ..core.api.special_values import Autogenerate
from ..core import Field
from ..core.bindings import RelatedObjectBinding
from ..core.exceptions import UnknownSystem
from ..core.utils import DONT_CARE
from .system_object import InfiniBoxObject
from ..core.type_binder import TypeBinder

class LinkBinder(TypeBinder):
    def __init__(self, *args, **kwargs):
        super(LinkBinder, self).__init__(*args, **kwargs)
        self._cached_related_systems = {}

    def remove_cached_related_system(self, related_system):
        self._cached_related_systems = {k:v for k, v in self._cached_related_systems.items() if v != related_system}

    def set_cached_related_system(self, link, related_system):
        self._cached_related_systems[link] = related_system

    def get_cached_related_system(self, link):
        return self._cached_related_systems.get(link)


class Link(InfiniBoxObject):

    BINDER_CLASS = LinkBinder

    FIELDS = [
        Field('id', type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field('name', creation_parameter=True, mutable=True, default=Autogenerate("link_{uuid}")),
        Field('local_replication_network_space', api_name='local_replication_network_space_id',
              binding=RelatedObjectBinding('network_spaces', value_for_none=None),
              type='infinisdk.infinibox.network_space:NetworkSpace',
              mutable=True, creation_parameter=True),
        Field('remote_link_id', type=int),
        Field('remote_host', type=str, mutable=True, creation_parameter=True),
        Field('remote_system_name', type=str),
        Field('remote_system_serial_number', type=int, is_filterable=True, is_sortable=True),
        Field('link_state', type=str),
        Field('state_description', type=str, feature_name="sync_replication"),
        Field('is_local_link_ready_for_sync', type=bool, feature_name="sync_replication"),
        Field('async_only', type=bool, feature_name="sync_replication"),
        Field('resiliency_mode', type=str, feature_name="active_active"),
        Field('witness_address', type=str, optional=True, is_filterable=True, is_sortable=True,
              creation_parameter=True, feature_name="active_active"),
        Field('local_witness_state', type=str, feature_name="active_active"),
        Field('link_mode', type=str, feature_name="active_active"),
    ]

    def is_up(self, from_cache=DONT_CARE):
        link_state = self.get_link_state(from_cache=from_cache)
        return link_state is not None and link_state.lower() == 'up'

    def is_down(self, from_cache=DONT_CARE):
        link_state = self.get_link_state(from_cache=from_cache)
        return link_state is not None and link_state.lower() in ['down', 'unknown']

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_replication()

    def attach(self, network_space):
        self.update_field('local_replication_network_space', network_space)

    def detach(self):
        self.update_field('local_replication_network_space', None)

    def refresh_connectivity(self, remote_host=None):
        data = {}
        if remote_host:
            data['remote_host'] = remote_host
            self.invalidate_cache('remote_host')
        url = self.get_this_url_path().add_path('refresh')
        self.system.api.post(url, data=data)

    def delete(self, force_if_remote_error=False, force_if_no_remote_credentials=False):  # pylint: disable=arguments-differ
        """Deletes this link

        :param force_if_remote_error: forces deletion even if remote side caused an API error
        :param force_if_no_remote_credentials: forces deletion even if no credentials to remote side
        """
        super().delete(force_if_remote_error=force_if_remote_error,
                       force_if_no_remote_credentials=force_if_no_remote_credentials)


    def get_linked_system(self, safe=False, from_cache=DONT_CARE):
        """Get the corresponsing system object at the remote and of the link. For this to work, the SDK user should
        call the register_related_system method of the Infinibox object when a link to a remote system is consructed
        for the first time"""
        related_system = self.system.links.get_cached_related_system(self)
        if related_system is not None:
            if not safe or related_system.is_active():
                return related_system
        remote_host = self.get_remote_host(from_cache=from_cache)
        for related_system in self.get_system().iter_related_systems():
            if safe and not related_system.is_active():
                continue
            for network_space in related_system.network_spaces.get_all():
                for ip in network_space.get_ips(from_cache=True):
                    if ip.ip_address == remote_host:
                        self.system.links.set_cached_related_system(self, related_system)
                        return related_system
        if safe:
            return None

        raise UnknownSystem("Could not find a related machine with IP address {}".format(remote_host))

    def get_remote_link(self, safe=False):
        """Get the corresponsing link object in the remote machine"""
        linked_system = self.get_linked_system(safe=safe)
        if linked_system is None:
            return None
        return linked_system.links.get_by_id_lazy(self.get_remote_link_id())

    def set_witness_address(self, witness_address):
        url = self.get_this_url_path().add_path('set_witness_address')
        self.system.api.post(url, data={'witness_address': witness_address})
        self.invalidate_cache('witness_address')
