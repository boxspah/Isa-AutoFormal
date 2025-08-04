import sys
import os
import logging


class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.buffer = ""

    def write(self, message):
        if message:
            self.buffer += message
            if message[-1] == "\n":
                self.logger.log(self.level, self.buffer.rstrip())
                self.buffer = ""

    def flush(self):
        if self.buffer:
            self.logger.log(self.level, self.buffer.rstrip())
            self.buffer = ""


def logging_init(log_path):
    if not os.path.exists("./logs"):
        os.makedirs("./logs")
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(f"{log_path}", mode="w"),
            logging.StreamHandler(),
        ],
    )
    sys.stdout = LoggerWriter(logging, logging.INFO)
    sys.stderr = LoggerWriter(logging, logging.ERROR)


import signal


class TimeoutException(Exception):
    pass


def timeout(seconds):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutException()

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    return decorator
