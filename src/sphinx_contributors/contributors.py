from docutils import nodes


class Contributor:
    def __init__(self, login, url, contributions=0, avatar_url="", name=""):
        self.contributions = contributions
        self.login = login
        self.url = url
        self.avatar_url = avatar_url
        self.name = name

    @property
    def display_name(self):
        return self.name or self.login

    def build(self, class_name, avatars_only=False):
        container_class = class_name + "_contributor"
        image_class = container_class + "__image"
        username_class = container_class + "__username"
        contributions_class = container_class + "__contributions"

        node_container = nodes.container(classes=[container_class])

        if self.avatar_url:
            node_image = nodes.image(
                uri=self.avatar_url,
                alt=self.display_name,
                classes=[image_class],
            )
            node_image_link = nodes.reference("", refuri=self.url)
            node_image_link += node_image
            node_container += node_image_link

        if avatars_only:
            return node_container

        node_username = nodes.paragraph(classes=[username_class])
        node_username += nodes.reference(text=self.display_name, refuri=self.url)
        node_container += node_username

        if self.contributions:
            node_contributions = nodes.paragraph(classes=[contributions_class])
            node_contributions += nodes.Text(
                str(self.contributions)
                + (" contributions" if self.contributions != 1 else " contribution"),
            )
            node_container += node_contributions
        return node_container


class ContributorsRepository:
    def __init__(
        self,
        contributors,
        reverse=True,
        limit=None,
        exclude=[],
        avatars=False,
        avatars_only=False,
    ):
        sorted_contributors = sorted(
            [c for c in contributors if c.login not in exclude],
            key=lambda c: c.contributions,
            reverse=reverse,
        )
        self.contributors = (
            sorted_contributors[:limit] if limit else sorted_contributors
        )
        self.avatars = avatars
        self.avatars_only = avatars_only

    def build(self, class_name):
        list_class = class_name + "_list"
        item_class = list_class + "__item"

        node_container = nodes.container(classes=[class_name])
        if self.avatars or self.avatars_only:
            node_container["classes"].append(class_name + "--avatars")
        node_list = nodes.bullet_list(classes=[list_class])

        for contributor in self.contributors:
            node_item = nodes.list_item(classes=[item_class])
            node_item += contributor.build(class_name, avatars_only=self.avatars_only)
            node_list += node_item
        node_container += node_list
        return node_container


