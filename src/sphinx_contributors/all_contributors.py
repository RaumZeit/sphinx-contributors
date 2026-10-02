import json

def _parse_allcontributors_json(filename):
    try:
        with open(filename, "r", encoding='utf-8') as f:
            return json.load(f)

    except Exception as err:
        print(f"Can't access all-contributors json file \"{filename}\" {err=}, {type(err)=}")
        pass

    return {}


class AllContributors:
    def __init__(self, config_file):
        self.data = _parse_allcontributors_json(config_file)

    @property
    def contributorsPerLine(self):
        return self.data.get('contributorsPerLine', 7)

    @property
    def imageSize(self):
        return int(self.data['imageSize']) if 'imageSize' in self.data and int(self.data['imageSize']) > 0 else 0

    @property
    def contributorsSortAlphabetically(self):
        return self.data.get('contributorsSortAlphabetically', False)

    @property
    def contributors(self):
        return self.data['contributors'] if 'contributors' in self.data else []

