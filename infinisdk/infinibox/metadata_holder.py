import requests
from sentinels import NOTHING

from ..core.exceptions import APICommandFailed
from ..core.object_query import LazyQuery


class MetadataHolder:

    system = None

    def _get_metadata_uri(self):
        raise NotImplementedError()  # pragma: no cover

    def _get_metadata_translated_result(self, metadata_items):
        if self.system.compat.get_metadata_version() >= 2:
            return dict((item['key'], item['value']) for item in metadata_items)
        return metadata_items

    def set_metadata(self, key, value):
        """Sets metadata key in the system associated with this object
        """
        return self.set_metadata_from_dict({key: value})

    def set_metadata_from_dict(self, data_dict):
        """Sets multiple metadata keys/values in the system associated with this object
        """
        return self.system.api.put(self._get_metadata_uri(), data=data_dict)

    def get_metadata_value(self, key, default=NOTHING):
        """Gets a metadata value, optionally specifying a default

        :param default: if specified, the value to retrieve if the metadata key doesn't exist.
           if not specified, and the key does not exist, the operation will raise an exception
        """
        metadata_url = self._get_metadata_uri().add_path(str(key))
        try:
            result = self.system.api.get(metadata_url).get_result()
        except APICommandFailed as caught:
            if caught.status_code != requests.codes.not_found or default is NOTHING:
                raise
            return default
        if self.system.compat.get_metadata_version() < 2:
            return result
        return result['value']

    def get_all_metadata(self):
        """:returns: Dictionary of all keys and values associated as metadata for this object
        """
        url = self._get_metadata_uri()
        if self.system.compat.get_metadata_version() < 2:
            return self.system.api.get(url).get_result()
        query = LazyQuery(self.system, url)
        return dict((item['key'], item['value']) for item in query)

    def unset_metadata(self, key):
        """Deletes a metadata key for this object
        """
        return self.system.api.delete(self._get_metadata_uri().add_path(str(key)))

    def clear_metadata(self):
        """Deletes all metadata keys for this object
        """
        self.system.api.delete(self._get_metadata_uri())
