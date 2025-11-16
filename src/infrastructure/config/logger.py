import logging.config
import logging.handlers
import atexit

from .settings import settings


def setup_logging() -> None:
    logging.config.dictConfig(settings.LOGGING_CONFIG)

    logging.getLogger().setLevel(settings.BOT_LOGLEVEL)
    for lib in ["sqlalchemy", "sqlalchemy.engine", "sqlmodel"]:
        logging.getLogger(lib).setLevel(settings.SQLALCHEMY_LOGLEVEL)
    for lib in ["telegram", "telegram.ext", "asyncio"]:
        logging.getLogger(lib).setLevel(settings.TELEGRAM_LOGLEVEL)
    for lib in ["httpx", "httpcore", "urllib3"]:
        logging.getLogger(lib).setLevel(settings.HTTP_LOGLEVEL)

    queue_handler: logging.handlers.QueueHandler = logging.getHandlerByName("queue_handler")
    if queue_handler:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)

    logger = logging.getLogger(__name__)
    logger.info("=========== Logging is configured ===========")