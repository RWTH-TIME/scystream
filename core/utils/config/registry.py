import os
import yaml
import logging
from pathlib import Path
from git import Repo, GitCommandError
from utils.config.environment import ENV


class RepoRegistry:
    """Singleton registry managing all configured and cached repos."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._repos = []
            cls._instance._load()
            cls._instance._sync_all()
        return cls._instance

    def _load(self):
        config_file = Path(ENV.REPO_CONFIG_FILE)
        if not config_file.exists():
            logging.warning(f"Repo config file not found: {config_file}")
            self._repos = []
            return

        with open(config_file, "r") as f:
            data = yaml.safe_load(f) or {}
            self._repos = data.get("repos", [])

        logging.info(f"Loaded {len(self._repos)} repos from {config_file}")

    def _sync_all(self):
        os.makedirs(ENV.REPO_CACHE_DIR, exist_ok=True)

        # 1️⃣ Template repo
        self._clone_or_update(ENV.WORKFLOW_TEMPLATE_REPO, ENV.TEMPLATE_DIR)

        # 2️⃣ Cached repos
        for repo_info in self._repos:
            name, url = repo_info["name"], repo_info["url"]
            path = Path(ENV.REPO_CACHE_DIR) / name
            self._clone_or_update(url, path)

    def _clone_or_update(self, url: str, path: Path | str):
        path = Path(path)
        try:
            if not path.exists():
                logging.info(f"Cloning {url} -> {path}")
                Repo.clone_from(
                    url,
                    str(path),
                    multi_options=[
                        "--depth=1",
                        "-c",
                        "core.sshCommand=ssh -o StrictHostKeyChecking=no",
                    ],
                    allow_unsafe_options=True,
                )
                logging.info(f"Cloned {path.name}")
            else:
                logging.info(f"Pulling latest for {path.name}")
                repo = Repo(str(path))
                repo.git.pull(url)
        except GitCommandError as e:
            logging.warning(f"Git operation failed for {path.name}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error syncing {path.name}: {e}")

    def get_cached_repo_path(self, repo_url: str) -> str | None:
        """Return cached repo path if repo_url is configured and exists."""
        repo_url = repo_url.strip()
        for repo in self._repos:
            if repo["url"].strip() == repo_url:
                path = Path(ENV.REPO_CACHE_DIR) / repo["name"]
                if path.exists():
                    return str(path)
        return None

    def list_all(self):
        return self._repos

    def reload(self):
        self._load()
        self._sync_all()
