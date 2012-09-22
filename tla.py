import hmac
import hashlib
import os

from flask import Flask, request
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

    # account_id = request.json['account_id']
    # message_id = request.json['message_id']

    #trade those for a message
    #build a Post
    #convert Post to html
    #commit with the right filename

    return "ok"

    #TODO convert to html
    #then create_gh_commit(...)


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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
