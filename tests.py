from copy import copy
import unittest
import sys

import tla
from models import Post
from test_data import cio_email, cio_webhook_post


class TlaTest(unittest.TestCase):

    def setUp(self):
        tla.app.config['TESTING'] = True
        tla.load_env_conf()
        self.app = tla.app.test_client()

    def tearDown(self):
        pass


class SmallTests(TlaTest):
    """Offline, fast test with no external dependencies."""

    def test_post_conversion(self):
        post = Post.from_cio_message(cio_email)

        self.assertEqual('subject', post.subject)
        self.assertEqual('author', post.author)
        self.assertEqual('body', post.body)
        self.assertEqual(0, post.date)

    def test_webhook_positive_verification(self):
        self.assertTrue(tla.verify_webhook_post(cio_webhook_post))

    def test_webhook_negative_verification(self):
        bad_post = copy(cio_webhook_post)
        bad_post['signature'] = 'bogus'
        self.assertTrue(not tla.verify_webhook_post(bad_post))


class BigTests(TlaTest):
    """Possibly online, slow test. Might mutate external resources."""
    pass


small_tests, big_tests = (unittest.defaultTestLoader.loadTestsFromTestCase(k)
                          for k in (SmallTests, BigTests))

if __name__ == '__main__':
    to_run = small_tests

    if len(sys.argv) > 1 and sys.argv[1] == 'big':
        to_run = big_tests

    unittest.TextTestRunner().run(to_run)
