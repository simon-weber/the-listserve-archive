import hmac
import hashlib
import json
import os

from github import Github
from flask import Flask, request
from models import Post
from rauth.hook import OAuth1Hook
import requests


ENV_KEYS = ('GH_USER', 'GH_SECRET', 'CIO_KEY', 'CIO_SECRET')

app = Flask(__name__)
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


@app.route('/cio/webhook', methods=['POST'])
def receive_mail():
    """POSTed to by context.IO when a new post is received."""
    app.logger.debug("received new post")
    app.logger.debug(request.form)
    app.logger.debug(request.json)

    if not verify_webhook_post(request.json):
        return "invalid"

    commit_post_data(request.json)

    return "ok"


@app.route('/cio/webhookfailure')
def handle_webhook_failure():
    """GET by context.IO if the WebHook fails and will no longer be active."""
    app.logger.error("context.IO reports WebHook failure!")
    app.logger.debug(request.form)
    app.logger.debug(request.json)

    #TODO need to notify; cIO only notifies on the first failure

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

    post = Post.from_cio_message(msg.json)

    html_fn, jekyll_html = post.to_jekyll_post()
    Github().commit(
        user=app.config['GH_USER'],
        passwd=app.config['GH_SECRET'],
        repo='the-listserve-archive',
        filepath='_posts/' + html_fn,
        content=jekyll_html,
        commit_message='add post html',
        branch=branch)

    Github().commit(
        user=app.config['GH_USER'],
        passwd=app.config['GH_SECRET'],
        repo='the-listserve-archive',
        filepath="data/{tstamp}.json".format(
            tstamp='-'.join(str(i) for i in post.date)
        ),
        content=json.dumps(post),
        commit_message='add post json',
        branch=branch)

    #TODO might need to make this constant, not linear on posts.
    all_posts = json.loads(
        Github().get_file(
            user=app.config['GH_USER'],
            repo='the-listserve-archive',
            filepath='data/all_posts.json',
            branch=branch))

    #Need string keys.
    all_posts['-'.join(str(i) for i in post.date)] = post

    Github().commit(
        user=app.config['GH_USER'],
        passwd=app.config['GH_SECRET'],
        repo='the-listserve-archive',
        filepath='data/all_posts.json',
        content=json.dumps(all_posts, sort_keys=True, indent=4),
        commit_message='add post to cumulative collection',
        branch=branch)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
