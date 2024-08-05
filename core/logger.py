import logging
import socket
import sys

from .version import get_version


class Logger:
    LOGGER_NAME = "render_vault"

    FORMAT_DEFAULT = f"[%(name)s][{get_version()}][%(levelname)s] %(message)s"

    LEVEL_DEFAULT = logging.DEBUG
    PROPAGATE_DEFAULT = True

    _logger_obj = None

    @classmethod
    def logger_obj(cls):
        if not cls._logger_obj:
            if cls.logger_exists():
                cls._logger_obj = logging.getLogger(cls.LOGGER_NAME)
            else:
                cls._logger_obj = logging.getLogger(cls.LOGGER_NAME)

                cls._logger_obj.setLevel(cls.LEVEL_DEFAULT)
                cls._logger_obj.propagate = cls.PROPAGATE_DEFAULT

                fmt = logging.Formatter(cls.FORMAT_DEFAULT)

                stream_handler = logging.StreamHandler(sys.stdout)
                stream_handler.setFormatter(fmt)
                cls._logger_obj.addHandler(stream_handler)

        return cls._logger_obj

    @classmethod
    def logger_exists(cls):
        return cls.LOGGER_NAME in logging.Logger.manager.loggerDict.keys()

    @classmethod
    def set_level(cls, level):
        lg = cls.logger_obj()
        lg.setLevel(level)

    @classmethod
    def set_propagate(cls, propagate):
        lg = cls.logger_obj()
        lg.propagate = propagate

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.debug(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.warning(msg, *args, **kwargs)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.error(msg, *args, **kwargs)

    @classmethod
    def critical(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.critical(msg, *args, **kwargs)

    @classmethod
    def log(cls, level, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.log(level, msg, *args, **kwargs)

    @classmethod
    def exception(cls, msg, *args, **kwargs):
        lg = cls.logger_obj()
        lg.exception(msg, *args, **kwargs)

    @classmethod
    def write_to_file(cls, path, level=logging.INFO):
        lg = cls.logger_obj()

        # Check if there is already a FileHandler with the same path
        for handler in lg.handlers:
            if (
                isinstance(handler, logging.FileHandler)
                and handler.baseFilename == path
            ):
                return  # If the FileHandler already exists, exit the method

        # If no matching FileHandler is found, create and add one
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(level)

        hostname = socket.gethostname()
        fmt = logging.Formatter(
            fmt=f"[%(asctime)s][{hostname}][{get_version()}][%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M",
        )
        file_handler.setFormatter(fmt)
        lg.addHandler(file_handler)


if __name__ == "__main__":
    Logger.set_propagate(False)

    Logger.debug("debug message")
    Logger.info("info message")
    Logger.warning("warning message")
    Logger.error("error message")
    Logger.critical("critical message")
