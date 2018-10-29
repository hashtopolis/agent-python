import requests


class Session:
    __instance = None

    def __new__(cls, s=None):
        if Session.__instance is None:
            Session.__instance = object.__new__(cls)
            Session.__instance.s = s
        return Session.__instance
