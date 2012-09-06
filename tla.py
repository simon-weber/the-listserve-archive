from collections import namedtuple
from datetime import datetime
import os
import json
from threading import Lock

from flask import Flask, request
from rauth.hook import OAuth1Hook
import requests
import chardet


ENV_KEYS = ('GH_USER', 'GH_SECRET', 'CIO_KEY', 'CIO_SECRET')
GH_LOCK = Lock()  # used to ensure only one thread is mutating GitHub at a time

app = Flask(__name__)
app.config['GH_ROOT'] = 'https://api.github.com/'
app.debug = True


def load_env_conf(keys=ENV_KEYS):
    """A hack, since I'm using Heroku env files + foreman."""
    global app
    for key in keys:
        app.config[key] = os.environ[key]

load_env_conf()


#Set up cIO session.
oauth_hook = OAuth1Hook(
    consumer_key=app.config['CIO_KEY'],
    consumer_secret=app.config['CIO_SECRET'])
cio_requests = requests.session(hooks={'pre_request': oauth_hook})


@app.route('/tlpost', methods=['POST'])
def tlpost():
    """POSTed to by context.IO when a new post is received."""
    app.logger.debug("received new post")
    app.logger.debug(request.form)
    app.logger.debug(request.json)

    account_id = request.json['account_id']
    message_id = request.json['message_id']

    #trade those for a message
    #build a Post
    #convert Post to html
    #commit with the right filename

    return "ok"

    #TODO convert to html
    #then create_gh_commit(...)


@app.route('/mailfailure')
def mailfailure():
    """GET by context.IO if the WebHook fails and will no longer be active."""
    app.logger.error("context.IO reports WebHook failure!")
    app.logger.debug(request.form)
    app.logger.debug(request.json)

    #need to notify; cIO only notifies on the first failure

    return "ok"


class Post(namedtuple('Post', ['subject', 'author', 'body', 'date',
                               'raw_body', 'raw_charset'])):
    """Represents a single Listserve email post.

    It stores raw body and charset information so decoding issues can be fixed
    retroactively.

    date:   a datetime object
    raw_*:  unicode
    others: bytestrings
    """

    @staticmethod
    def from_cio_message(message):
        subject = message['subject'].encode()

        m_from = message['addresses']['from']
        author = m_from['name'].encode() if 'name' in m_from else 'Anonymous'

        m_body = message['body'][0]   # Listserve always sends 1 plaintext body
        raw_body = m_body['content']
        raw_charset = m_body['charset']

        try:
            body = raw_body.encode(raw_charset)
        except UnicodeError:
            guess_enc = chardet.detect(body)['encoding']
            body = raw_body.encode(guess_enc, errors='replace')

        date = datetime.fromtimestamp(message['date'])

        return Post(subject, author, body, date, raw_body, raw_charset)


def create_gh_commit(user, passwd, repo,
                     filepath, contents, commit_message,
                     executable=False, force=False):
    """Create a new commit on GitHub.

    See http://developer.github.com/v3/git/."""

    #TODO insert link to my blog post about this.

    app.loggger.debug("will commit %s", filepath)

    GH_ROOT = app.config['GH_ROOT']

    with GH_LOCK:

        sha_latest_commit = requests.get(
            GH_ROOT + "repos/{user}/{repo}/git/refs/heads/master".format(
                user=user,
                repo=repo)
        ).json['object']['sha']

        sha_base_tree = requests.get(
            GH_ROOT + "repos/{user}/{repo}/git/commits/{sha}".format(
                user=user,
                repo=repo,
                sha=sha_latest_commit)
        ).json['tree']['sha']

        sha_new_tree = requests.post(
            GH_ROOT + "repos/{user}/{repo}/git/trees".format(
                user=user,
                repo=repo
            ),
            auth=(user, passwd),
            data=json.dumps({
                'base_tree': sha_base_tree,
                'tree': [
                    {
                        'path': filepath,
                        'mode': '100755' if executable else '100644',
                        'type': 'blob',
                        'content': contents
                    }
                ],
            })
        ).json['sha']

        sha_new_commit = requests.post(
            GH_ROOT + "repos/{user}/{repo}/git/commits".format(
                user=user,
                repo=repo
            ),
            auth=(user, passwd),
            data=json.dumps({
                'message': commit_message,
                'parents': [sha_latest_commit],
                'tree': sha_new_tree,
            })
        ).json['sha']

        app.logger.debug(requests.patch(
            GH_ROOT + "repos/{user}/{repo}/git/refs/heads/master".format(
                user=user,
                repo=repo
            ),
            auth=(user, passwd),
            data=json.dumps({
                'sha': sha_new_commit,
                'force': force
            })
        ).json)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
