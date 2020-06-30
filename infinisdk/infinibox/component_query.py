import functools
import operator
from numbers import Number

from ..core.utils.python import cmp
from ..core.object_query import QueryBase


class ComponentQueryBase(QueryBase):
    def __init__(self, system, query_objects_str, *predicates, **kw):
        self.system = system
        self.predicates = predicates
        self.kw = kw
        self._fetched_items = None
        self._force_fetch = False
        self._str = query_objects_str.replace('_', ' ').title()
        if predicates or kw:
            self._str += ' with '
            self._str += ' AND '.join(["({})".format(pred) for pred in predicates] +\
                                      ["({}={})".format(k, v) for k, v in kw.items()])

    def force_fetching_objects(self):
        self._force_fetch = True
        return self

    def __getitem__(self, index):
        if isinstance(index, Number) and index < 0:
            raise NotImplementedError("Negative indices not supported yet")
        return [item for item in self][index]

    def __iter__(self):
        for item in self._get_items():
            yield item

    def _get_items(self):
        raise NotImplementedError()

    def __len__(self):
        return len([item for item in self])

    def __str__(self):
        return self._str

    def __repr__(self):
        return "<ComponentsQuery: {}>".format(self._str)


class InfiniBoxComponentQuery(ComponentQueryBase):
    def __init__(self, system, object_type, *predicates, **kw):
        super(InfiniBoxComponentQuery, self).__init__(system, object_type.get_plural_name(), *predicates, **kw)
        self.object_type = object_type
        self.sort_criteria = tuple()
        # predicates' field attribute is QField (non the object field), therefore, we should get the object's one
        # for checking its cahced attribute
        field_names = [pred.field.name for pred in predicates] + list(kw)
        relevant_fields = [self.object_type.fields.get_or_fabricate(field_name) for field_name in field_names]
        self._force_fetch = any(field.cached is not True for field in relevant_fields)

    def _get_items(self):
        returned = self._fetched_items
        if returned is None:
            def _sort_cmp_items(x, y):
                for criteria in self.sort_criteria:
                    sign_func = operator.neg if criteria.prefix == '-' else operator.pos
                    sort_field_name = criteria.field.name
                    x_val = x.get_field(sort_field_name)
                    y_val = y.get_field(sort_field_name)
                    res = cmp(x_val, y_val)
                    if res != 0:
                        return sign_func(res)
                return 0

            with self._get_binder().fetch_tree_once_context(force_fetch=self._force_fetch, with_logging=False):
                all_components = self.system.components._components_by_id.values()  # pylint: disable=protected-access
                returned = [item for item in all_components if self.passed_filtering(item)]

            if self.sort_criteria:
                returned = sorted(returned, key=functools.cmp_to_key(_sort_cmp_items))
            self._fetched_items = returned
        return returned

    def _get_binder(self):
        if self.object_type.get_type_name() == 'infiniboxsystemcomponent':
            return self.system.components.enclosures
        return self.system.components[self.object_type]

    def passed_filtering(self, item):
        if self.object_type != self.system.components.object_type and self.object_type != type(item):
            return False
        if not item.is_in_system():
            return False
        for predicate in self.predicates:
            try:
                op_func = getattr(operator, predicate.operator_name)
            except AttributeError:
                raise NotImplementedError("Filtering by {} operator is not supported".format(predicate.operator_name))
            item_value = item.get_field(predicate.field.name)
            if not op_func(item_value, predicate.value):
                return False
        for k, v in self.kw.items():
            if item.get_field(k) != v:
                return False
        return True

    def page(self, page_index):
        assert page_index == 1 # pragma: no cover
        return self

    def page_size(self, page_size):  # pylint: disable=unused-argument
        return self # pragma: no cover

    def sort(self, *criteria):
        self.sort_criteria += criteria
        return self

    def only_fields(self, field_names):
        raise NotImplementedError()  # pragma: no cover


class InfiniBoxGenericComponentQuery(ComponentQueryBase):
    def __init__(self, system, *predicates, **kw):
        super(InfiniBoxGenericComponentQuery, self).__init__(system, 'All components', *predicates, **kw)

    def _get_items(self):
        if self._fetched_items is not None:
            return self._fetched_items
        items = []
        with self.system.components.fetch_tree_once_context(force_fetch=self._force_fetch, with_logging=False):
            fields = set(predicate.field.name for predicate in self.predicates) | set(self.kw)
            for component_type in self.system.components.get_component_types():
                if not component_type.is_supported(self.system):
                    continue
                if not fields.issubset(set(field.name for field in component_type.fields)):
                    continue
                assert component_type
                collection = self.system.components[component_type]
                query = collection.find(*self.predicates, **self.kw)
                if self._force_fetch:
                    query.force_fetching_objects()
                for item in query:
                    items.append(item)
        self._fetched_items = items
        return self._fetched_items
