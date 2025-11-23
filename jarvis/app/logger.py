import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from jarvis.app.config import AppConfig


_LOGGER_NAME = "jarvis"


def _build_formatter() -> logging.Formatter:
    # Базовый формат логов: Дата - Имя логгера - Уровень - Сообщение
    return logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def _ensure_file_handler(log_file: Path, level: int) -> RotatingFileHandler:
    # Ротация файла логов, чтобы не разрастался без ограничений
    handler = RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(_build_formatter())
    return handler


def _ensure_console_handler(level: int) -> logging.StreamHandler:
    # Обычная консоль без цветов (для prod)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(_build_formatter())
    return handler


def _ensure_error_file_handler(log_file: Path) -> RotatingFileHandler:
    # Отдельный файл для ошибок (ERROR и выше)
    handler = RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    handler.setLevel(logging.ERROR)
    handler.setFormatter(_build_formatter())
    return handler


class _ColorFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__("%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        try:
            # Цвета для Windows через colorama (если доступна)
            from colorama import Fore, Style, init as colorama_init  # type: ignore

            colorama_init()
            self._colors = {
                logging.DEBUG: Fore.BLUE,
                logging.INFO: Fore.GREEN,
                logging.WARNING: Fore.YELLOW,
                logging.ERROR: Fore.RED,
                logging.CRITICAL: Fore.MAGENTA,
            }
            self._reset = Style.RESET_ALL
        except Exception:
            self._colors = {}
            self._reset = ""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        color = self._colors.get(record.levelno, "")
        if color:
            return f"{color}{base}{self._reset}"
        return base


def _ensure_colored_console_handler(level: int) -> logging.StreamHandler:
    # Цветная консоль (для dev)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(_ColorFormatter())
    return handler


def get_logger(config: AppConfig) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    # Предотвращаем дублирование хендлеров при повторной инициализации
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, config.log_level))
    log_file = config.logs_dir / "jarvis.log"
    errors_file = config.logs_dir / "errors.log"

    logger.addHandler(_ensure_file_handler(log_file, getattr(logging, config.log_level)))
    logger.addHandler(_ensure_error_file_handler(errors_file))
    if config.mode == "dev":
        logger.addHandler(_ensure_colored_console_handler(getattr(logging, config.log_level)))
    else:
        logger.addHandler(_ensure_console_handler(getattr(logging, config.log_level)))
    logger.propagate = False
    return logger


