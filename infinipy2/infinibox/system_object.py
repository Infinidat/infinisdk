from ..core import SystemObject


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
