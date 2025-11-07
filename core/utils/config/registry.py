import logging
from pathlib import Path
from urllib.parse import urlparse
from utils.config.environment import ENV
import os
from git import Repo
import subprocess
from fastapi import HTTPException


class RepoRegistry:
    """Singleton registry managing all configured and cached repos."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._repos = []
            cls._instance._load()
        return cls._instance

    def _load(self):
        cache_dir = Path(ENV.REPO_CACHE_DIR)

        if not cache_dir.exists():
            logging.warning(f"Repo cache dir does not exist: {cache_dir}")
            self._repos = []
            return

        repos = []
        for entry in cache_dir.iterdir():
            if entry.is_dir() and (entry / ".git").exists():
                repos.append(entry)

        self._repos = repos
        logging.info(
                f"Loaded {len(self._repos)} cached repos from {cache_dir}"
            )

    def _get_repo_name_from_url(self, repo_url: str) -> str:
        url = repo_url.strip()

        # Normalize ssh clone "url"
        if ":" in url and not url.startswith(
            ("http://", "https://", "ssh://", "git://")
        ):
            url = "ssh://" + repo_url.replace(":", "/", 1)

        parsed = urlparse(url)
        repo = os.path.basename(parsed.path)

        # Strip trailing .git
        if repo.endswith(".git"):
            repo = repo[:-4]

        return repo

    def get_repo(self, repo_url: str) -> str:
        """
        Return cached repo path if repo_url is configured and exists.
        Clones repo to cache if not exists
        """
        repo_name = self._get_repo_name_from_url(repo_url)
        path = Path(ENV.REPO_CACHE_DIR) / repo_name

        if path.exists():
            return str(path)
        else:
            # If repo not cached, clone and return path
            try:
                logging.info(f"Repo {repo_url} not cached, cloning...")
                Repo.clone_from(
                    repo_url,
                    path,
                    multi_options=[
                        "--depth=1",
                        "-c",
                        "core.sshCommand=ssh -o StrictHostKeyChecking=no"
                    ],
                    allow_unsafe_options=True
                )

                return str(path)
            except subprocess.CalledProcessError as e:
                logging.error(
                    f"Could not clone the repository {repo_url}: {e}"
                )
                raise HTTPException(
                    status_code=422,
                    detail=f"Couldn't clone the repository: {repo_url}"
                )
            except HTTPException as e:
                raise e

    def list_all(self):
        return self._repos

    def reload(self):
        self._load()
