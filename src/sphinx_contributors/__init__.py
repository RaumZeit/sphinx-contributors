"""
Contributors extension for Sphinx.
(c) 2018 - present David Garcia (@dgarcia360)
# This code is licensed under MIT license (see LICENSE.md for details)
"""

__version__ = "0.3.0"

from pathlib import Path

from docutils.parsers.rst import Directive, directives
from sphinx.util import logging

from .contributors import ContributorsRepository
from .repository import Repository

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
        "provider": directives.unchanged,
    }

    def run(self):
        avatars_only = "avatars_only" in self.options
        use_avatars = "avatars" in self.options or avatars_only
        class_name = self.options.get("class_name", "sphinx-contributors")
        show_contributions = "contributions" in self.options
        show_names = "names" in self.options
        # compile list of additional users to exclude/exclude
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
        provider = self.options.get("provider", "github")

        contributors_by_login = {}

        for r in self.arguments[0].split():
            repo = Repository(r, provider = provider, include = include, exclude = exclude)
            for k, v in repo.get_contributors().items():
                if k not in contributors_by_login:
                    contributors_by_login[k] = v
                else:
                    contributors_by_login[k].update(v)

        contributors = list(contributors_by_login.values())

        repo = ContributorsRepository(
            contributors,
            reverse=order,
            limit=limit,
            exclude=exclude,
            show_names = show_names,
            show_contributions = show_contributions,
            avatars=use_avatars,
            avatars_only=avatars_only
        )

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
