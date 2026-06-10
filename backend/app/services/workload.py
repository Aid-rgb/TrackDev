"""
Метрики нагрузки и объема работы (асинхронные функции)
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from .base import get_issues, get_period_range, parse_date


async def get_backlog(redmine_key: str, project_id: Optional[int] = None) -> Dict[str, Any]:
    """Бэклог: количество всех открытых задач"""
    params = {"status_id": "open"}
    if project_id:
        params["project_id"] = project_id
    
    issues = await get_issues(redmine_key, params, use_cache=True)
    
    by_priority = defaultdict(int)
    by_tracker = defaultdict(int)
    by_status = defaultdict(int)
    
    for issue in issues:
        priority = issue.get("priority", {}).get("name", "Unknown")
        tracker = issue.get("tracker", {}).get("name", "Unknown")
        status = issue.get("status", {}).get("name", "Unknown")
        
        by_priority[priority] += 1
        by_tracker[tracker] += 1
        by_status[status] += 1
    
    return {
        "total": len(issues),
        "by_priority": dict(by_priority),
        "by_tracker": dict(by_tracker),
        "by_status": dict(by_status)
    }


async def get_backlog_change(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "week"
) -> Dict[str, Any]:
    """Изменение бэклога: сравнение новых и закрытых задач за период"""
    start_date, end_date = get_period_range(period)
    start_str = start_date.strftime('%Y-%m-%d')
    
    # Новые задачи за период
    new_params = {"created_on": f">={start_str}"}
    if project_id:
        new_params["project_id"] = project_id
    
    # Закрытые задачи за период
    closed_params = {
        "closed_on": f">={start_str}",
        "status_id": "closed",
    }
    if project_id:
        closed_params["project_id"] = project_id
    
    # Параллельные запросы
    import asyncio
    new_issues, closed_issues = await asyncio.gather(
        get_issues(redmine_key, new_params, use_cache=True),
        get_issues(redmine_key, closed_params, use_cache=True)
    )
    
    new_count = len(new_issues)
    closed_count = len(closed_issues)
    change = new_count - closed_count
    
    # Определение тренда
    if change > 5:
        trend = "increasing"
    elif change < -5:
        trend = "decreasing"
    else:
        trend = "stable"
    
    return {
        "new_issues": new_count,
        "closed_issues": closed_count,
        "change": change,
        "trend": trend,
        "period": period
    }


async def get_inflow_ratio(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "week"
) -> Dict[str, Any]:
    """Коэффициент притока задач: отношение новых задач к выполненным"""
    change_data = await get_backlog_change(redmine_key, project_id, period)
    new_count = change_data["new_issues"]
    closed_count = change_data["closed_issues"]
    
    if closed_count == 0:
        ratio = new_count if new_count > 0 else 0
    else:
        ratio = new_count / closed_count
    
    # Интерпретация
    if ratio < 0.8:
        interpretation = "Объем работ сокращается"
    elif ratio <= 1.2:
        interpretation = "Стабильная ситуация"
    else:
        interpretation = "Объем работ растет"
    
    return {
        "ratio": round(ratio, 2),
        "interpretation": interpretation,
        "new_count": new_count,
        "closed_count": closed_count,
        "period": period
    }


async def get_velocity(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "week"
) -> Dict[str, Any]:
    """Скорость выполнения задач (Velocity)"""
    start_date, end_date = get_period_range(period)
    
    params = {
        "closed_on": f">={start_date.strftime('%Y-%m-%d')}",
        "status_id": "closed",
    }
    if project_id:
        params["project_id"] = project_id
    
    closed_issues = await get_issues(redmine_key, params, use_cache=True)
    
    # Группировка по неделям
    by_week = defaultdict(int)
    for issue in closed_issues:
        closed_on_str = issue.get("closed_on")
        if closed_on_str:
            closed_on = parse_date(closed_on_str)
            if closed_on:
                week_start = closed_on - timedelta(days=closed_on.weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                by_week[week_key] += 1
    
    return {
        "closed_count": len(closed_issues),
        "period": period,
        "by_week": dict(sorted(by_week.items()))
    }


async def get_old_tasks(redmine_key: str, project_id: Optional[int] = None) -> Dict[str, Any]:
    """Старые задачи (старше 30, 90 и 180 дней)"""
    now = datetime.now()
    days_30_ago = now - timedelta(days=30)
    days_90_ago = now - timedelta(days=90)
    days_180_ago = now - timedelta(days=180)
    
    params = {"status_id": "open"}
    if project_id:
        params["project_id"] = project_id
    
    open_issues = await get_issues(redmine_key, params, use_cache=True)
    
    older_30 = 0
    older_90 = 0
    older_180 = 0
    
    for issue in open_issues:
        created_str = issue.get("created_on")
        if created_str:
            created = parse_date(created_str)
            if created:
                if created < days_180_ago:
                    older_180 += 1
                if created < days_90_ago:
                    older_90 += 1
                if created < days_30_ago:
                    older_30 += 1
    
    return {
        "older_30_days": older_30,
        "older_90_days": older_90,
        "older_180_days": older_180,
        "total_open": len(open_issues)
    }
