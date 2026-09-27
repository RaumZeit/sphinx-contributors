import os
import re
import requests
import subprocess

from sphinx.util import logging

from .contributors import Contributor

logger = logging.getLogger(__name__)

email_pat = re.compile(r"(.*)\s+\<(.*)\>")


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


def get_github_contributors(repo_name, exclude = [], anonymous = False, pages = 100, default_avatar = ""):
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
            avatar = c.get("avatar_url", default_avatar)
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
        logger.warning(f"Error while retrieving data from github repository \"{repo_name}\" {err=}, {type(err)=}")

    return contributors


def get_github_user_data(login, default_avatar = ""):
    try:
        user = requests.get(
            "https://api.github.com/users/" + login,
            headers=_github_headers(),
        ).json()
        return Contributor(
                    login         = login,
                    url           = user.get("html_url", "https://github.com/" + login),
                    contributions = 0,
                    avatar_url    = user.get("avatar_url", default_avatar),
                    name          = user.get("name", ""),
                    email         = user.get("email", "")
                )
    except Exception:
        pass

    return None


def _git_shortlog(repo_name):
    result = subprocess.run(['git',
                             '-C', repo_name,
                             'shortlog',
                             '--summary',
                             '--numbered',
                             '--email'
                            ],
                            stdout=subprocess.PIPE)

    return result.stdout.decode()


def get_local_contributors(repo_name, exclude = [], default_avatar = ""):
    contributors = {}

    for r in _git_shortlog(repo_name).split("\n"):
        rr = r.strip().split("\t")
        if len(rr) > 1:
            count, contributor = r.strip().split("\t")
            m = email_pat.match(contributor)
            if m:
                name, email = m.group(1), m.group(2)
                contributors[email] = Contributor(
                    login         = email,
                    url           = "",
                    contributions = int(count),
                    name          = name,
                    email         = email,
                    avatar_url    = default_avatar
                )

    return contributors


class Repository:
    def __init__(self, url, provider = "github", include = [], exclude = [], rst_dir = ".", default_avatar = ""):
        self.url = url
        self.provider = provider
        self.include = include
        self.exclude = exclude
        self.rst_dir = rst_dir
        self.default_avatar = default_avatar

    def get_contributors(self):
        """
        Query github reposirtory to get list of contributors
        """
        get_user_data = None

        contributors = {}

        if self.provider == "github":
            contributors = get_github_contributors(self.url, self.exclude, self.default_avatar)
            get_user_data = get_github_user_data
        elif self.provider == "local":
            contributors = get_local_contributors(os.path.join(self.rst_dir, self.url), self.exclude, self.default_avatar)

        if callable(get_user_data):
            # get more contributor data
            for login in contributors.keys():
                d = get_user_data(login, self.default_avatar)
                if d:
                    contributors[login].update(d)

             # add all auxiliary contributors
            for login in self.include:
                # skip if we already have this contributor in our list
                if login in contributors:
                    continue

                d = get_user_data(login, self.default_avatar)

                if d:
                    contributors[login] = d
                else:
                    logger.warning("Could not fetch data for auxiliary user: " + login)

        return contributors


