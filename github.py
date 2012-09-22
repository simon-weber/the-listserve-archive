import json
import requests
from threading import Lock

from decorator import decorator


class GithubException(Exception):
    """Raised when GitHub returns an error from an api call."""
    pass


class Github:

    @staticmethod
    def _verify(res):
        """Given a requests response, raise a _GithubException_ on an error."""

        if not res.ok:
            raise GithubException(str(res) + ':' + str(res.json))

        return res

    def __init__(self, api_url='https://api.github.com/'):
        self.API = api_url
        self._mutex = Lock()

    @decorator
    def _atomic(f, self, *args, **kwargs):
        """Ensure the decorated method is the only one in this instance
        modifying GitHub resorces."""

        with self._mutex:
            return f(self, *args, **kwargs)

    @_atomic
    def commit(self, user, passwd, repo,
               filepath, contents, commit_message,
               branch='master',
               executable=False, force=False):
        """Make a commit on GitHub.

        If _filepath_ exists, it will be replaced; if not, it will be created.

        Raise GithubException if there is a problem.

        See http://developer.github.com/v3/git/"""

        sha_latest_commit = Github._verify(requests.get(
            self.API + "repos/{user}/{repo}/git/refs/heads/{branch}".format(
                branch=branch,
                user=user,
                repo=repo)
        )).json['object']['sha']

        sha_base_tree = Github._verify(requests.get(
            self.API + "repos/{user}/{repo}/git/commits/{sha}".format(
                user=user,
                repo=repo,
                sha=sha_latest_commit)
        )).json['tree']['sha']

        sha_new_tree = Github._verify(requests.post(
            self.API + "repos/{user}/{repo}/git/trees".format(
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
        )).json['sha']

        sha_new_commit = Github._verify(requests.post(
            self.API + "repos/{user}/{repo}/git/commits".format(
                user=user,
                repo=repo
            ),
            auth=(user, passwd),
            data=json.dumps({
                'message': commit_message,
                'parents': [sha_latest_commit],
                'tree': sha_new_tree,
            })
        )).json['sha']

        Github._verify(requests.patch(
            self.API + "repos/{user}/{repo}/git/refs/heads/{branch}".format(
                branch=branch,
                user=user,
                repo=repo
            ),
            auth=(user, passwd),
            data=json.dumps({
                'sha': sha_new_commit,
                'force': force
            }))
        )
