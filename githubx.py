"""Allows use of some high-level git operations at GitHub."""

import base64
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

        head_ref = gh_repo.get_git_ref("heads/%s" % branch)
        latest_commit = gh_repo.get_git_commit(head_ref.object.sha)

        base_tree = latest_commit.tree

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

        head_ref.edit(sha=new_commit.sha, force=force)

    @_atomic
    def get_file(self, repo, filepath, branch='master'):
        """Return a unicode string of the file contents.
        Raise a github.GithubException is the file is not found."""

        #Raising an exception isn't the best general api, but for my use
        #it makes the most sense; I always expect the file to be there.

        gh_repo = self._gh.get_user().get_repo(repo)

        latest_commit = gh_repo.get_git_ref("heads/%s" % branch)

        base_tree = gh_repo.get_git_commit(latest_commit.object.sha).tree

        matching_blobs = [el for el in base_tree.tree
                          if el.type == 'blob' and
                          el.path == filepath]

        if not matching_blobs:
            raise github.GithubException('File not found in repo.')

        blob = gh_repo.get_git_blob(matching_blobs[0].sha)

        if blob.encoding == 'base64':
            return base64.b64decode(blob.content)
        else:
            return blob.content
