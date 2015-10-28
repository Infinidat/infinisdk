from ..core.api.special_values import Autogenerate
from ..core import Field
from ..core.bindings import RelatedObjectBinding
from ..core.exceptions import InfiniSDKException, UnknownSystem
from .system_object import InfiniBoxObject



class Link(InfiniBoxObject):

    FIELDS = [

        Field('id', type=int, is_identity=True, is_filterable=True, is_sortable=True),
        Field('name', creation_parameter=True, mutable=True, default=Autogenerate("link_{uuid}")),
        Field('local_replication_network_space', api_name='local_replication_network_space_id',
              binding=RelatedObjectBinding('network_spaces'),
              type='infinisdk.infinibox.network_space:NetworkSpace', creation_parameter=True),
        Field('remote_link_id', type=int),
        Field('remote_host', type=str, creation_parameter=True),
        Field('remote_system_name', type=str),
        Field('remote_system_serial_number', type=int),
        Field('link_state', type=str),
    ]

    def is_up(self):
        return self.get_link_state().lower() == 'up'

    def is_down(self):
        return self.get_link_state().lower() in ['down', 'unknown']

    @classmethod
    def is_supported(cls, system):
        return system.compat.has_replication()

    def delete(self, force_if_remote_error=False, force_if_no_remote_credentials=False):
        """Deletes this link

        :param force_if_remote_error: forces deletion even if remote side caused an API error
        :param force_if_no_remote_credentials: forces deletion even if no credentials to remote side
        """
        url = self.get_this_url_path()
        if force_if_remote_error:
            url = url.add_query_param('force_if_remote_error', 'true')
        if force_if_no_remote_credentials:
            url = url.add_query_param('force_if_no_remote_credentials', 'true')
        with self._get_delete_context():
            self.system.api.delete(url)

    def get_linked_system(self):
        """Get the corresponsing system object at the remote and of the link. For this to work, the SDK user should
        call the register_related_system method of the Infinibox object when a link to a remote system is consructed
        for the first time"""
        remote_host = self.get_remote_host()
        for related_system in self.get_system().iter_related_systems():
            for network_space in related_system.network_spaces.get_all():
                for ip in network_space.get_ips():
                    if ip.ip_address == remote_host:
                        return related_system

        raise UnknownSystem("Could not find a related machine with IP address {0}".format(remote_host))
