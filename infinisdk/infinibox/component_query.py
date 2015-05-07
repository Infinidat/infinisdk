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
import operator
from numbers import Number

from .._compat import cmp, iteritems, itervalues, sorted


class InfiniBoxComponentQuery(object):
    def __init__(self, system, object_type, *predicates, **kw):
        self.system = system
        self.object_type = object_type
        self.predicates = predicates
        self.kw = kw
        self.sort_criteria = tuple()
        self._fetched_items = None
        self._force_fetch = bool(self.predicates) or \
            any(self.object_type.fields.get_or_fabricate(field_name).cached != True for field_name in self.kw)

    def force_fetching_objects(self):
        self._force_fetch = True
        return self

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
                else:
                    return 0

            with self._get_binder().fetch_tree_once_context(force_fetch=self._force_fetch, with_logging=False):
                returned = [item for item in itervalues(self.system.components._components_by_id)
                                 if self.passed_filtering(item)]

            if self.sort_criteria:
                 returned = sorted(returned, cmp=_sort_cmp_items)
            self._fetched_items = returned
        return returned

    def _get_binder(self):
        if self.object_type.get_type_name() == 'infiniboxsystemcomponent':
            return self.system.components.enclosures
        return self.system.components[self.object_type]

    def __iter__(self):
        for item in self._get_items():
            yield item

    def __len__(self):
        return len([item for item in self])

    def to_list(self):
        return list(self)

    def __getitem__(self, index):
        if isinstance(index, Number) and index < 0:
            raise NotImplementedError("Negative indices not supported yet")
        return [item for item in self][index]

    def passed_filtering(self, item):
        if (self.object_type != self.system.components.object_type and
            self.object_type != type(item)):
            return False
        for predicate in self.predicates:
            try:
                op_func = getattr(operator, predicate.operator_name)
            except AttributeError:
                raise NotImplementedError("Filtering by {0} operator is not supported".format(predicate.operator_name))
            item_value = item.get_field(predicate.field.name)
            if not op_func(item_value, predicate.value):
                return False
        for k, v in iteritems(self.kw):
            if item.get_field(k) != v:
                return False
        return True

    def page(self, page_index):
        raise NotImplementedError()  # pragma: no cover

    def page_size(self, page_size):
        raise NotImplementedError()  # pragma: no cover

    def sort(self, *criteria):
        self.sort_criteria += criteria
        return self

    def only_fields(self, field_names):
        raise NotImplementedError()  # pragma: no cover
