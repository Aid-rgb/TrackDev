"""
Метрики качества (асинхронные функции)
"""
from typing import Optional, Dict, Any
from app.integrations.redmine_client import request, get_trackers, get_issue_statuses
from .base import get_issues, get_period_range
import logging
import asyncio

logger = logging.getLogger(__name__)

# Кэш для трекеров и статусов (живет в памяти процесса)
_trackers_cache: Dict[str, Dict[str, int]] = {}
_statuses_cache: Dict[str, Dict[str, list]] = {}


async def _get_bug_tracker_ids(redmine_key: str) -> list:
    """
    Получает ID трекеров для багов (с кэшированием)
    
    Returns:
        list: Список ID трекеров, содержащих 'bug', 'ошибка', 'дефект'
    """
    cache_key = redmine_key[:8] if redmine_key else "default"
    
    if cache_key in _trackers_cache:
        trackers = _trackers_cache[cache_key]
    else:
        trackers = await get_trackers(redmine_key)
        _trackers_cache[cache_key] = trackers
    
    # Ищем трекеры, содержащие ключевые слова
    bug_keywords = ["bug", "ошибка", "дефект", "error", "defect"]
    bug_ids = []
    
    for tracker_name, tracker_id in trackers.items():
        if any(keyword in tracker_name for keyword in bug_keywords):
            bug_ids.append(str(tracker_id))
    
    if not bug_ids:
        logger.warning("No bug trackers found, will use client-side filtering", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "available_trackers": list(trackers.keys())
        })
    
    return bug_ids


async def _get_closed_status_ids(redmine_key: str) -> list:
    """
    Получает ID закрытых статусов (с кэшированием)
    
    Returns:
        list: Список ID закрытых статусов
    """
    cache_key = redmine_key[:8] if redmine_key else "default"
    
    if cache_key in _statuses_cache:
        statuses = _statuses_cache[cache_key]
    else:
        statuses = await get_issue_statuses(redmine_key)
        _statuses_cache[cache_key] = statuses
    
    return statuses.get("closed", ["5", "6"])


async def get_bug_rate(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "month"
) -> Dict[str, Any]:
    """Доля ошибок (Bug Rate) - оптимизированная версия"""
    start_date, end_date = get_period_range(period)
    
    # Получаем ID трекеров для багов
    bug_tracker_ids = await _get_bug_tracker_ids(redmine_key)
    
    params = {
        "created_on": f">={start_date.strftime('%Y-%m-%d')}",
        "limit": 1000
    }
    if project_id:
        params["project_id"] = project_id
    
    # Параллельные запросы: все задачи и только баги
    if bug_tracker_ids:
        # Server-side фильтрация багов
        bug_params = params.copy()
        bug_params["tracker_id"] = ",".join(bug_tracker_ids)
        
        all_issues, bug_issues = await asyncio.gather(
            get_issues(redmine_key, params, use_cache=True),
            get_issues(redmine_key, bug_params, use_cache=True)
        )
        
        bug_count = len(bug_issues)
        logger.info("Bug rate calculated (server-side filtering)", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "bug_count": bug_count,
            "total_count": len(all_issues),
            "tracker_ids": bug_tracker_ids
        })
    else:
        # Fallback: client-side фильтрация
        all_issues = await get_issues(redmine_key, params, use_cache=True)
        
        bug_count = 0
        for issue in all_issues:
            tracker = issue.get("tracker", {}).get("name", "").lower()
            if "bug" in tracker or "ошибка" in tracker or "дефект" in tracker:
                bug_count += 1
        
        logger.info("Bug rate calculated (client-side filtering)", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "bug_count": bug_count,
            "total_count": len(all_issues)
        })
    
    total = len(all_issues)
    rate = (bug_count / total * 100) if total > 0 else 0
    
    return {
        "bug_count": bug_count,
        "total_count": total,
        "bug_rate_percent": round(rate, 1),
        "period": period
    }


