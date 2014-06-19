from .._compat import itervalues, iteritems, sorted, cmp
import operator



class InfiniBoxComponentQuery(object):
    def __init__(self, system, object_type, *predicates, **kw):
        self.system = system
        self.object_type = object_type
        self.predicates = predicates
        self.kw = kw
        self.sort_criteria = tuple()


    def _get_items(self):
        def _sort_cmp_items(x, y):
            for criteria in self.sort_criteria:
                sign_func = operator.neg if criteria.prefix == '-' else operator.pos
                sort_field_name = criteria.field.name
                x_val = x.get_field(sort_field_name)
                y_val = y.get_field(sort_field_name)
                res = cmp(x_val, y_val)
                if res != 0:
                    return sign_func(res)
            else:
                return 0

        fetched_items = [item for item in itervalues(self.system.components._components_by_id)
                         if self.passed_filtering(item)]

        if not self.sort_criteria:
            return fetched_items

        return sorted(fetched_items, cmp=_sort_cmp_items)

    def __iter__(self):
        self._fetch()

        for item in self._get_items():
                yield item

    def __len__(self):
        return len([item for item in self])

    def __getitem__(self, index):
        if index < 0:
            raise NotImplementedError("Negative indices not supported yet")
        return [item for item in self][index]

    def passed_filtering(self, item):
        if (self.object_type != self.system.components.object_type and
            self.object_type != type(item)):
            return False
        for predicate in self.predicates:
            op_func = getattr(operator, predicate.operator_name)
            item_value = item.get_field(predicate.field.name)
            if not op_func(item_value, predicate.value):
                return False
        for k, v in iteritems(self.kw):
            if item.get_field(k) != v:
                return False
        return True

    def _fetch(self):
        if self.object_type in [self.system.components.nodes.object_type,
                                self.system.components.services.object_type]:
            self._fetch_nodes()
        else:
            self._fetch_all()

    def _fetch_all(self):
        components = self.system.components
        if not components.should_fetch_all():
            return
        Rack = components.racks.object_type
        rack_1_url = Rack.get_specific_rack_url(1)
        rack_1_data = self.system.api.get(rack_1_url).get_json()['result']
        system_component = components.system_component
        Rack.construct(self.system, rack_1_data, system_component.id)
        components.mark_fetched_all()

    def _fetch_nodes(self):
        components = self.system.components
        if not components.should_fetch_nodes():
            return
        rack_1 = components.racks.choose()
        Node = components.nodes.object_type
        nodes_url = Node.get_url_path(self.system)
        nodes_data = self.system.api.get(nodes_url).get_json()['result']
        for node_data in nodes_data:
            Node.construct(self.system, node_data, rack_1.id)
        components.mark_fetched_nodes()

    def page(self, page_index):
        raise NotImplementedError()  # pragma: no cover

    def page_size(self, page_size):
        raise NotImplementedError()  # pragma: no cover

    def sort(self, *criteria):
        self.sort_criteria += criteria
        return self

    def only_fields(self, field_names):
        raise NotImplementedError()  # pragma: no cover
