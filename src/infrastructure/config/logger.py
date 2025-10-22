import re
import logging.config
import logging.handlers
import atexit

from .settings import settings


class PathFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if match := re.match(r"/usr/local/lib/python\d\.\d+/(?:site-packages/)?(.*)", record.pathname):
            matched_path = match.group(1)
            record.pathname = matched_path
        record.pathname = record.pathname.replace("/app/", "")

        return super().format(record)


def setup_logging() -> None:
    logging.config.dictConfig(settings.LOGGING_CONFIG)

    logging.getLogger(settings.LOGGER_NAME).setLevel(settings.BOT_LOGLEVEL)
    for lib in ["sqlalchemy", "sqlalchemy.engine", "sqlmodel"]:
        logging.getLogger(lib).setLevel(settings.SQLALCHEMY_LOGLEVEL)
    for lib in ["telegram", "telegram.ext", "asyncio"]:
        logging.getLogger(lib).setLevel(settings.TELEGRAM_LOGLEVEL)
    for lib in ["httpx", "httpcore"]:
        logging.getLogger(lib).setLevel(settings.HTTP_LOGLEVEL)

    queue_handler: logging.handlers.QueueHandler = logging.getHandlerByName("queue_handler")
    if queue_handler:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)

    logger = logging.getLogger(settings.LOGGER_NAME)
    logger.info("===========Logging is configured.===========")