async def get_bug_metrics(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "month"
) -> Dict[str, Any]:
    """Метрики по ошибкам: новые, закрытые, открытые - оптимизированная версия"""
    start_date, end_date = get_period_range(period)
    
    # Получаем ID трекеров для багов и закрытых статусов
    bug_tracker_ids, closed_status_ids = await asyncio.gather(
        _get_bug_tracker_ids(redmine_key),
        _get_closed_status_ids(redmine_key)
    )
    
    if not bug_tracker_ids:
        # Fallback к старому методу с client-side фильтрацией
        return await _get_bug_metrics_fallback(redmine_key, project_id, period)
    
    # Параметры для разных запросов с server-side фильтрацией багов
    new_params = {
        "created_on": f">={start_date.strftime('%Y-%m-%d')}",
        "tracker_id": ",".join(bug_tracker_ids),
        "limit": 1000
    }
    
    closed_params = {
        "closed_on": f">={start_date.strftime('%Y-%m-%d')}",
        "status_id": ",".join(closed_status_ids),
        "tracker_id": ",".join(bug_tracker_ids),
        "limit": 1000
    }
    
    open_params = {
        "status_id": "open",
        "tracker_id": ",".join(bug_tracker_ids),
        "limit": 1000
    }
    
    if project_id:
        new_params["project_id"] = project_id
        closed_params["project_id"] = project_id
        open_params["project_id"] = project_id
    
    # Параллельные запросы
    new_bugs, closed_bugs, open_bugs = await asyncio.gather(
        get_issues(redmine_key, new_params, use_cache=True),
        get_issues(redmine_key, closed_params, use_cache=True),
        get_issues(redmine_key, open_params, use_cache=True)
    )
    
    logger.info("Bug metrics calculated (server-side filtering)", extra={
        "user_id": redmine_key[:8] if redmine_key else "unknown",
        "new_bugs": len(new_bugs),
        "closed_bugs": len(closed_bugs),
        "open_bugs": len(open_bugs),
        "tracker_ids": bug_tracker_ids
    })
    
    return {
        "new_bugs": len(new_bugs),
        "closed_bugs": len(closed_bugs),
        "open_bugs": len(open_bugs),
        "period": period
    }


async def _get_bug_metrics_fallback(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "month"
) -> Dict[str, Any]:
    """Fallback метод с client-side фильтрацией"""
    start_date, end_date = get_period_range(period)
    
    new_params = {
        "created_on": f">={start_date.strftime('%Y-%m-%d')}",
        "tracker_id": "*",
        "limit": 1000
    }
    
    closed_params = {
        "closed_on": f">={start_date.strftime('%Y-%m-%d')}",
        "status_id": "closed",
        "limit": 1000
    }
    
    open_params = {
        "status_id": "open",
        "limit": 1000
    }
    
    if project_id:
        new_params["project_id"] = project_id
        closed_params["project_id"] = project_id
        open_params["project_id"] = project_id
    
    new_issues, closed_issues, open_issues = await asyncio.gather(
        get_issues(redmine_key, new_params, use_cache=True),
        get_issues(redmine_key, closed_params, use_cache=True),
        get_issues(redmine_key, open_params, use_cache=True)
    )
    
    # Фильтруем баги client-side
    new_bugs = [i for i in new_issues if "bug" in i.get("tracker", {}).get("name", "").lower()]
    closed_bugs = [i for i in closed_issues if "bug" in i.get("tracker", {}).get("name", "").lower()]
    open_bugs = [i for i in open_issues if "bug" in i.get("tracker", {}).get("name", "").lower()]
    
    logger.warning("Bug metrics calculated (client-side filtering fallback)", extra={
        "user_id": redmine_key[:8] if redmine_key else "unknown",
        "new_bugs": len(new_bugs),
        "closed_bugs": len(closed_bugs),
        "open_bugs": len(open_bugs)
    })
    
    return {
        "new_bugs": len(new_bugs),
        "closed_bugs": len(closed_bugs),
        "open_bugs": len(open_bugs),
        "period": period
    }


