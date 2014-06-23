from infinisdk._compat import itervalues, string_types


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

    @property
    def volume(self):
        return self.system.volumes.safe_get_by_id(self.volume_id)

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
        return self.system.clusters.get_by_id_lazy(self.host_cluster_id)

    def get_mapping_object(self):
        returned = self.get_cluster()
        if returned is None:
            returned = self.get_host()

        return returned

    mapping_object = property(get_mapping_object)

    def is_clustered(self):
        return self.get_cluster() is not None

    def get_volume(self):
        """ Returns the volume mapped to this LU
        """
        return self.system.volumes.get_by_id_lazy(self.volume_id)

    @classmethod
    def _unmap(cls, obj, lun):
        url = obj.get_this_url_path().add_path('luns/lun/{0}'.format(lun))
        obj.system.api.delete(url)

    def delete(self):
        """ Deletes (or unmaps) this LU
        """
        obj = self.get_host() or self.get_cluster()
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
        return "<LUN {0}>".format(self.get_lun())

    def __eq__(self, other):
        return type(other) == type(self) and other.id == self.id


class LogicalUnitContainer(object):
    def __init__(self, system):
        self.luns = {}
        self._system = system
        self._rel_classes = (system.volumes.object_type,
                             system.hosts.object_type,
                             system.clusters.object_type)

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

    def add_logical_unit(self, lu):
        self.luns[lu.get_lun()] = lu

    def __getitem__(self, item):
        if isinstance(item, self._rel_classes):
            item_getter_name = "get_{0}".format(item.get_type_name())
            item_getter = getattr(LogicalUnit, item_getter_name)
            lus = [lu for lu in itervalues(self.luns) if item_getter(lu)==item]
            if not lus:
                raise KeyError('{0} has no logical units'.format(item))
            return self.from_logical_units(self._system, lus)
        return self.luns[item]

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def __len__(self):
        return len(self.luns)

    def __iter__(self):
        for lu in itervalues(self.luns):
            yield lu

    def __contains__(self, item):
        return item in itervalues(self.luns)

    def __repr__(self):
        return "[{0}]".format(", ".join(map(str, self)))
