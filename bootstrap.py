"""A little utility for manually patching in posts."""

import argparse
import codecs
import datetime
import errno
from glob import glob
import os
import pprint
import time
import subprocess
import sys

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


def _write_out(posts, yaml=True, supporting=False):
    for p in posts:
        for path, contents in tla.files_to_create(p):
            if path.startswith('_posts') and not yaml:
                continue
            if not path.startswith('_posts') and not supporting:
                continue

            mkdir_p(os.path.dirname(path))

            with codecs.open(path, 'w', 'utf-8') as f:
                f.write(contents)

            print path


def dl_after(args):
    """Download posts received after args.date and write them to _posts."""

    git_checkout_branch('gh-pages')

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

    _write_out(posts)


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

    _write_out(posts, yaml=False, supporting=True)


def add_manually(args):
    entering = True
    posts = []

    while entering:
        posts.append(get_post_from_user())
        entering = raw_input('again? (y/n): ') == 'y'

    _write_out(posts)


def get_post_from_user():
    ok = False
    sentinel = '<stop>'
    post_kwargs = {
        'subject': None,
        'author': None,
        'body': None,
        'date': None,
    }

    print "enter %r on a line by itself to end input" % sentinel

    while not ok:
        for param in post_kwargs.keys():
            print
            print "%s:" % param
            entered = '\n'.join(iter(raw_input, sentinel))
            post_kwargs[param] = entered.decode(sys.stdin.encoding)

        date_list = [int(i) for i in post_kwargs['date'].split('-')]
        post_kwargs['date'] = date_list

        print
        pprint.pprint(post_kwargs)
        ok = raw_input('confirm (y/n) :') == 'y'

    return Post(**post_kwargs)


def main():
    parser = argparse.ArgumentParser(
        description='A tool to manually patch in posts.')
    commands = parser.add_subparsers(help='commands')

    get_parser = commands.add_parser(
        'dl_after',
        help='Download posts through cIO.')
    get_parser.add_argument('date', help='date in YYYY-MM-DD form')
    get_parser.set_defaults(func=dl_after)

    rebuild_parser = commands.add_parser(
        'rebuild_from_yaml',
        help='Rebuild all files from from _posts/*.html.')
    rebuild_parser.set_defaults(func=rebuild_from_yaml)

    manual_add_parser = commands.add_parser(
        'add_manually',
        help='Create post files by manually entering post content.')
    manual_add_parser.set_defaults(func=add_manually)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
