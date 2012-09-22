from copy import copy
import json
import unittest
import time
import sys

import tla
from models import Post
from github import Github
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
        self.assertEqual('body\n\n--\n\nunsubscribe'.split(),
                         post.body.split())
        self.assertEqual(0, post.date)

    def test_post_json_serialize(self):
        post = Post.from_cio_message(cio_email)

        json_post = json.dumps(post)
        self.assertEqual(post, Post(*json.loads(json_post)))

    def test_webhook_positive_verification(self):
        self.assertTrue(tla.verify_webhook_post(cio_webhook_post))

    def test_webhook_negative_verification(self):
        bad_post = copy(cio_webhook_post)
        bad_post['signature'] = 'bogus'
        self.assertTrue(not tla.verify_webhook_post(bad_post))

    def test_post_jekyll_conversion(self):
        post = Post.from_cio_message(cio_email)

        fn, content = post.to_jekyll_post()
        #TODO verify better


class BigTests(TlaTest):
    """Possibly online, slow test. Might mutate external resources."""

    def test_commit_new_file(self):
        gh = Github()
        new_file = "file-%s" % time.time()

        #On failure, raise a GithubException
        gh.commit(user=tla.app.config['GH_USER'],
                  passwd=tla.app.config['GH_SECRET'],
                  repo='the-listserve-archive',
                  filepath=new_file,
                  contents='new file contents',
                  commit_message='new commit',
                  branch='testing')

    def test_commit_update_file(self):
        gh = Github()

        #On failure, raise a GithubException
        gh.commit(user=tla.app.config['GH_USER'],
                  passwd=tla.app.config['GH_SECRET'],
                  repo='the-listserve-archive',
                  filepath='README',
                  contents='Orphan branch used for GitHub api testing.',
                  commit_message='update commit',
                  branch='testing')


small_tests, big_tests = (unittest.defaultTestLoader.loadTestsFromTestCase(k)
                          for k in (SmallTests, BigTests))
all_tests = unittest.TestSuite((small_tests, big_tests))

if __name__ == '__main__':
    to_run = small_tests

    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            to_run = all_tests
            print 'Running all tests:'
        elif sys.argv[1] == 'big':
            to_run = big_tests
            print 'Running big tests:'
        else:
            print 'bad argument; not running tests'
            exit(-1)
    else:
        print 'Running small tests:'

    unittest.TextTestRunner().run(to_run)
