import logging
import sys


class LoggerSetup:
    def __init__(
        self, loggerName: str, loggingLevel: str = "info", loggingFormat: dict = None,
    ) -> None:
        self.logger = logging.getLogger(loggerName)
        self.logger.setLevel(level=getattr(logging, loggingLevel.upper()))
        handler = logging.StreamHandler(sys.stdout)

        logFormat = loggingFormat or {
            "logFormat": (
                "%(asctime)s | %(levelname)s | %(filename)s "
                "| %(funcName)s | %(lineno)s : %(message)s"
            ),
            "dateFormat": "%Y-%m-%d %H:%M:%S",
        }
        # https://docs.python.org/3/howto/logging-cookbook.html#use-of-alternative-formatting-styles
        formatter = logging.Formatter(
            logFormat["logFormat"], datefmt=logFormat["dateFormat"]
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def getLogger(self) -> logging.Logger:
        return self.logger
