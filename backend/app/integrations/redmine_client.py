"""
Базовый HTTP клиент для работы с Redmine API
Асинхронная версия с httpx
"""
import httpx
from typing import Dict, Any, Optional
from app.core.config import REDMINE_URL
from app.core.exceptions import (
    RedmineConnectionError,
    RedmineTimeoutError,
    RedmineAuthError,
    RedmineForbiddenError,
    RedmineNotFoundError,
    RedmineValidationError,
    RedmineServerError,
    RedmineRateLimitError
)
import logging

logger = logging.getLogger(__name__)

# HTTP клиент для повторного использования соединений
_client: Optional[httpx.AsyncClient] = None


async def get_redmine_client() -> httpx.AsyncClient:
    """Получает или создает HTTP клиент"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        logger.info("HTTP client created", extra={
            "timeout": 30.0,
            "max_connections": 100
        })
    return _client


async def close_redmine_client():
    """Закрывает HTTP клиент"""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("HTTP client closed")


class RedmineClient:
    """Клиент для работы с Redmine API"""
    
    @staticmethod
    async def request(
        method: str,
        endpoint: str,
        redmine_key: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Асинхронный HTTP запрос к Redmine API
        
        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: API endpoint (например, "issues.json")
            redmine_key: Redmine API ключ
            params: Query параметры
            data: Данные для POST/PUT запросов
        
        Returns:
            Dict: Response data
        
        Raises:
            Exception: При ошибке запроса
        """
        url = f"{REDMINE_URL}/{endpoint}"
        headers = {"X-Redmine-API-Key": redmine_key}
        
        client = await get_redmine_client()
        
        logger.debug("Redmine API request", extra={
            "method": method,
            "endpoint": endpoint,
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "params": params
        })
        
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            )
            response.raise_for_status()
            
            logger.debug("Redmine API response success", extra={
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "user_id": redmine_key[:8] if redmine_key else "unknown"
            })
            
            return response.json()
        except httpx.TimeoutException as e:
            logger.error("Redmine API timeout", extra={
                "method": method,
                "endpoint": endpoint,
                "timeout": 30,
                "user_id": redmine_key[:8] if redmine_key else "unknown"
            })
            raise RedmineTimeoutError(
                details={"endpoint": endpoint, "method": method}
            )
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            
            logger.error("Redmine API HTTP error", extra={
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "response_text": e.response.text[:200],
                "user_id": redmine_key[:8] if redmine_key else "unknown"
            })
            
            # Детальная обработка HTTP статусов
            if status_code == 401:
                raise RedmineAuthError(
                    details={"endpoint": endpoint}
                )
            elif status_code == 403:
                raise RedmineForbiddenError(
                    message=f"Доступ запрещен к {endpoint}. Проверьте права доступа в Redmine",
                    details={"endpoint": endpoint}
                )
            elif status_code == 404:
                # Пытаемся определить тип ресурса из endpoint
                resource_type = endpoint.split("/")[0].replace(".json", "")
                raise RedmineNotFoundError(
                    message=f"Ресурс {resource_type} не найден в Redmine",
                    resource_type=resource_type,
                    resource_id=None
                )
            elif status_code == 422:
                raise RedmineValidationError(
                    message="Неверные параметры запроса к Redmine",
                    details={"endpoint": endpoint, "params": params, "response": e.response.text[:200]}
                )
            elif status_code == 429:
                raise RedmineRateLimitError(
                    details={"endpoint": endpoint}
                )
            elif status_code >= 500:
                raise RedmineServerError(
                    message=f"Внутренняя ошибка Redmine сервера (код {status_code})",
                    status_code=status_code,
                    details={"endpoint": endpoint, "response": e.response.text[:200]}
                )
            else:
                raise RedmineServerError(
                    message=f"Ошибка Redmine API: HTTP {status_code}",
                    status_code=status_code,
                    details={"endpoint": endpoint}
                )
        except httpx.ConnectError as e:
            logger.error("Redmine connection error", extra={
                "method": method,
                "endpoint": endpoint,
                "error": str(e),
                "redmine_url": REDMINE_URL,
                "user_id": redmine_key[:8] if redmine_key else "unknown"
            })
            raise RedmineConnectionError(
                message=f"Не удалось подключиться к Redmine серверу ({REDMINE_URL}). Проверьте доступность сервера",
                details={"redmine_url": REDMINE_URL, "error": str(e)}
            )
        except httpx.RequestError as e:
            logger.error("Redmine API request error", extra={
                "method": method,
                "endpoint": endpoint,
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": redmine_key[:8] if redmine_key else "unknown"
            })
            raise RedmineConnectionError(
                message=f"Ошибка запроса к Redmine: {str(e)}",
                details={"endpoint": endpoint, "error": str(e), "error_type": type(e).__name__}
            )
        except Exception as e:
            logger.error("Redmine API unexpected error", extra={
                "method": method,
                "endpoint": endpoint,
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": redmine_key[:8] if redmine_key else "unknown"
            })
            raise RedmineServerError(
                message=f"Неожиданная ошибка при работе с Redmine: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )


async def get_trackers(redmine_key: str) -> Dict[str, int]:
    """
    Получает список трекеров (Bug, Feature, Task и т.д.)
    
    Returns:
        Dict[str, int]: Mapping tracker_name → tracker_id
    """
    try:
        data = await request("GET", "trackers.json", redmine_key=redmine_key)
        trackers = data.get("trackers", [])
        
        tracker_map = {}
        for tracker in trackers:
            name = tracker.get("name", "").lower()
            tracker_id = tracker.get("id")
            if name and tracker_id:
                tracker_map[name] = tracker_id
        
        logger.info("Trackers fetched", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "count": len(tracker_map),
            "trackers": list(tracker_map.keys())
        })
        
        return tracker_map
    except Exception as e:
        logger.error("Error fetching trackers", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "error": str(e)
        })
        return {}


async def get_issue_statuses(redmine_key: str) -> Dict[str, list]:
    """
    Получает статусы задач
    
    Returns:
        Dict with 'open' and 'closed' status IDs
    """
    try:
        data = await request("GET", "issue_statuses.json", redmine_key=redmine_key)
        statuses = data.get("issue_statuses", [])
        
        open_statuses = []
        closed_statuses = []
        
        for status in statuses:
            status_id = status.get("id")
            is_closed = status.get("is_closed", False)
            
            if status_id:
                if is_closed:
                    closed_statuses.append(str(status_id))
                else:
                    open_statuses.append(str(status_id))
        
        logger.info("Issue statuses fetched", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "open_count": len(open_statuses),
            "closed_count": len(closed_statuses)
        })
        
        return {
            "open": open_statuses,
            "closed": closed_statuses
        }
    except Exception as e:
        logger.error("Error fetching issue statuses", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "error": str(e)
        })
        # Fallback to common status IDs
        return {
            "open": ["1", "2", "4"],  # New, In Progress, Feedback
            "closed": ["5", "6"]  # Closed, Rejected
        }


# Backward compatibility
request = RedmineClient.request
