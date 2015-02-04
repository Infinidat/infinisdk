### !
### Infinidat Ltd.  -  Proprietary and Confidential Material
###
### Copyright (C) 2015, Infinidat Ltd. - All Rights Reserved
###
### NOTICE: All information contained herein is, and remains the property of Infinidat Ltd.
### All information contained herein is protected by trade secret or copyright law.
### The intellectual and technical concepts contained herein are proprietary to Infinidat Ltd.,
### and may be protected by U.S. and Foreign Patents, or patents in progress.
###
### Redistribution and use in source or binary forms, with or without modification,
### are strictly forbidden unless prior written permission is obtained from Infinidat Ltd.
### !
from ..core.api.special_values import Autogenerate
from ..core.type_binder import TypeBinder
from ..core import Field
from ..core.bindings import RelatedObjectBinding
from ..core.exceptions import TooManyObjectsFound
from .system_object import InfiniBoxObject


class ReplicaBinder(TypeBinder):

    """Implements *system.replicas*
    """

    def replicate_volume(self, volume, link, remote_pool=None, remote_volume=None):
        """Replicates a volume, creating its remote replica on the specified pool

        :param remote_pool: if omitted, ``remote_volume`` must be specified. Otherwise, means creating target volume
        :param remote_volume: if omitted, ``remote_pool`` must be specified. Otherwise, means creating based on existing volume on target
        """
        if remote_volume is None:
            assert remote_pool is not None
            return self.replicate_volume_create_target(volume, link, remote_pool=remote_pool)
        return self.replicate_volume_existing_target(volume, link, remote_volume=remote_volume)

    def replicate_volume_create_target(self, volume, link, remote_pool):
        return self.create(
            link=link, remote_pool_id=remote_pool.id,
            entity_pairs=[{
                'local_entity_id': volume.id,
                'remote_base_action': 'CREATE',
            }], entity_type='VOLUME')

    def replicate_volume_existing_target(self, volume, link, remote_volume):
        return self.create(
            link=link,
            entity_pairs=[{
                'local_entity_id': volume.id,
                'remote_entity_id': remote_volume.id,
                'remote_base_action': 'NO_BASE_DATA',
            }], entity_type='VOLUME')


class Replica(InfiniBoxObject):

    BINDER_CLASS = ReplicaBinder

    FIELDS = [

        Field('id', type=int, is_identity=True),
        Field('link', api_name='link_id', binding=RelatedObjectBinding(
            'links'), type='infinisdk.infinibox.link:Link', creation_parameter=True),
        Field('name', creation_parameter=True, mutable=True, is_filterable=True,
              default=Autogenerate("replica_{uuid}")),
        Field('entity_pairs', type=list, creation_parameter=True),
        Field('entity_type', type=str,
              creation_parameter=True, default='VOLUME'),
        Field('remote_pool_id', type=int,
              creation_parameter=True, optional=True),
        Field('remote_replica_id', type=int),
        Field('role', type=str),
        Field('state', type=str),
        Field('sync_interval', type=int,
              creation_parameter=True, default=30000),

    ]

    def get_local_entity(self):
        """Returns the local entity used for replication, assuming there is only one
        """
        pairs = self.get_entity_pairs(from_cache=True)
        if self.get_field('entity_type', from_cache=True).lower() != 'volume':
            raise NotImplementedError()  # pragma: no cover
        if len(pairs) > 1:
            raise TooManyObjectsFound()
        [pair] = pairs
        return self.system.volumes.get_by_id_lazy(pair['local_entity_id'])

    def get_local_volume(self):
        """Returns the local volume, assuming there is exactly one
        """
        return self.get_local_entity()

    def suspend(self):
        """Suspends this replica
        """
        self.system.api.post(self.get_this_url_path().add_path('suspend'))
        self.refresh('state')

    def resume(self):
        """Resumes this replica
        """
        self.system.api.post(self.get_this_url_path().add_path('resume'))
        self.refresh('state')

    def is_suspended(self, *args, **kwargs):
        """Returns whether or not this replica is in suspended state
        """
        return self.get_state(*args, **kwargs).lower() == 'suspended'

    def change_role(self, retain_staging_area=False):
        self.system.api.post(self.get_this_url_path()
                                 .add_path('change_role')
                                 .add_query_param('retain_staging_area', 'true' if retain_staging_area else 'false'))
        self.refresh()

    def is_source(self):
        return self.get_role().lower() == 'source'

    def is_target(self):
        return not self.is_source()

    def has_local_entity(self, entity):
        pairs = self.get_field('entity_pairs', from_cache=True)
        for pair in pairs:
            if pair['local_entity_id'] == entity.id:
                return True
        return False

    def delete(self, retain_staging_area=False, force_if_remote_error=False, force_on_target=False, force_if_no_remote_credentials=False):
        path = self.get_this_url_path()
        if retain_staging_area:
            path = path.add_query_param('retain_staging_area', 'true')
        if force_if_remote_error:
            path = path.add_query_param('force_if_remote_error', 'true')
        if force_on_target:
            path = path.add_query_param('force_on_target', 'true')
        if force_if_no_remote_credentials:
            path = path.add_query_param('force_if_no_remote_credentials', 'true')

        self.system.api.delete(path)
