from copy import copy
import datetime
import json
import unittest
import time
import sys

import tla
from githubx import Githubx, file_description
from models import Post
from test_data import cio_email, cio_webhook_post


class TlaTest(unittest.TestCase):
    def setUp(self):
        tla.app.config['TESTING'] = True
        tla.load_env_conf()
        self.app = tla.app.test_client()
        self.githubx = Githubx(
            tla.app.config['GH_USER'],
            tla.app.config['GH_SECRET'],
            user_agent='github.com/simon-weber/the-listserve-archive')

    def tearDown(self):
        pass


class SmallTests(TlaTest):
    """Offline, fast test with no external dependencies."""

    #TODO stub github and move to small tests

    def test_post_datestr(self):
        post = Post('subject', 'author', 'body', (1990, 1, 1))
        for p in post.datestr().split('-'):
            self.assertTrue(len(p) >= 2)

    def test_post_from_cio(self):
        post = Post.from_cio_message(cio_email)

        self.assertEqual('subject', post.subject)
        self.assertEqual('author', post.author)
        self.assertEqual('p1a\np1b\n\np2a\n\n'.split(),
                         post.body.split())
        self.assertEqual(datetime.date.fromtimestamp(0),
                         datetime.date(*post.date))

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

        #TODO unsure how to properly verify this
        fname, contents = post.to_jekyll_html()

        #Make sure we have enough '-'s.
        self.assertTrue(fname.count('-') >= 3)


class BigTests(TlaTest):
    """Possibly online, slow test. Will not mutate external resources."""
    def test_get_gh_readme(self):
        content = self.githubx.get_file(
            repo='the-listserve-archive',
            filepath='README',
            branch='testing')

        self.assertTrue('Orphan branch used for GitHub api testing.',
                        content.split('\n')[0])


class HugeTests(TlaTest):
    """Possibly online, slow test. Might mutate external resources."""

    #TODO verify these by getting the file
    def test_commit_new_file(self):
        new_file = "file-%s" % time.time()

        self.githubx.commit(
            repo='the-listserve-archive',
            file_descriptions=[
                file_description(path=new_file,
                                 contents='new file contents')],
            commit_message='new commit',
            branch='testing')

    def test_commit_update_file(self):
        now = time.time()

        self.githubx.commit(
            repo='the-listserve-archive',
            file_descriptions=[
                file_description(path='README',
                                 contents="Orphan branch used for GitHub api testing.\n%s" % now)],
            commit_message='update commit',
            branch='testing')

    def test_commit_post_data(self):
        tla.commit_post_data(cio_webhook_post, branch='testing')


if __name__ == '__main__':
    arg_to_tests = dict(
        zip(('small', 'big', 'huge'),
            [unittest.defaultTestLoader.loadTestsFromTestCase(tests)
             for tests in (SmallTests, BigTests, HugeTests)]
           ))
    arg_to_tests['all'] = unittest.TestSuite(arg_to_tests.values())

    to_run = arg_to_tests['small']

    if len(sys.argv) > 1:
        to_run = arg_to_tests.get(sys.argv[1])
        if not to_run:
            print 'invalid argument. Possible tests are: ', arg_to_tests.keys()
            exit(-1)

    unittest.TextTestRunner().run(to_run)
