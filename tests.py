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
        #TODO verify


class BigTests(TlaTest):
    """Possibly online, slow test. Will not mutate external resources."""
    def test_get_gh_readme(self):
        content = Github().get_file(
            user=tla.app.config['GH_USER'],
            repo='the-listserve-archive',
            filepath='README',
            branch='testing')

        self.assertTrue('Orphan branch used for GitHub api testing.', content)


class HugeTests(TlaTest):
    """Possibly online, slow test. Might mutate external resources."""

    #TODO verify these by getting the file
    def test_commit_new_file(self):
        new_file = "file-%s" % time.time()

        #On failure, raise a GithubException
        Github().commit(user=tla.app.config['GH_USER'],
                  passwd=tla.app.config['GH_SECRET'],
                  repo='the-listserve-archive',
                  filepath=new_file,
                  content='new file contents',
                  commit_message='new commit',
                  branch='testing')

    def test_commit_update_file(self):
        #On failure, raise a GithubException
        Github().commit(user=tla.app.config['GH_USER'],
                  passwd=tla.app.config['GH_SECRET'],
                  repo='the-listserve-archive',
                  filepath='README',
                  content='Orphan branch used for GitHub api testing.',
                  commit_message='update commit',
                  branch='testing')

arg_to_tests = dict(
    zip(('small', 'big', 'huge'),
        [unittest.defaultTestLoader.loadTestsFromTestCase(tests)
         for tests in (SmallTests, BigTests, HugeTests)]
       )
)
arg_to_tests['all'] = unittest.TestSuite(arg_to_tests.values())

if __name__ == '__main__':
    to_run = arg_to_tests['small']

    if len(sys.argv) > 1:
        to_run = arg_to_tests.get(sys.argv[1])
        if not to_run:
            print 'invalid argument. Possible tests are: ', arg_to_tests.keys()
            exit(-1)

    unittest.TextTestRunner().run(to_run)
