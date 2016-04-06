from .._compat import itervalues, string_types, requests
from ..core.exceptions import APICommandFailed
from sentinels import NOTHING


class LogicalUnit(object):
    def __init__(self, system, id, lun, clustered, host_cluster_id, volume_id,
                 host_id, **kwargs):
        self.system = system
        self.id = id
        self.lun = int(lun) if isinstance(lun, string_types) else lun
        self.clustered = clustered
        self.host_cluster_id = host_cluster_id
        self.volume_id = volume_id
        self.host_id = host_id
        self.additional_data = kwargs
        self.mapping_object = self.get_host() or self.get_cluster()

    @property
    def volume(self):
        return self.system.volumes.get_by_id_lazy(self.volume_id)

    def get_host(self):
        """ Returns the host to which this LU belongs
        """
        if not self.host_id:
            return None
        return self.system.hosts.get_by_id_lazy(self.host_id)

    def get_cluster(self):
        """ Returns the cluster to which this LU belongs
        """
        if not self.host_cluster_id:
            return None
        return self.system.host_clusters.get_by_id_lazy(self.host_cluster_id)

    def get_mapping_object(self):
        return self.mapping_object

    def is_clustered(self):
        return self.get_cluster() is not None

    def get_volume(self):
        """ Returns the volume mapped to this LU
        """
        return self.system.volumes.get_by_id_lazy(self.volume_id)

    @classmethod
    def _unmap(cls, obj, lun):
        url = obj.get_this_url_path().add_path('luns/lun/{0}'.format(lun))
        try:
            obj.system.api.delete(url)
        except APICommandFailed as e:
            if e.status_code != requests.codes.not_found:
                raise
        obj.refresh('luns')

    def delete(self):
        """ Deletes (or unmaps) this LU
        """
        if self.is_clustered():
            obj = self.get_cluster()
        else:
            obj = self.get_host()
        self._unmap(obj, self.lun)

    unmap=delete

    def get_lun(self):
        """ Returns the logical unit number of this LU
        """
        return self.lun

    def __int__(self):
        """ Same as :meth:`.get_lun`
        """
        return self.get_lun()

    def __repr__(self):
        return "<LUN {0}: {1}->{2}>".format(self.get_lun(), self.get_mapping_object(), self.get_volume())

    def __eq__(self, other):
        return type(other) == type(self) and other.id == self.id

    def get_unique_key(self):
        return (self.system, self.host_cluster_id, self.host_id, self.volume_id, self.lun)

    def __hash__(self):
        return hash(self.get_unique_key())


class LogicalUnitContainer(object):
    def __init__(self, system):
        self.luns = set()
        self._system = system


    @classmethod
    def from_logical_units(cls, system, logical_units):
        container = cls(system)
        for lu in logical_units:
            container.add_logical_unit(lu)
        return container

    @classmethod
    def from_dict_list(cls, system, lus_info):
        container = cls(system)
        for lu_info in lus_info:
            lu = LogicalUnit(system, **lu_info)
            container.add_logical_unit(lu)
        return container

    def get_lun_to_volume_dict(self):
        return dict((int(lun), lun.volume) for lun in self)

    def add_logical_unit(self, lu):
        self.luns.add(lu)

    def get_lus_for_mapping_object(self, mapping_object):
        lus = []
        for lu in iter(self):
            if lu.get_mapping_object() == mapping_object:
                lus.append(lu)
        return lus

    def get_lus_for_volume(self, volume):
        lus = []
        for lu in iter(self):
            if lu.get_volume() == volume:
                lus.append(lu)
        return lus

    def get_lus_for_lun(self, lun):
        lus = []
        for lu in iter(self):
            if lu.get_lun() == lun:
                lus.append(lu)
        return lus

    def __getitem__(self, item):
        if hasattr(item, 'get_type_name'):
            if item.get_type_name() == 'volume':
                getter = self.get_lus_for_volume
            else:
                getter = self.get_lus_for_mapping_object
            items = getter(item)
        elif isinstance(item, LogicalUnit):
            items = [item] if item in self else []
        else:
            items = self.get_lus_for_lun(item)

        if len(items) == 0:
            raise KeyError('{0} has no logical units'.format(item))
        if len(items) > 1:
            raise ValueError('{0} have too many logical units'.format(item))
        return items[0]

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def __len__(self):
        return len(self.luns)

    def __iter__(self):
        return iter(self.luns)

    def __contains__(self, item):
        return item in self.luns

    def __repr__(self):
        return "<LogicalUnitsContainer: [{0}]>".format(", ".join(map(str, self)))
