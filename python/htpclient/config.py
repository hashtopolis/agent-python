import os.path
import json


class Config:
    CONFIG_FILE = "config.json"
    config = {}

    def __init__(self):
        # load from file
        if os.path.isfile(self.CONFIG_FILE):
            self.config = json.load(open(self.CONFIG_FILE))
        else:
            self.__save()

    def update(self):
        self.config = json.load(open(self.CONFIG_FILE))

    def get_value(self, key):
        if key in self.config:
            return self.config[key]
        return ''

    def set_value(self, key, val):
        self.config[key] = val
        self.__save()

    def __save(self):
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
