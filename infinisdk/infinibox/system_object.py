from urlobject import URLObject as URL
from ..core.system_object import SystemObject, DONT_CARE
from ..core.exceptions import InfiniSDKException, CacheMiss
from .lun import LogicalUnit, LogicalUnitContainer
from .metadata_holder import MetadataHolder
from ..core.utils import end_reraise_context
import gossip


class InfiniBoxObject(SystemObject, MetadataHolder):

    def _get_metadata_uri(self):
        return URL("metadata/{}".format(self.id))

class InfiniBoxLURelatedObject(InfiniBoxObject):

    def get_lun(self, lun, from_cache=DONT_CARE, fetch_if_not_cached=True):
        fetch_from_cache = self._deduce_from_cache(["luns"], from_cache)
        if fetch_from_cache:
            try:
                return self.get_luns(from_cache=from_cache, fetch_if_not_cached=False)[lun]
            except (KeyError, CacheMiss):
                if not fetch_if_not_cached:
                    raise CacheMiss('LUN {} is not cached'.format(int(lun)))

        url = self.get_this_url_path().add_path('luns/{}'.format(lun))
        lun_info = self.system.api.get(url).get_result()
        lu = LogicalUnit(system=self.system, **lun_info)
        luns = self._cache.get('luns')
        if luns is None:
            # If luns is not in cache -> a luns refresh was requested...
            return lu

        for cached_lun_info in luns:
            if cached_lun_info['lun'] == lun:
                cached_lun_info.update(lun_info)
                break
        else:
            luns.append(lun_info)
        self.update_field_cache({'luns': luns})
        return lu


    def get_luns(self, *args, **kwargs):
        """
        Returns all LUNs mapped to this object

        :returns: A collection of :class:`.LogicalUnit` objects
        """
        luns_info = self.get_field('luns', *args, **kwargs)
        return LogicalUnitContainer.from_dict_list(self.system, luns_info)

    def get_lun_to_volume_dict(self):
        return self.get_luns().get_lun_to_volume_dict()

    def is_volume_mapped(self, volume):
        """
        Returns whether or not a given volume is mapped to this object
        """
        luns = self.get_luns()
        for lun in luns:
            if lun.get_volume() == volume:
                return True

        return False

    def _get_hook_data(self, volume, lun=None):
        return {'volume': volume, 'host_or_cluster': self, 'lun': int(lun) if lun else None}

    def map_volume(self, volume, lun=None):
        """
        Maps a volume to this object, possibly specifying the logical unit number (LUN) to use

        :returns: a :class:`.LogicalUnit` object representing the added LUN
        """
        post_data = {'volume_id': volume.get_id()}
        if lun is not None:
            post_data['lun'] = int(lun)
        url = self.get_this_url_path().add_path('luns')
        hook_tags = self.get_tags_for_object_operations(self.system)
        hook_data = self._get_hook_data(volume, lun)
        gossip.trigger_with_tags('infinidat.sdk.pre_volume_mapping',
                                 hook_data, tags=hook_tags)
        try:
            res = self.system.api.post(url, data=post_data)
        except Exception as e: # pylint: disable=broad-except
            with end_reraise_context():
                hook_data['exception'] = e
                gossip.trigger_with_tags('infinidat.sdk.volume_mapping_failure',
                                         hook_data, tags=hook_tags)
        volume.invalidate_cache('mapped')
        self.invalidate_cache('luns')
        lun_obj = LogicalUnit(system=self.system, **res.get_result())
        hook_data['lun_object'] = lun_obj
        gossip.trigger_with_tags('infinidat.sdk.post_volume_mapping', hook_data, tags=hook_tags)
        return lun_obj

    def unmap_volume(self, volume=None, lun=None):
        """
        Unmaps a volume either by specifying the volume or the lun it occupies
        """
        if volume:
            if lun is not None:
                raise InfiniSDKException('unmap_volume does not support volume & lun together')
            lun = self.get_luns()[volume]
        elif lun:
            lun = self.get_luns()[lun]
        else:
            raise InfiniSDKException('unmap_volume does must get or volume or lun')
        assert self == lun.get_mapping_object()
        hook_tags = self.get_tags_for_object_operations(self.system)
        hook_data = self._get_hook_data(volume, lun)
        gossip.trigger_with_tags('infinidat.sdk.pre_volume_unmapping', hook_data, tags=hook_tags)
        self.invalidate_cache('luns')
        try:
            lun.unmap()
        except Exception as e: # pylint: disable=broad-except
            with end_reraise_context():
                hook_data['exception'] = e
                gossip.trigger_with_tags('infinidat.sdk.volume_unmapping_failure', hook_data, tags=hook_tags)
        if volume:
            volume.invalidate_cache('mapped')
        gossip.trigger_with_tags('infinidat.sdk.post_volume_unmapping', hook_data, tags=hook_tags)
