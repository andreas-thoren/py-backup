import logging
import sys


class LoggingConfigurator:
    # TODO change default log level to logging.INFO when program is ready
    STDOUT_LOG_LEVEL = logging.DEBUG
    STDERR_LOG_LEVEL = logging.ERROR
    LOG_FORMAT = "%(levelname)s | %(asctime)s | Message: %(message)s"
    LOG_DATEFORMAT = "%Y-%m-%dT%H:%M:%SZ"

    _initialized = False

    @classmethod
    def setup_logging(cls):
        if cls._initialized:
            return

        logger = logging.getLogger()
        logger.setLevel(cls.STDOUT_LOG_LEVEL)

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(cls.STDOUT_LOG_LEVEL)
        stdout_handler.addFilter(lambda record: record.levelno < cls.STDERR_LOG_LEVEL)
        stdout_handler.setFormatter(
            logging.Formatter(cls.LOG_FORMAT, datefmt=cls.LOG_DATEFORMAT)
        )

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(cls.STDERR_LOG_LEVEL)
        stderr_handler.setFormatter(
            logging.Formatter(cls.LOG_FORMAT, datefmt=cls.LOG_DATEFORMAT)
        )

        logger.addHandler(stdout_handler)
        logger.addHandler(stderr_handler)
        cls._initialized = True


def get_logger(name: str) -> logging.Logger:
    LoggingConfigurator.setup_logging()
    return logging.getLogger(name)
