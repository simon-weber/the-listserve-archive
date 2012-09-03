import os

from flask import Flask
import requests


GH_ROOT = 'https://api.github.com/'
GH_USER = os.environ['GITHUB_USER']
GH_SECRET = os.environ['GITHUB_SECRET']
CIO_KEY = os.environ['CIO_KEY']
CIO_SECRET = os.environ['CIO_SECRET']

app = Flask(__name__)


@app.route('/tlpost', methods=['POST'])
def tlpost():
    """POSTed to by context.IO when a new post is received."""
    app.logger.debug("received new post")
    #TODO convert to html
    #create_gh_commit(...)

@app.route('/mailfailure')
def mailfailure():
    """GET by context.IO if the WebHook fails and will no longer be active."""
    app.logger.error("context.IO reports WebHook failure!")
    #TODO need to notify about this

def create_gh_commit(user, passwd, repo, 
        filepath, contents, commit_message, 
        executable=False, force=False):
    """Create a new commit on GitHub. See http://developer.github.com/v3/git/."""

    #Used both:
    # http://www.pqpq.de/2011/07/pithub-how-to-commit-new-file-via.html
    # http://swanson.github.com/blog/2011/07/23/digging-around-the-github-api-take-2.html
    #as a reference here. Neither were totally correct.

    app.loggger.debug("will commit %s",filepath)

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
