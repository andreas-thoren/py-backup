import logging
import sys

LOGGING_INITIALIZED = False

def setup_logging():
    class InfoFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno <= logging.WARNING

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(InfoFilter())
    stdout_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)


def get_logger(name: str) -> logging.Logger:
    global LOGGING_INITIALIZED
    if not LOGGING_INITIALIZED:
        setup_logging()
        LOGGING_INITIALIZED = True
    return logging.getLogger(name)
