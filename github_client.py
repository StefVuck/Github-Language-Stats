import shutil
import subprocess
import tempfile
from typing import List, Dict, Optional

from github import Github
from github.GithubException import GithubException

from loc_counter import count_loc


class GitHubClient:
    def __init__(self, token: str):
        self.github = Github(token)
        self.token = token
        self.user = self.github.get_user()

    def is_repo_private(self, repo) -> bool:
        return repo.private

    def get_all_repos(self, excluded_repos: Optional[List[str]] = None,
                      include_forks: bool = False) -> List:
        excluded_repos = excluded_repos or []
        repos = []

        for repo in self.user.get_repos(affiliation='owner'):
            if repo.name not in excluded_repos:
                if include_forks or not repo.fork:
                    repos.append(repo)

        return repos

    def get_language_stats(self, repo) -> Dict[str, int]:
        try:
            return repo.get_languages()
        except GithubException as e:
            print(f"Error fetching languages for {repo.name}: {e}")
            return {}

    def get_loc_stats(self, repo) -> Dict[str, int]:
        clone_url = f"https://x-access-token:{self.token}@github.com/{repo.full_name}.git"
        tmp_dir = tempfile.mkdtemp()
        try:
            subprocess.run(
                ['git', 'clone', '--depth=1', '--quiet', clone_url, tmp_dir],
                check=True,
                capture_output=True,
            )
            return count_loc(tmp_dir)
        except subprocess.CalledProcessError as e:
            print(f"Error cloning {repo.name}: {e.stderr.decode().strip()}")
            return {}
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def get_username(self) -> str:
        return self.user.login
