import logging.config
import logging.handlers
import atexit

from .config import settings


def setup_logging() -> None:
    logging.config.dictConfig(settings.LOGGING_CONFIG)

    queue_handler: logging.handlers.QueueHandler = logging.getHandlerByName("queue_handler")
    if queue_handler:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)

    logger = logging.getLogger(settings.LOGGER_NAME)
    logger.info("Logging is configured.")