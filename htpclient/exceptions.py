class RestartLoopException(Exception):
    pass


class QuitException(Exception):
    pass


class TaskLoadingError(RestartLoopException):
    pass


class CrackerLoadingError(RestartLoopException):
    pass
