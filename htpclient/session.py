
from __future__ import annotations

import requests


class Session:
    __instance: Session = None
    s: requests.Session

    def __new__(cls, s: requests.Session | None = None):
        if Session.__instance is None:
            Session.__instance = object.__new__(cls)
            assert isinstance(s, requests.Session)
            Session.__instance.s = s
        return Session.__instance
