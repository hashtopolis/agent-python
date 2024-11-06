import requests


class Session:
    __instance = None

    def __new__(cls, s=None, using_mtls=False):
        if Session.__instance is None:
            Session.__instance = object.__new__(cls)
            Session.__instance.s = s
            Session.__instance.using_mtls = using_mtls
        return Session.__instance
