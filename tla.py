import hmac
import hashlib
import os

from flask import Flask, request
from rauth import OAuth1Session

from githubx import Githubx, file_description
from models import Post


ENV_KEYS = ('GH_USER', 'GH_SECRET', 'CIO_KEY', 'CIO_SECRET')

app = Flask(__name__)
app.debug = True


def load_env_conf(keys=ENV_KEYS):
    """A hack, since I'm using Heroku env files + foreman."""
    global app
    for key in keys:
        app.config[key] = os.environ[key]

load_env_conf()


cio_requests = OAuth1Session(os.environ['CIO_KEY'], os.environ['CIO_SECRET'])

githubx = Githubx(
    app.config['GH_USER'],
    app.config['GH_SECRET'],
    user_agent='github.com/simon-weber/the-listserve-archive')


@app.route('/cio/webhook', methods=['POST'])
def receive_mail():
    """POSTed to by context.IO when a new post is received."""
    app.logger.debug("received new post")
    app.logger.debug(request.form)
    app.logger.debug(request.json())

    if not verify_webhook_post(request.json()):
        return "invalid"

    commit_post_data(request.json())

    return "ok"


@app.route('/cio/webhookfailure', methods=['GET', 'POST'])
def handle_webhook_failure():
    """Context.IO might get or post at this for different kinds of failure."""
    app.logger.error("context.IO reports WebHook failure!")
    app.logger.debug(request.args)
    app.logger.debug(request.json())

    return "ok"


def verify_webhook_post(request_json):
    """Return True if the request is from context.IO.

    http://context.io/docs/2.0/accounts/webhooks."""

    sig = hmac.new(app.config['CIO_SECRET'],
                   msg=str(request_json['timestamp']) + request_json['token'],
                   digestmod=hashlib.sha256).hexdigest()

    return sig == request_json['signature']


def commit_post_data(webhook_request_json, branch='gh-pages'):
    """Commit a .html file in _posts/, a .json in data/, and append to the
    cumulative .json in data/."""

    webhook = webhook_request_json  # convenience

    account_id = webhook['account_id']
    msg_id = webhook['message_data']['message_id']

    msg = cio_requests.get(
        "https://api.context.io/2.0/accounts/{aid}/messages/{mid}".format(
            aid=account_id,
            mid=msg_id),
        params={'include_body': 1,
                'body_type': 'text/plain'}
    )

    # context.io responded with a list once?
    app.logger.debug('message response:')
    app.logger.debug(msg.json())

    post = Post.from_cio_message(msg.json())

    path_content_pairs = files_to_create(post)

    githubx.commit(
        repo='the-listserve-archive',
        file_descriptions=[file_description(*pair) for pair in path_content_pairs],
        commit_message="add post (%s)" % post.datestr(),
        branch=branch)


def files_to_create(post):
    """Return a list of (filepath, contents) pairs.

    The first item in the list will be for _posts."""

    post_fname, jekyll_html = post.to_jekyll_html()

    date_path = os.path.join(*post.datestr().split('-'))

    json_fname = date_path + '.json'
    jekyll_json = post.to_jekyll_json()

    multipost_fname = date_path + '.html'
    jekyll_multipost = post.to_jekyll_multipost()

    return [
        (os.path.join('_posts', post_fname),
         jekyll_html),
        (json_fname,
         jekyll_json),
        (multipost_fname,
         jekyll_multipost),
    ]

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
