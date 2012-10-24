"""A little utility for manually patching in posts."""

import argparse
import datetime
from glob import glob
import json
import os
import time
import subprocess

from rauth.hook import OAuth1Hook
import requests

from models import Post


key, secret = os.environ['CIO_KEY'], os.environ['CIO_SECRET']
aid = os.environ['CIO_AID']

oauth_hook = OAuth1Hook(
        consumer_key=os.environ['CIO_KEY'],
        consumer_secret=os.environ['CIO_SECRET']
)
cio_requests = requests.session(hooks={'pre_request': oauth_hook})


def git_checkout_branch(name):
    """Checkout a git branch. The working tree must be clean.

    Raise an exception on failure."""

    if subprocess.call(["git", "diff", "--quiet", "HEAD"]) != 0:
        raise Exception("Dirty working tree; not checking out %s" % name)

    if subprocess.call(["git", "checkout", name]) != 0:
        raise Exception("Could not checkout %s" % name)


def dl_after(args):
    """Download posts received after args.date, write them out to individual
    json in ./data, then rebuild ./data/all_posts.json."""

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
                'date_after': tstamp
               }
    )

    if req.json:
        msgs += req.json
    else:
        print "error:", req
        print "will not continue"
        return

    posts = [Post.from_cio_message(m) for m in msgs]

    #Write out
    git_checkout_branch('gh-pages')
    if not os.path.exists('data'):
        #ignore race condition
        os.makedirs('data')

    for p in posts:
        fn = 'data/%s.json' % p.datestr()
        contents = json.dumps(p)

        with open(fn, 'w') as f:
            f.write(contents)

        print fn

    #Rebuild all_posts.json
    #Read in files to include old .jsons
    all_posts = {}

    for fname in glob('data/????-??-??.json'):
        with open(fname) as f:
            post = Post(*json.load(f))

        all_posts[post.datestr()] = post

    with open('data/all_posts.json', 'w') as f:
        f.write(json.dumps(all_posts, sort_keys=True, indent=4))

    print 'data/all_posts.json'


def rebuild_posts(args):
    """Write out ./_posts using ./data/all_posts.json."""

    git_checkout_branch('gh-pages')

    with open('data/all_posts.json') as f:
        all_posts = json.load(f)

    posts = [Post(*p) for p in all_posts.values()]

    if not os.path.exists('_posts'):
        #ignore race condition
        os.makedirs('_posts')

    for p in posts:
        fn, jekyll_html = p.to_jekyll_html()
        fn = '_posts/' + fn

        with open(fn, 'w') as f:
            f.write(jekyll_html)

        print fn


def main():
    parser = argparse.ArgumentParser(
        description='A tool to manually patch in posts.')
    commands = parser.add_subparsers(help='commands')

    get_parser = commands.add_parser('dl_after',
                                     help='Download posts through cIO.')
    get_parser.add_argument('date', help='date in YYYY-MM-DD form')
    get_parser.set_defaults(func=dl_after)

    rebuild_parser = commands.add_parser('rebuild_posts',
                                         help='Rebuild ./_posts from ./data')
    rebuild_parser.set_defaults(func=rebuild_posts)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
