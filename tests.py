from datetime import datetime
import unittest
import sys

import tla
from test_data import cio_email


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

    def test_post_conversion(self):
        post = tla.Post.from_cio_message(cio_email)

        for key in range(3):
            self.assertEqual(str, type(post[key]), str(key))

        self.assertEqual('subject', post.subject)
        self.assertEqual('author', post.author)
        self.assertEqual('body', post.body)
        self.assertEqual(datetime.fromtimestamp(0), post.date)

        for key in range(4, 6):
            self.assertEqual(unicode, type(post[key]), str(key))

        self.assertEqual(u'body', post.raw_body)
        self.assertEqual(u'utf-8', post.raw_charset)


class BigTest(TlaTest):
    """Possibly online, slow test. Might mutate external resources."""
    pass


small_tests, big_tests = (unittest.defaultTestLoader.loadTestsFromTestCase(k)
                          for k in (SmallTest, BigTest))

if __name__ == '__main__':
    to_run = small_tests

    if len(sys.argv) > 1 and sys.argv[1] == 'big':
        to_run = big_tests

    unittest.TextTestRunner().run(to_run)
