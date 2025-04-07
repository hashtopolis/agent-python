from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from htpclient import Agent


class ChunkStatus(Enum):
    """Enum representing the status of a chunk"""

    KEYSPACE_REQUIRED = -1
    BENCHMARK = -2
    FULLY_DISPATCHED = 0
    HEALTH_CHECK = -3
    NORMAL = 1


class Chunk:
    """Class representing a chunk of keyspace"""

    def __init__(self, agent: Agent, task_id: int):  # pylint: disable=E0601:used-before-assignment
        self.agent = agent
        self.task_id = task_id

        if not self.__load():
            self.agent.send_error("Loading chunk failed")
            raise RuntimeError("Loading chunk failed")

    def __load(self):
        query: dict[str, Any] = {
            "action": "getChunk",
            "taskId": self.task_id,
        }

        response = self.agent.post(query)

        if response is None:
            return False

        self.status = (
            ChunkStatus[response["status"].upper()]
            if response["status"].upper() in ChunkStatus.__members__
            else ChunkStatus.NORMAL
        )

        if self.status == ChunkStatus.HEALTH_CHECK:
            return True

        if self.status == ChunkStatus.KEYSPACE_REQUIRED:
            return True

        if self.status == ChunkStatus.BENCHMARK:
            return True

        if self.status == ChunkStatus.FULLY_DISPATCHED:
            return True

        self.length = int(response["length"])
        self.chunk_id = int(response["chunkId"])
        self.skip = int(response["skip"])

        return True

    def send_keyspace(self, keyspace: int):
        """Send the keyspace to the server"""
        query: dict[str, Any] = {
            "action": "sendKeyspace",
            "taskId": self.task_id,
            "keyspace": keyspace,
        }

        response = self.agent.post(query)

        if response is None:
            return False

        return True
