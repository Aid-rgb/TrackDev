"""
Конфигурация логирования для приложения
Поддерживает JSON и text форматы
"""
import logging
import sys
from typing import Any
import json
import os


class StructuredFormatter(logging.Formatter):
    """JSON formatter для structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует лог запись в JSON"""
        log_data = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем extra данные из structured logging
        extra_keys = [
            "user_id", "project_id", "endpoint", "error", "error_type",
            "count", "limit", "period", "duration_ms", "status_code",
            "operation", "cache_key", "params", "health_score", "status"
        ]
        
        for key in extra_keys:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        
        # Stack trace для ошибок
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для консоли"""
    
    # ANSI цвета
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m"        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует лог запись с цветами"""
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        
        # Основной формат
        log_fmt = f"{color}%(asctime)s - %(name)s - %(levelname)s{reset} - %(message)s"
        
        # Добавляем extra данные если есть
        extras = []
        if hasattr(record, "user_id"):
            extras.append(f"user_id={record.user_id}")
        if hasattr(record, "project_id"):
            extras.append(f"project_id={record.project_id}")
        if hasattr(record, "error_type"):
            extras.append(f"error={record.error_type}")
        
        if extras:
            log_fmt += f" [{', '.join(extras)}]"
        
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging(
    level: str = None,
    json_format: bool = None,
    colored: bool = None
):
    """
    Настройка логирования для приложения
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
               По умолчанию берется из переменной окружения LOG_LEVEL или INFO
        json_format: Использовать JSON формат для логов
                     По умолчанию берется из переменной окружения LOG_JSON или False
        colored: Использовать цветной вывод (только для text формата)
                 По умолчанию берется из переменной окружения LOG_COLORED или True
    """
    # Получаем настройки из переменных окружения или используем значения по умолчанию
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    if json_format is None:
        json_format = os.getenv("LOG_JSON", "false").lower() == "true"
    
    if colored is None:
        colored = os.getenv("LOG_COLORED", "true").lower() == "true"
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Создаем handler для stdout
    handler = logging.StreamHandler(sys.stdout)
    
    # Выбираем форматтер
    if json_format:
        handler.setFormatter(StructuredFormatter())
    elif colored and sys.stdout.isatty():  # Цвета только если вывод в терминал
        handler.setFormatter(ColoredFormatter())
    else:
        # Обычный text формат
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
    
    # Настраиваем root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Удаляем старые handlers если есть
    root_logger.handlers.clear()
    
    root_logger.addHandler(handler)
    
    # Уменьшаем verbose сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)
    
    # Логируем информацию о конфигурации
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "level": level,
            "json_format": json_format,
            "colored": colored and sys.stdout.isatty()
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Получить logger с указанным именем
    
    Args:
        name: Имя логгера (обычно __name__)
    
    Returns:
        Настроенный logger
    """
    return logging.getLogger(name)


# Для удобного импорта
__all__ = ["setup_logging", "get_logger"]
