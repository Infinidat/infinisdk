from ..core import SystemObject
from ..core.exceptions import InfiniSDKException
from .lun import LogicalUnitContainer, LogicalUnit


class InfiniBoxObject(SystemObject):
    def _get_metadata_uri(self):
        return "metadata/{0}".format(self.id)

    def _get_result(self, api_response):
        return api_response.get_json()['result']

    def set_metadata(self, key, value):
        return self._get_result(self.system.api.post(self._get_metadata_uri(), data={key: value}))

    def get_metadata_value(self, key):
        metadata_url = '{0}/{1}'.format(self._get_metadata_uri(), key)
        return self._get_result(self.system.api.get(metadata_url))

    def get_all_metadata(self):
        return self._get_result(self.system.api.get(self._get_metadata_uri()))

    def unset_metadata(self, key):
        return self.system.api.delete("{0}/{1}".format(self._get_metadata_uri(), key))

    def clear_metadata(self):
        return self.system.api.delete(self._get_metadata_uri())


class InfiniBoxLURelatedObject(InfiniBoxObject):

    def get_luns(self, *args, **kwargs):
        luns_info = self.get_field('luns', *args, **kwargs)
        return LogicalUnitContainer.from_dict_list(self.system, luns_info)

    def is_volume_mapped(self, volume):
        luns = self.get_luns()
        for lun in luns:
            if lun.get_volume() == volume:
                return True
        else:
            return False

    def map_volume(self, volume, lun=None):
        post_data = {'volume_id': volume.get_id()}
        if lun is not None:
            post_data['lun'] = int(lun)
        url = self.get_this_url_path().add_path('luns')
        self.system.api.post(url, data=post_data)
        return volume.get_lun()

    def unmap_volume(self, volume=None, lun=None):
        if volume:
            if lun is not None:
                raise InfiniSDKException('unmap_volume does not support volume & lun together')
            lun = volume.get_lun()
        elif lun is None:
            raise InfiniSDKException('unmap_volume does must get or volume or lun')
        LogicalUnit._unmap(self, int(lun))
