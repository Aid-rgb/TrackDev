import os
from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Загружаем допустимые API ключи из переменных окружения
# Формат: ALLOWED_API_KEYS=key1,key2,key3
# ИЛИ можно хранить в формате user1:key1,user2:key2 для идентификации пользователей
ALLOWED_API_KEYS = os.getenv("ALLOWED_API_KEYS", "").split(",") if os.getenv("ALLOWED_API_KEYS") else []
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def validate_api_key(api_key: Optional[str] = None) -> bool:
    """
    Проверяет валидность API ключа
    """
    if not ALLOWED_API_KEYS:
        logger.warning("No API keys configured, allowing all requests")
        return True
    
    if not api_key:
        return False
    
    # Проверяем, есть ли ключ в списке допустимых
    # Поддерживаем формат "username:redmine_key" или просто "key"
    for allowed in ALLOWED_API_KEYS:
        if ":" in allowed:
            # Формат username:redmine_key
            _, redmine_key = allowed.split(":", 1)
            if api_key == redmine_key or api_key == allowed:
                return True
        else:
            # Простой формат - просто ключ
            if api_key == allowed:
                return True
    
    return False


async def api_key_middleware(request: Request, call_next):
    """
    Middleware для проверки API ключа
    """
    # Пути, которые не требуют авторизации
    public_paths = ["/", "/health", "/docs", "/openapi.json", "/redoc", "/dashboard", "/old-dashboard"]
    
    # Разрешаем статические файлы (assets, static) без проверки ключа
    path = request.url.path
    if path in public_paths or path.startswith("/assets/") or path.startswith("/static/"):
        return await call_next(request)
    
    # Получаем API ключ из заголовка
    api_key = request.headers.get(API_KEY_NAME)
    
    # Проверяем ключ
    if not await validate_api_key(api_key):
        logger.warning(f"Invalid or missing API key for path: {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Добавляем API ключ в состояние запроса для дальнейшего использования
    request.state.api_key = api_key
    
    return await call_next(request)


def get_redmine_key_from_api_key(api_key: Optional[str]) -> str:
    """
    Извлекает Redmine API ключ из переданного API ключа.
    Если API ключ в формате "username:redmine_key", возвращает redmine_key.
    Иначе возвращает сам ключ (предполагаем, что это Redmine API ключ).
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Если ключ содержит двоеточие, извлекаем Redmine ключ
    if ":" in api_key:
        _, redmine_key = api_key.split(":", 1)
        return redmine_key
    
    # Иначе предполагаем, что это сам Redmine API ключ
    return api_key


def get_api_key_scheme():
    """
    Возвращает схему безопасности для документации
    """
    return api_key_header