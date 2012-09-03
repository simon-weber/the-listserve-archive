import os

from flask import Flask
import requests

ENV_KEYS = ('GH_USER', 'GH_SECRET', 'CIO_KEY', 'CIO_SECRET')

app = Flask(__name__)
app.config['GH_ROOT'] = 'https://api.github.com/'

def load_env_conf(keys=ENV_KEYS):
    """A hack, since I'm using Heroku env files + foreman."""
    global app
    for key in keys:
        app.config[key] = os.environ[key]

load_env_conf()

@app.route('/tlpost', methods=['POST'])
def tlpost():
    """POSTed to by context.IO when a new post is received."""
    app.logger.debug("received new post")
    app.logger.debug(request)
    app.logger.debug(request.json)

    return "ok"

    #TODO convert to html
    #then create_gh_commit(...)

@app.route('/mailfailure')
def mailfailure():
    """GET by context.IO if the WebHook fails and will no longer be active."""
    app.logger.error("context.IO reports WebHook failure!")
    app.logger.debug(request)
    app.logger.debug(request.json)

    #apparently, cIO will email me when this fails; might not even need this

    return "ok"


def create_gh_commit(user, passwd, repo, 
        filepath, contents, commit_message, 
        executable=False, force=False):
    """Create a new commit on GitHub. See http://developer.github.com/v3/git/."""

    #Used both:
    # http://www.pqpq.de/2011/07/pithub-how-to-commit-new-file-via.html
    # http://swanson.github.com/blog/2011/07/23/digging-around-the-github-api-take-2.html
    #as a reference here. Neither were totally correct.

    app.loggger.debug("will commit %s",filepath)

    GH_ROOT = app.config['GH_ROOT']

    sha_latest_commit = requests.get(GH_ROOT+"repos/{user}/{repo}/git/refs/heads/master".format(
        user=user,
        repo=repo)
        ).json['object']['sha']

    sha_base_tree = requests.get(GH_ROOT+"repos/{user}/{repo}/git/commits/{sha}".format(
        user=user,
        repo=repo,
        sha=sha_latest_commit)
        ).json['tree']['sha']

    sha_new_tree = requests.post(GH_ROOT+"repos/{user}/{repo}/git/trees".format(
        user=user,
        repo=repo
        ),
        auth = (user, passwd),
        data = json.dumps({
            'base_tree':sha_base_tree,
            'tree':[
                {
                    'path': filepath,
                    'mode': '100755' if executable else '100644',
                    'type': 'blob',
                    'content': contents
                    }
                ],
            })
        ).json['sha']

    sha_new_commit = requests.post(GH_ROOT+"repos/{user}/{repo}/git/commits".format(
        user=user,
        repo=repo
        ),
        auth = (user, passwd),
        data = json.dumps({
            'message': commit_message,
            'parents':[sha_latest_commit],
            'tree': sha_new_tree,
            })
        ).json['sha']

    app.logger.debug(requests.patch(GH_ROOT+"repos/{user}/{repo}/git/refs/heads/master".format(
        user=user,
        repo=repo
        ),
        auth = (user, passwd),
        data = json.dumps({
            'sha':sha_new_commit,
            'force': force
            })
        ).json)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
