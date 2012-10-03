"""Allows use of some high-level git operations at GitHub."""

import base64
import requests
from threading import Lock

from decorator import decorator
import github


class Githubx:
    def __init__(self, *args, **kwargs):
        """All parameters are passed to PyGithub."""
        self._gh = github.Github(*args, **kwargs)
        self._mutex = Lock()

    @decorator
    def _atomic(f, self, *args, **kwargs):
        """Ensure the decorated method is the only one in this instance
        modifying GitHub resorces."""

        with self._mutex:
            return f(self, *args, **kwargs)

    @_atomic
    def commit(self, repo, filepath, content,
               commit_message,
               branch='master',
               executable=False, force=False):
        """Make a commit on GitHub.

        If _filepath_ exists, it will be replaced; if not, it will be created.

        See http://developer.github.com/v3/git/"""

        gh_repo = self._gh.get_user().get_repo(repo)

        latest_commit = gh_repo.get_git_ref("heads/%s" % branch)

        base_tree = gh_repo.get_git_commit(latest_commit).tree

        new_tree = gh_repo.create_git_tree(
            [github.InputGitTreeElement(
                path=filepath,
                mode='100755' if executable else '100644',
                type='blob',
                content=content
            )],
            base_tree)

        new_commit = gh_repo.create_git_commit(
            message=commit_message,
            parents=[latest_commit],
            tree=new_tree)

        new_commit.edit(sha=new_commit.sha, force=force)

    @_atomic
    def get_file(self, user, repo,
                 filepath, branch='master'):
        """Returns a unicode string of the file contents."""



        sha_latest_commit = Github._verify(requests.get(
            self._API + "repos/{user}/{repo}/git/refs/heads/{branch}".format(
                user=user,
                repo=repo,
                branch=branch)
        )).json['object']['sha']

        sha_base_tree = Github._verify(requests.get(
            self._API + "repos/{user}/{repo}/git/commits/{sha}".format(
                user=user,
                repo=repo,
                sha=sha_latest_commit)
        )).json['tree']['sha']

        tree = Github._verify(
            requests.get(
                self._API +
                "repos/{user}/{repo}/git/trees/{sha}?recursive=1".format(
                    user=user,
                    repo=repo,
                    sha=sha_base_tree)
            )).json['tree']

        blob_found = [blob for blob in tree
                      if blob['type'] == 'blob' and
                      blob['path'] == filepath]

        if not blob_found:
            raise GithubException('File not found in repo.')

        blob = Github._verify(requests.get(blob_found[0]['url'])).json

        if blob['encoding'] == 'base64':
            return base64.b64decode(blob['content'])
        else:
            return blob['content']
