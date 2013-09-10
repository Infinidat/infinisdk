import logbook.compat
try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase


def setUp():
    logbook.compat.LoggingHandler().push_application()
