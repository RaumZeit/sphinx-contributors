import os
import requests
from sphinx.util import logging

from .contributors import Contributor

logger = logging.getLogger(__name__)


def _github_headers():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return {"Authorization": "token " + token}
    return {}


def _github_get_paginated(url):
    results = []
    headers = _github_headers()
    while url:
        r = requests.get(url, headers=headers)
        results.extend(r.json())
        url = r.links.get("next", {}).get("url")
    return results

class Repository:
    def __init__(self, url, provider = "github", include = [], exclude = []):
        self.url = url
        self.provider = provider
        self.include = include
        self.exclude = exclude

    def get_contributors(self):
        """
        Query github reposirtory to get list of contributors
        """
        contributors = {}

        print(f"query data for {self.url}")
        try:
            results = _github_get_paginated(
                "https://api.github.com/repos/"
                + self.url
                + "/contributors?per_page=100"
            )

            for c in results:
                login = c.get("login")

                if login in self.exclude:
                    continue

                contributors[login] = Contributor(
                        login,
                        c.get("html_url"),
                        c.get("contributions"),
                        c.get("avatar_url"),
                    )
        except Exception as err:
            logger.warning(f"Error while retrieving data from github repository \"{self.url}\" {err=}, {type(err)=}")

        # add all auxiliary contributors
        for login in self.include:
            # skip if we already have this contributor in our list
            if login in contributors:
                continue

            try:
                user = requests.get(
                    "https://api.github.com/users/" + login,
                    headers=_github_headers(),
                ).json()
                contributors[login] = Contributor(
                        login,
                        user.get("html_url", "https://github.com/" + login),
                        0,
                        user.get("avatar_url", ""),
                    )
            except Exception:
                logger.warning("Could not fetch auxiliary github user: " + login)

        # query contributor names from logins
        for login in contributors.keys():
            try:
                user = requests.get(
                    "https://api.github.com/users/" + login,
                    headers=_github_headers(),
                ).json()
                contributors[login].name = user.get("name") or ""
            except Exception:
                pass

        return contributors


