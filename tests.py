import os
import unittest
import tempfile
import sys

import tla

class TlaTest(unittest.TestCase):

    def setUp(self):
        tla.app.config['TESTING'] = True
        tla.load_env_conf()
        self.app = tla.app.test_client()

    def tearDown(self):
        pass

    @classmethod
    def create_suite(cls):
        """Return a TestSuite that includes subclasses of this test."""
        suite = unittest.TestSuite()
        suite.addTests(c() for c in cls.__subclasses__())
        return suite

class SmallTest(TlaTest):
    """Offline, fast test with no external dependencies."""
    pass

class BigTest(TlaTest):
    """Possibly online, slow test. Might mutate external resources."""
    pass


small_tests, big_tests = SmallTest.create_suite(), BigTest.create_suite()

if __name__ == '__main__':
    to_run = small_tests

    if len(sys.argv) > 1 and sys.argv[1] == 'big':
        to_run = big_tests

    unittest.TextTestRunner().run(to_run)
