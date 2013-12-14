"""A little utility for manually patching in posts."""

import argparse
import codecs
import datetime
import errno
from glob import glob
import os
import time
import subprocess

from rauth.hook import OAuth1Hook
import requests
import yaml

from models import Post
import tla

key, secret = os.environ['CIO_KEY'], os.environ['CIO_SECRET']
aid = os.environ['CIO_AID']

oauth_hook = OAuth1Hook(
    consumer_key=os.environ['CIO_KEY'],
    consumer_secret=os.environ['CIO_SECRET']
)
cio_requests = requests.session(hooks={'pre_request': oauth_hook})


def mkdir_p(path):
    """equivalent to mkdir -p.

    from: http://stackoverflow.com/a/600612/1231454"""

    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def git_checkout_branch(name):
    """Checkout a git branch. The working tree must be clean.

    Raise an exception on failure."""

    if subprocess.call(["git", "diff", "--quiet", "HEAD"]) != 0:
        raise Exception("Dirty working tree; not checking out %s" % name)

    if subprocess.call(["git", "checkout", name]) != 0:
        raise Exception("Could not checkout %s" % name)


def dl_after(args):
    """Download posts received after args.date and write them to _posts."""

    date = datetime.datetime(*[int(i) for i in args.date.split('-')])
    date -= datetime.timedelta(hours=5)
    tstamp = time.mktime(date.timetuple())

    #Download
    msgs = []

    req = cio_requests.get(
        'https://api.context.io/2.0/accounts/' + aid + '/messages',
        params={'folder': 'thelistserve',
                'include_body': 1,
                'body_type': 'text/plain',
                'date_after': tstamp,
                'sort_order': 'asc',
                }

    )

    if req.json:
        msgs += req.json
    else:
        print "error:", req
        print "terminating without writing out"
        return

    posts = [Post.from_cio_message(m) for m in msgs]

    #Write out
    git_checkout_branch('gh-pages')

    mkdir_p('_posts')

    for p in posts:
        # just write out the post
        path, contents = tla.files_to_create(p)[0]

        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(contents)

        print path


def rebuild_from_yaml(args):
    """Write out all files using yaml representations in ``_posts/*.html``."""

    git_checkout_branch('gh-pages')

    posts = []
    for fname in glob('_posts/*.html'):
        with codecs.open(fname, 'r', 'utf-8') as f:
            c = f.read()
            # we only want the yaml frontmatter
            start = c.index('---') + 3
            end = c.rindex('---')
            frontmatter = yaml.safe_load(c[start:end])

            posts.append(Post(**frontmatter['api_data']['post']))

    for p in posts:
        for path, contents in tla.files_to_create(p):
            if path.startswith('_posts'):
                # don't overwrite posts
                continue

            mkdir_p(os.path.dirname(path))

            with codecs.open(path, 'w', 'utf-8') as f:
                f.write(contents)

            print path


def main():
    parser = argparse.ArgumentParser(
        description='A tool to manually patch in posts.')
    commands = parser.add_subparsers(help='commands')

    get_parser = commands.add_parser('dl_after',
                                     help='Download posts through cIO.')
    get_parser.add_argument('date', help='date in YYYY-MM-DD form')
    get_parser.set_defaults(func=dl_after)

    rebuild_parser = commands.add_parser('rebuild_from_yaml',
                                         help='Rebuild all files from from _posts/*.html.')
    rebuild_parser.set_defaults(func=rebuild_from_yaml)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
