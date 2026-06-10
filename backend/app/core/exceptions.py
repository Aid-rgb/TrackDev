"""
Кастомные исключения для Redmine API
Позволяют различать типы ошибок и предоставлять понятные сообщения пользователю
"""


class RedmineException(Exception):
    """Базовое исключение для Redmine операций"""
    def __init__(self, message: str, status_code: int = None, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class RedmineConnectionError(RedmineException):
    """Ошибка подключения к Redmine серверу"""
    def __init__(self, message: str = "Не удалось подключиться к Redmine серверу", details: dict = None):
        super().__init__(message, status_code=502, details=details)


class RedmineTimeoutError(RedmineException):
    """Таймаут при запросе к Redmine"""
    def __init__(self, message: str = "Превышено время ожидания ответа от Redmine", details: dict = None):
        super().__init__(message, status_code=504, details=details)


class RedmineAuthError(RedmineException):
    """Ошибка авторизации в Redmine (неверный API ключ)"""
    def __init__(self, message: str = "Неверный Redmine API ключ. Проверьте ключ в настройках", details: dict = None):
        super().__init__(message, status_code=401, details=details)


class RedmineForbiddenError(RedmineException):
    """Доступ запрещен (нет прав на ресурс)"""
    def __init__(self, message: str = "Доступ запрещен. У вас нет прав на этот ресурс в Redmine", details: dict = None):
        super().__init__(message, status_code=403, details=details)


class RedmineNotFoundError(RedmineException):
    """Ресурс не найден в Redmine"""
    def __init__(self, message: str = "Ресурс не найден в Redmine", resource_type: str = None, resource_id: int = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, status_code=404, details=details)


class RedmineValidationError(RedmineException):
    """Ошибка валидации данных в Redmine (неверные параметры)"""
    def __init__(self, message: str = "Неверные параметры запроса к Redmine", details: dict = None):
        super().__init__(message, status_code=422, details=details)


class RedmineServerError(RedmineException):
    """Внутренняя ошибка Redmine сервера"""
    def __init__(self, message: str = "Внутренняя ошибка Redmine сервера", status_code: int = 500, details: dict = None):
        super().__init__(message, status_code=status_code, details=details)


class RedmineRateLimitError(RedmineException):
    """Превышен лимит запросов к Redmine"""
    def __init__(self, message: str = "Превышен лимит запросов к Redmine. Попробуйте позже", details: dict = None):
        super().__init__(message, status_code=429, details=details)
