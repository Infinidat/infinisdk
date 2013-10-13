import logbook.compat
import logbook
try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase

handler = None

def setUp():
    global handler
    handler = logbook.compat.LoggingHandler()
    handler.push_application()

def tearDown():
    handler.pop_application()
    from .utils.api_scenarios import _rule_cache
    for filename, rules in _rule_cache.items():
        for rule in rules:
            if not rule.use_count:
                logbook.warning("Rule {}:{} not used", rule.filename, rule.item_index)
