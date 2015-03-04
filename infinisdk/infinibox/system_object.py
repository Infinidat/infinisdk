###!
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
###!
from .._compat import requests
from sentinels import NOTHING

from ..core.system_object import SystemObject, DONT_CARE
from ..core.exceptions import APICommandFailed, InfiniSDKException, CacheMiss
from .lun import LogicalUnit, LogicalUnitContainer


class InfiniBoxObject(SystemObject):

    def _get_metadata_uri(self):
        return "metadata/{0}".format(self.id)

    def _get_result(self, api_response):
        return api_response.get_json()['result']

    def set_metadata(self, key, value):
        """Sets metadata key in the system associated with this object
        """
        return self.set_metadata_from_dict({key: value})

    def set_metadata_from_dict(self, data_dict):
        """Sets multiple metadata keys/values in the system associated with this object
        """
        return self._get_result(self.system.api.post(self._get_metadata_uri(), data=data_dict))

    def get_metadata_value(self, key, default=NOTHING):
        """Gets a metadata value, optionally specifying a default

        :param default: if specified, the value to retrieve if the metadata key doesn't exist.
           if not specified, and the key does not exist, the operation will raise an exception
        """
        metadata_url = '{0}/{1}'.format(self._get_metadata_uri(), key)
        try:
            return self._get_result(self.system.api.get(metadata_url))
        except APICommandFailed as caught:
            if caught.status_code != requests.codes.not_found or default is NOTHING:
                raise
            return default

    def get_all_metadata(self):
        """:returns: Dictionary of all keys and values associated as metadata for this object
        """
        return self._get_result(self.system.api.get(self._get_metadata_uri()))

    def unset_metadata(self, key):
        """Deletes a metadata key for this object
        """
        return self.system.api.delete("{0}/{1}".format(self._get_metadata_uri(), key))

    def clear_metadata(self):
        """Deletes all metadata keys for this object
        """
        self.system.api.delete(self._get_metadata_uri())


class InfiniBoxLURelatedObject(InfiniBoxObject):

    def get_lun(self, lun, from_cache=DONT_CARE, fetch_if_not_cached=True):
        fetch_from_cache = self._deduce_from_cache(["luns"], from_cache)
        if fetch_from_cache:
            try:
                return self.get_luns(from_cache=from_cache, fetch_if_not_cached=False)[lun]
            except (KeyError, CacheMiss):
                if not fetch_if_not_cached:
                    raise CacheMiss('LUN {0} is not cached'.format(int(lun)))

        url = self.get_this_url_path().add_path('luns/{0}'.format(lun))
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

        :rtype: A collection of :class:`.LogicalUnit` objects
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
        else:
            return False

    def map_volume(self, volume, lun=None):
        """
        Maps a volume to this object, possibly specifying the logical unit number (LUN) to use

        :rtype: a :class:`.LogicalUnit` object representing the added LUN
        """
        post_data = {'volume_id': volume.get_id()}
        if lun is not None:
            post_data['lun'] = int(lun)
        url = self.get_this_url_path().add_path('luns')
        res = self.system.api.post(url, data=post_data)
        volume.refresh('mapped')
        self.refresh('luns')
        return LogicalUnit(system=self.system, **res.get_result())

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
        self.refresh('luns')
        lun.unmap()
        if volume:
            volume.refresh('mapped')
