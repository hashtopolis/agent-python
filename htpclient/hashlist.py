import logging
import os
from typing import Any


class Hashlist:
    """Class representing a hashlist"""

    def __init__(self, agent: Any, hashlist_id: int):  # pylint: disable=E0601:used-before-assignment
        self.hashlist_id = hashlist_id
        self.agent = agent

        if not self.__load():
            self.agent.send_error("Loading hashlist failed")
            raise RuntimeError("Loading hashlist failed")

    def __load(self):
        hashlists_dir = self.agent.config.get_value("hashlists-path")

        if not isinstance(hashlists_dir, str):
            return False

        self.path = os.path.join(hashlists_dir, str(self.hashlist_id))

        if os.path.isfile(self.path):
            logging.info("Hashlist already loaded.")
            return True

        query: dict[str, Any] = {
            "action": "getHashlist",
            "hashlistId": self.hashlist_id,
        }

        response = self.agent.post(query)

        if response is None:
            return False

        if not response["url"]:
            self.agent.send_error(f"Getting hashlist failed {response}")
            return False

        if not self.agent.download(response["url"], self.path):
            return False

        return True

    def load_found_hashes(self, hashlist_id: int, cracker_id: int):
        """Load found hashes from the hashlist"""
        query = {
            "action": "getFound",
            "hashlistId": hashlist_id,
        }

        response = self.agent.post(query)

        if response is None:
            return False

        if not self.agent.download(
            response["url"],
            os.path.join(self.agent.config.get_value("crackers-path"), str(cracker_id), "hashcat.potfile"),  # type: ignore
        ):
            return False

        return True
