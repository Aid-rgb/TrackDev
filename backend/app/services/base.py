"""
Базовые функции для метрик Redmine (асинхронные, без классов)
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
import logging
from app.integrations.redmine_client import request

logger = logging.getLogger(__name__)

# In-memory кэш (простой словарь)
_cache: Dict[str, Tuple[Any, datetime]] = {}


def _get_cache_key(endpoint: str, params: dict, redmine_key: str) -> str:
    """Генерирует ключ кэша для запроса"""
    # Добавляем первые 8 символов ключа для разделения кэша по пользователям
    key_prefix = redmine_key[:8] if redmine_key else "default"
    param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{key_prefix}:{endpoint}?{param_str}"


def _get_from_cache(cache_key: str, ttl: int = 300) -> Optional[Any]:
    """Получает данные из in-memory кэша (TTL в секундах)"""
    if cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        age_seconds = (datetime.now() - timestamp).total_seconds()
        if age_seconds < ttl:
            logger.debug(f"Cache HIT: {cache_key}")
            return cached_data
        else:
            # Кэш истек
            del _cache[cache_key]
    return None


def _set_cache(cache_key: str, data: Any):
    """Сохраняет данные в in-memory кэш"""
    _cache[cache_key] = (data, datetime.now())
    
    # Ограничиваем размер кэша (100 записей)
    if len(_cache) > 100:
        # Удаляем самые старые записи
        oldest_keys = sorted(_cache.items(), key=lambda x: x[1][1])[:20]
        for key, _ in oldest_keys:
            del _cache[key]
        logger.debug("Cache cleanup performed", extra={
            "removed_entries": 20,
            "remaining_entries": len(_cache)
        })


def clear_cache():
    """Очищает весь кэш"""
    cache_size = len(_cache)
    _cache.clear()
    logger.info("Cache cleared", extra={
        "cleared_entries": cache_size
    })


async def get_issues(
    redmine_key: str,
    params: Optional[dict] = None,
    max_results: int = 1000,
    use_cache: bool = True
) -> List[dict]:
    """
    Асинхронное получение списка задач с пагинацией и кэшированием
    
    Args:
        redmine_key: Redmine API ключ
        params: Параметры запроса
        max_results: Максимальное количество результатов
        use_cache: Использовать кэш
    
    Returns:
        List[dict]: Список задач
    """
    if params is None:
        params = {}
    
    cache_key = _get_cache_key("issues.json", params, redmine_key)
    user_id = redmine_key[:8] if redmine_key else "unknown"
    
    # Проверяем кэш
    if use_cache:
        cached = _get_from_cache(cache_key)
        if cached is not None:
            logger.debug("Issues fetched from cache", extra={
                "user_id": user_id,
                "count": len(cached),
                "params": params
            })
            return cached
    
    all_issues = []
    limit = 100  # Оптимальный размер страницы
    
    default_params = {"limit": limit, "offset": 0}
    default_params.update(params)
    
    try:
        # Первый запрос для получения total_count
        default_params["offset"] = 0
        data = await request("GET", "issues.json", redmine_key=redmine_key, params=default_params)
        total_count = data.get("total_count", 0)
        issues = data.get("issues", [])
        all_issues.extend(issues)
        
        # Ограничиваем максимальное количество результатов
        actual_total = min(total_count, max_results)
        
        if len(all_issues) >= actual_total:
            _set_cache(cache_key, all_issues)
            return all_issues
        
        # Параллельные запросы для оставшихся страниц
        import asyncio
        
        remaining_pages = []
        offset = limit
        while offset < actual_total:
            remaining_pages.append(offset)
            offset += limit
        
        # Выполняем параллельно (батчами по 5)
        for i in range(0, len(remaining_pages), 5):
            batch = remaining_pages[i:i+5]
            
            async def fetch_page(page_offset: int):
                page_params = default_params.copy()
                page_params["offset"] = page_offset
                try:
                    page_data = await request("GET", "issues.json", redmine_key=redmine_key, params=page_params)
                    return page_data.get("issues", [])
                except Exception as e:
                    logger.error(f"Error fetching page at offset {page_offset}: {e}")
                    return []
            
            # Запускаем батч параллельно
            batch_results = await asyncio.gather(*[fetch_page(offset) for offset in batch])
            
            for result in batch_results:
                all_issues.extend(result)
            
            if len(all_issues) >= actual_total:
                break
        
        # Сохраняем в кэш
        _set_cache(cache_key, all_issues)
        
        logger.info("Issues fetched successfully", extra={
            "user_id": user_id,
            "count": len(all_issues),
            "total_count": total_count,
            "cached": use_cache,
            "params": params
        })
        
    except Exception as e:
        logger.error("Error fetching issues", extra={
            "user_id": user_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "params": params
        })
    
    return all_issues


async def get_time_entries(
    redmine_key: str,
    params: Optional[dict] = None,
    max_results: int = 1000,
    use_cache: bool = True
) -> List[dict]:
    """
    Асинхронное получение записей времени с кэшированием
    
    Args:
        redmine_key: Redmine API ключ
        params: Параметры запроса
        max_results: Максимальное количество результатов
        use_cache: Использовать кэш
    
    Returns:
        List[dict]: Список записей времени
    """
    if params is None:
        params = {}
    
    cache_key = _get_cache_key("time_entries.json", params, redmine_key)
    user_id = redmine_key[:8] if redmine_key else "unknown"
    
    # Проверяем кэш
    if use_cache:
        cached = _get_from_cache(cache_key)
        if cached is not None:
            logger.debug("Time entries fetched from cache", extra={
                "user_id": user_id,
                "count": len(cached),
                "params": params
            })
            return cached
    
    all_entries = []
    limit = 100
    
    default_params = {"limit": limit, "offset": 0}
    default_params.update(params)
    
    try:
        # Первый запрос
        default_params["offset"] = 0
        data = await request("GET", "time_entries.json", redmine_key=redmine_key, params=default_params)
        total_count = data.get("total_count", 0)
        entries = data.get("time_entries", [])
        all_entries.extend(entries)
        
        actual_total = min(total_count, max_results)
        
        if len(all_entries) >= actual_total:
            _set_cache(cache_key, all_entries)
            return all_entries
        
        # Параллельные запросы
        import asyncio
        
        remaining_pages = []
        offset = limit
        while offset < actual_total:
            remaining_pages.append(offset)
            offset += limit
        
        for i in range(0, len(remaining_pages), 5):
            batch = remaining_pages[i:i+5]
            
            async def fetch_page(page_offset: int):
                page_params = default_params.copy()
                page_params["offset"] = page_offset
                try:
                    page_data = await request("GET", "time_entries.json", redmine_key=redmine_key, params=page_params)
                    return page_data.get("time_entries", [])
                except Exception as e:
                    logger.error(f"Error fetching time entries at offset {page_offset}: {e}")
                    return []
            
            batch_results = await asyncio.gather(*[fetch_page(offset) for offset in batch])
            
            for result in batch_results:
                all_entries.extend(result)
            
            if len(all_entries) >= actual_total:
                break
        
        # Сохраняем в кэш
        _set_cache(cache_key, all_entries)
        
        logger.info("Time entries fetched successfully", extra={
            "user_id": user_id,
            "count": len(all_entries),
            "total_count": total_count,
            "cached": use_cache,
            "params": params
        })
        
    except Exception as e:
        logger.error("Error fetching time entries", extra={
            "user_id": user_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "params": params
        })
    
    return all_entries


@lru_cache(maxsize=128)
def parse_date(date_str: str) -> Optional[datetime]:
    """Парсинг даты из строки, возвращает naive datetime (с кэшированием)"""
    if not date_str:
        return None
    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        else:
            return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception as e:
        logger.error(f"Error parsing date {date_str}: {e}")
        return None


def get_period_range(period: str = "week") -> Tuple[datetime, datetime]:
    """Получение диапазона дат для периода"""
    now = datetime.now()
    
    if "|" in period:
        try:
            start_str, end_str = period.split("|")
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.strptime(end_str, "%Y-%m-%d")
            # Если end - это конец дня, то можно добавить время или просто оставить как есть
            return start, end
        except ValueError as e:
            logger.error(f"Error parsing custom period {period}: {e}")
            pass

    if period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    elif period == "quarter":
        start = now - timedelta(days=90)
    elif period == "year":
        start = now - timedelta(days=365)
    else:
        start = now - timedelta(days=30)  # Default to month
    
    return start, now