async def get_bug_fix_ratio(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "month"
) -> Dict[str, Any]:
    """Коэффициент устранения ошибок"""
    bug_metrics = await get_bug_metrics(redmine_key, project_id, period)
    
    new_bugs = bug_metrics["new_bugs"]
    closed_bugs = bug_metrics["closed_bugs"]
    
    if new_bugs == 0:
        ratio = closed_bugs if closed_bugs > 0 else 1.0
    else:
        ratio = closed_bugs / new_bugs
    
    # Интерпретация
    if ratio >= 1.0:
        interpretation = "Команда успевает устранять все ошибки"
    elif ratio >= 0.8:
        interpretation = "Баланс близок к равновесию"
    else:
        interpretation = "Ошибки накапливаются быстрее, чем исправляются"
    
    return {
        "ratio": round(ratio, 2),
        "interpretation": interpretation,
        "new_bugs": new_bugs,
        "closed_bugs": closed_bugs,
        "period": period
    }


async def get_reopened_tasks(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "month"
) -> Dict[str, Any]:
    """
    Переоткрытые задачи - оптимизированная версия с батчингом
    
    Использует Semaphore для ограничения параллельных запросов и уменьшает
    количество анализируемых задач для повышения производительности.
    """
    start_date, end_date = get_period_range(period)
    
    # Получаем ID закрытых статусов
    closed_status_ids = await _get_closed_status_ids(redmine_key)
    
    # Получаем закрытые задачи за период (уменьшено до 50 для производительности)
    params = {
        "closed_on": f">={start_date.strftime('%Y-%m-%d')}",
        "status_id": ",".join(closed_status_ids),
        "limit": 50  # Уменьшено с 200 до 50 для оптимизации
    }
    if project_id:
        params["project_id"] = project_id
    
    closed_issues = await get_issues(redmine_key, params, use_cache=True)
    
    if not closed_issues:
        return {
            "reopened_count": 0,
            "total_analyzed": 0,
            "reopened_percent": 0,
            "period": period
        }
    
    total_analyzed = len(closed_issues)
    reopened_count = 0
    
    # Semaphore для ограничения параллельных запросов (не более 10 одновременно)
    semaphore = asyncio.Semaphore(10)
    
    async def check_issue_reopened(issue: dict) -> bool:
        """Проверяет, была ли задача переоткрыта"""
        issue_id = issue.get("id")
        if not issue_id:
            return False
        
        async with semaphore:
            try:
                # Получаем полную информацию о задаче с журналом изменений
                issue_data = await request(
                    "GET",
                    f"issues/{issue_id}.json",
                    redmine_key=redmine_key,
                    params={"include": "journals"}
                )
                
                journals = issue_data.get("issue", {}).get("journals", [])
                
                # Проверяем изменения статуса
                was_closed = False
                
                for journal in journals:
                    for detail in journal.get("details", []):
                        if detail.get("name") == "status_id":
                            new_value = detail.get("new_value")
                            old_value = detail.get("old_value")
                            
                            # Если статус изменился на "закрыто"
                            if new_value and str(new_value) in closed_status_ids:
                                was_closed = True
                            
                            # Если после закрытия статус изменился обратно (переоткрыта)
                            if was_closed and old_value and str(old_value) in closed_status_ids:
                                return True
                
                return False
                    
            except Exception as e:
                logger.error("Error fetching journal for issue", extra={
                    "user_id": redmine_key[:8] if redmine_key else "unknown",
                    "issue_id": issue_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                return False
    
    # Параллельная проверка всех задач с ограничением по Semaphore
    logger.info("Checking reopened tasks", extra={
        "user_id": redmine_key[:8] if redmine_key else "unknown",
        "total_tasks": total_analyzed,
        "max_concurrent": 10
    })
    
    results = await asyncio.gather(*[check_issue_reopened(issue) for issue in closed_issues])
    reopened_count = sum(results)
    
    reopened_percent = (reopened_count / total_analyzed * 100) if total_analyzed > 0 else 0
    
    logger.info("Reopened tasks analysis complete", extra={
        "user_id": redmine_key[:8] if redmine_key else "unknown",
        "reopened_count": reopened_count,
        "total_analyzed": total_analyzed,
        "reopened_percent": round(reopened_percent, 1)
    })
    
    return {
        "reopened_count": reopened_count,
        "total_analyzed": total_analyzed,
        "reopened_percent": round(reopened_percent, 1),
        "period": period,
        "note": "Анализ ограничен последними 50 задачами для оптимизации производительности"
    }
