from urlobject import URLObject as URL

from .metadata_holder import MetadataHolder


class SystemMetadata(MetadataHolder):

    def __init__(self, system):
        super(SystemMetadata, self).__init__()
        self.system = system

    def _get_metadata_uri(self):
        return URL("metadata/system")
