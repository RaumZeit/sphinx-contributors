"""
Contributors extension for Sphinx.
(c) 2018 - present David Garcia (@dgarcia360)
# This code is licensed under MIT license (see LICENSE.md for details)
"""

__version__ = "0.3.0"

import os
from pathlib import Path

import requests
from docutils.parsers.rst import Directive, directives
from sphinx.util import logging

from .contributors import Contributor, ContributorsRepository

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


class ContributorsDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "avatars": directives.flag,
        "avatars_only": directives.flag,
        "class_name": directives.unchanged,
        "contributions": directives.flag,
        "exclude": directives.unchanged,
        "include": directives.unchanged,
        "limit": directives.positive_int,
        "names": directives.flag,
        "order": directives.unchanged,
    }

    def run(self):
        avatars_only = "avatars_only" in self.options
        use_avatars = "avatars" in self.options or avatars_only
        class_name = self.options.get("class_name", "sphinx-contributors")
        show_contributions = "contributions" in self.options
        show_names = "names" in self.options
        exclude = [
            _exclude.strip() for _exclude in self.options.get("exclude", "").split(",")
        ]
        include = [
            _include.strip()
            for _include in self.options.get("include", "").split(",")
            if _include.strip()
        ]
        limit = self.options.get("limit", None)
        order = self.options.get("order", "DESC") == "DESC"

        repositories = self.arguments[0].split()
        contributors_by_login = {}
        for repo_name in repositories:
            try:
                results = _github_get_paginated(
                    "https://api.github.com/repos/"
                    + repo_name
                    + "/contributors?per_page=100"
                )
                for c in results:
                    login = c.get("login")
                    if login in contributors_by_login:
                        if show_contributions:
                            contributors_by_login[login].contributions += c.get(
                                "contributions", 0
                            )
                    else:
                        contributors_by_login[login] = Contributor(
                            login,
                            c.get("html_url"),
                            c.get("contributions") if show_contributions else 0,
                            c.get("avatar_url") if use_avatars else "",
                        )
            except Exception:
                logger.warning("The repository " + repo_name + " does not exist.")
        contributors = list(contributors_by_login.values())

        existing_logins = {c.login for c in contributors}
        for login in include:
            if login in existing_logins:
                continue
            try:
                user = requests.get(
                    "https://api.github.com/users/" + login,
                    headers=_github_headers(),
                ).json()
                contributors.append(
                    Contributor(
                        login,
                        user.get("html_url", "https://github.com/" + login),
                        0,
                        user.get("avatar_url", "") if use_avatars else "",
                    )
                )
            except Exception:
                logger.warning("Could not fetch user: " + login)

        repo = ContributorsRepository(
            contributors,
            reverse=order,
            limit=limit,
            exclude=exclude,
            avatars=use_avatars,
            avatars_only=avatars_only,
        )

        if show_names:
            for contributor in repo.contributors:
                try:
                    user = requests.get(
                        "https://api.github.com/users/" + contributor.login,
                        headers=_github_headers(),
                    ).json()
                    contributor.name = user.get("name") or ""
                except Exception:
                    pass

        return [repo.build(class_name)]


def setup(app):
    # Add directive
    app.add_directive("contributors", ContributorsDirective)
    # Add CSS
    static_dir = str(Path(__file__).parent.joinpath("_static").absolute())
    app.connect(
        "builder-inited", (lambda app: app.config.html_static_path.append(static_dir))
    )
    app.add_css_file("sphinx_contributors.css")

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
