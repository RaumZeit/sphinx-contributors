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


def get_github_contributors(repo_name, exclude = [], anonymous = False, pages = 100):
    """
    Get all contributors from a github repository

    This function retrieves all contributors of a github.com hosted repository
    by querying the github API. It creates a dictionary of Contributor objects
    where the key is the contributors github login.
    If anonymous contributors are requested as well, i.e. contributors without
    a github login, their respective email address is used as key.
    """
    contributors = {}

    try:
        results = _github_get_paginated(
            f"https://api.github.com/repos/{repo_name}" \
            f"/contributors?per_page={pages}{'&anon=1' if anonymous else ''}"
        )

        for c in results:
            ctype = c.get("type", "User")

            if ctype == "User":
                login = c.get("login")
            elif anonymous and ctype == "Anonymous":
                login = c.get("email")
            else:
                continue

            if login in exclude:
                continue

            html_url = c.get("html_url")
            contributions = c.get("contributions", 0)
            email = c.get("email", "")
            avatar = c.get("avatar_url", "")
            name = c.get("name", "")

            contributors[login] = Contributor(
                    login         = login,
                    url           = html_url,
                    contributions = contributions,
                    avatar_url    = avatar,
                    name          = name,
                    email         = email
                )
    except Exception as err:
        logger.warning(f"Error while retrieving data from github repository \"{self.url}\" {err=}, {type(err)=}")

    return contributors


def get_github_user_data(login):
    try:
        user = requests.get(
            "https://api.github.com/users/" + login,
            headers=_github_headers(),
        ).json()
        return Contributor(
                    login         = login,
                    url           = user.get("html_url", "https://github.com/" + login),
                    contributions = 0,
                    avatar_url    = user.get("avatar_url", ""),
                    name          = user.get("name", ""),
                    email         = user.get("email", "")
                )
    except Exception:
        pass

    return None


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
        get_user_data = None

        contributors = {}

        if self.provider == "github":
            contributors = get_github_contributors(self.url, self.exclude)
            get_user_data = get_github_user_data

        # query contributor names from logins
        for login in contributors.keys():
            d = get_user_data(login)
            if d:
                contributors[login].update(d)

         # add all auxiliary contributors
        for login in self.include:
            # skip if we already have this contributor in our list
            if login in contributors:
                continue

            d = get_github_user_data(login)

            if d:
                contributors[login] = d
            else:
                logger.warning("Could not fetch data for auxiliary user: " + login)

        return contributors


