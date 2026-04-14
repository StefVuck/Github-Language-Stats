from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class LanguageAnalyzer:
    def __init__(self, excluded_languages: Optional[List[str]] = None,
                 hide_private_repo_names: bool = False):
        self.language_bytes = defaultdict(int)
        self.language_repos = defaultdict(set)
        self.language_repo_bytes = defaultdict(lambda: defaultdict(int))
        self.excluded_languages = set(excluded_languages or [])
        self.hide_private_repo_names = hide_private_repo_names
        self.private_repos = set()

    def add_repo_languages(self, repo_name: str, languages: Dict[str, int],
                          is_private: bool = False):
        if is_private:
            self.private_repos.add(repo_name)

        for language, byte_count in languages.items():
            if language not in self.excluded_languages:
                self.language_bytes[language] += byte_count
                self.language_repos[language].add(repo_name)
                self.language_repo_bytes[language][repo_name] = byte_count

    def get_by_repos(self) -> List[Tuple[str, int]]:
        result = list(self.language_repos.items())
        return sorted([(lang, len(repos)) for lang, repos in result],
                     key=lambda x: x[1], reverse=True)

    def get_by_bytes(self) -> List[Tuple[str, int]]:
        result = list(self.language_bytes.items())
        return sorted(result, key=lambda x: x[1], reverse=True)

    def get_by_weighted(self) -> List[Tuple[str, float]]:
        if not self.language_repos:
            return []

        max_repos = max(len(repos) for repos in self.language_repos.values())
        max_bytes = max(self.language_bytes.values()) if self.language_bytes else 1

        weighted_scores = {}
        for language, repos in self.language_repos.items():
            repos_normalized = len(repos) / max_repos
            bytes_normalized = self.language_bytes[language] / max_bytes
            weighted_scores[language] = (repos_normalized + bytes_normalized) / 2

        result = list(weighted_scores.items())
        return sorted(result, key=lambda x: x[1], reverse=True)

    def get_all_languages(self) -> List[str]:
        return list(self.language_repos.keys())

    def get_top_contributing_repos(self, language: str,
                                   top_n: int = 10) -> List[Tuple[str, int]]:
        if language not in self.language_repo_bytes:
            return []

        repo_bytes = self.language_repo_bytes[language]

        if not self.hide_private_repo_names:
            sorted_repos = sorted(repo_bytes.items(), key=lambda x: x[1], reverse=True)
            return sorted_repos[:top_n]

        result = []
        private_total = 0
        private_count = 0

        for repo, byte_count in sorted(repo_bytes.items(), key=lambda x: x[1], reverse=True):
            if repo in self.private_repos:
                private_total += byte_count
                private_count += 1
            else:
                result.append((repo, byte_count))

        if private_count > 0:
            result.append((f"[{private_count} Private Repos]", private_total))

        return sorted(result, key=lambda x: x[1], reverse=True)[:top_n]
