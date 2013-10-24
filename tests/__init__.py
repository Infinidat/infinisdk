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
