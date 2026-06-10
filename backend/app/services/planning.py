"""
Метрики планирования и управления (асинхронные функции)
"""
from typing import Optional, Dict, Any
from collections import defaultdict
from .base import get_issues, get_time_entries, get_period_range
from . import workload as workload_module
import logging

logger = logging.getLogger(__name__)


async def get_time_tracking_stats(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "month"
) -> Dict[str, Any]:
    """Статистика по учету времени"""
    start_date, end_date = get_period_range(period)
    
    params = {
        "from": start_date.strftime('%Y-%m-%d'),
        "to": end_date.strftime('%Y-%m-%d'),
    }
    if project_id:
        params["project_id"] = project_id
    
    time_entries = await get_time_entries(redmine_key, params, use_cache=True)
    
    # Агрегация данных
    total_hours = 0
    by_user = defaultdict(float)
    by_activity = defaultdict(float)
    user_detailed = defaultdict(lambda: {"total": 0, "activities": defaultdict(float)})
    issue_time_map = defaultdict(float)
    issues_with_time = set()
    
    for entry in time_entries:
        hours = entry.get("hours", 0)
        total_hours += hours
        
        user = entry.get("user", {}).get("name", "Unknown")
        by_user[user] += hours
        
        activity = entry.get("activity", {}).get("name", "Unknown")
        by_activity[activity] += hours
        
        user_detailed[user]["total"] += hours
        user_detailed[user]["activities"][activity] += hours
        
        issue_id = entry.get("issue", {}).get("id")
        if issue_id:
            issues_with_time.add(issue_id)
            issue_time_map[issue_id] += hours
            
    # Получаем информацию по трекерам и приоритетам задач
    by_tracker = defaultdict(float)
    by_priority = defaultdict(float)
    
    if issues_with_time:
        # Разбиваем на чанки по 100 ID, чтобы не превысить длину URL
        issue_ids_list = list(issues_with_time)
        chunk_size = 100
        for i in range(0, len(issue_ids_list), chunk_size):
            chunk = issue_ids_list[i:i + chunk_size]
            issues_params = {"issue_id": ",".join(map(str, chunk)), "status_id": "*"}
            chunk_issues = await get_issues(redmine_key, issues_params, use_cache=True)
            for issue in chunk_issues:
                issue_id = issue.get("id")
                tracker_name = issue.get("tracker", {}).get("name", "Unknown")
                priority_name = issue.get("priority", {}).get("name", "Unknown")
                
                time_spent = issue_time_map.get(issue_id, 0)
                by_tracker[tracker_name] += time_spent
                by_priority[priority_name] += time_spent
    
    # Средние значения
    days_in_period = (end_date - start_date).days or 1
    avg_hours_per_day = total_hours / days_in_period
    
    # Топ пользователей
    top_users = sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Преобразуем user_detailed в удобный список для фронтенда
    user_detailed_list = []
    for user_name, data in sorted(user_detailed.items(), key=lambda x: x[1]["total"], reverse=True):
        user_data = {"name": user_name, "total": round(data["total"], 1)}
        for act, h in data["activities"].items():
            user_data[act] = round(h, 1)
        user_detailed_list.append(user_data)
    
    return {
        "total_hours": round(total_hours, 1),
        "total_entries": len(time_entries),
        "issues_tracked": len(issues_with_time),
        "avg_hours_per_day": round(avg_hours_per_day, 1),
        "by_user": dict(by_user),
        "by_activity": dict(by_activity),
        "by_tracker": dict(by_tracker),
        "by_priority": dict(by_priority),  # Новое поле
        "user_detailed": user_detailed_list,
        "top_users": [{"name": name, "hours": round(hours, 1)} for name, hours in top_users],
        "period": period
    }


async def get_workload_distribution(
    redmine_key: str,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """Распределение нагрузки по пользователям"""
    params = {"status_id": "open"}
    if project_id:
        params["project_id"] = project_id
    
    open_issues = await get_issues(redmine_key, params, use_cache=True)
    
    by_user = defaultdict(lambda: {"count": 0, "estimated_hours": 0, "tasks": []})
    unassigned = 0
    
    for issue in open_issues:
        assigned_to = issue.get("assigned_to")
        if assigned_to:
            user_name = assigned_to.get("name", "Unknown")
            by_user[user_name]["count"] += 1
            
            estimated = issue.get("estimated_hours", 0) or 0
            by_user[user_name]["estimated_hours"] += estimated
            
            by_user[user_name]["tasks"].append({
                "id": issue.get("id"),
                "subject": issue.get("subject", "")[:50],
                "priority": issue.get("priority", {}).get("name", ""),
                "estimated_hours": estimated
            })
        else:
            unassigned += 1
    
    # Сортировка по нагрузке
    workload = []
    for user, data in by_user.items():
        workload.append({
            "user": user,
            "active_tasks": data["count"],
            "estimated_hours": round(data["estimated_hours"], 1),
            "avg_hours_per_task": round(data["estimated_hours"] / data["count"], 1) if data["count"] > 0 else 0,
            "top_tasks": data["tasks"][:5]
        })
    
    workload.sort(key=lambda x: x["active_tasks"], reverse=True)
    
    return {
        "total_users": len(by_user),
        "unassigned_tasks": unassigned,
        "workload": workload[:20],
        "avg_tasks_per_user": round(sum(u["active_tasks"] for u in workload) / len(workload), 1) if workload else 0
    }


async def get_estimation_accuracy(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "month"
) -> Dict[str, Any]:
    """Точность оценки трудозатрат"""
    start_date, end_date = get_period_range(period)
    
    # Закрытые задачи с оценкой
    params = {
        "closed_on": f">={start_date.strftime('%Y-%m-%d')}",
        "status_id": "closed",
    }
    if project_id:
        params["project_id"] = project_id
    
    # Параметры для time entries
    time_params = {
        "from": start_date.strftime('%Y-%m-%d'),
        "to": end_date.strftime('%Y-%m-%d'),
    }
    if project_id:
        time_params["project_id"] = project_id
    
    # Параллельные запросы
    import asyncio
    closed_issues, time_entries = await asyncio.gather(
        get_issues(redmine_key, params, use_cache=True),
        get_time_entries(redmine_key, time_params, use_cache=True)
    )
    
    # Агрегируем время по задачам
    actual_hours_by_issue = defaultdict(float)
    for entry in time_entries:
        issue_id = entry.get("issue", {}).get("id")
        if issue_id:
            actual_hours_by_issue[issue_id] += entry.get("hours", 0)
    
    # Анализ точности
    deviations = []
    underestimated = 0
    overestimated = 0
    accurate = 0
    details = []
    
    for issue in closed_issues:
        estimated = issue.get("estimated_hours")
        issue_id = issue.get("id")
        
        if estimated and estimated > 0 and issue_id in actual_hours_by_issue:
            actual = actual_hours_by_issue[issue_id]
            
            if actual > 0:
                deviation_percent = ((actual - estimated) / estimated) * 100
                deviations.append(abs(deviation_percent))
                
                if deviation_percent > 20:
                    underestimated += 1
                    category = "Недооценено"
                elif deviation_percent < -20:
                    overestimated += 1
                    category = "Переоценено"
                else:
                    accurate += 1
                    category = "Точно"
                
                details.append({
                    "id": issue_id,
                    "subject": issue.get("subject", "")[:50],
                    "estimated": estimated,
                    "actual": round(actual, 1),
                    "deviation": round(deviation_percent, 1),
                    "category": category
                })
    
    avg_deviation = sum(deviations) / len(deviations) if deviations else 0
    details.sort(key=lambda x: abs(x["deviation"]), reverse=True)
    
    return {
        "avg_deviation_percent": round(avg_deviation, 1),
        "underestimated": underestimated,
        "overestimated": overestimated,
        "accurate": accurate,
        "total_analyzed": len(deviations),
        "accuracy_rate": round(accurate / len(deviations) * 100, 1) if deviations else 0,
        "worst_estimates": details[:10],
        "period": period
    }


async def get_unassigned_tasks(redmine_key: str, project_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Задачи без исполнителя
    Использует fallback, если сервер не поддерживает фильтр assigned_to_id=!*
    """
    params = {
        "status_id": "open",
        "assigned_to_id": "!*",  # Недокументированный фильтр
    }
    if project_id:
        params["project_id"] = project_id
    
    import asyncio
    from app.core.exceptions import RedmineValidationError
    
    # Пытаемся использовать server-side фильтр
    try:
        unassigned, backlog = await asyncio.gather(
            get_issues(redmine_key, params, use_cache=True),
            workload_module.get_backlog(redmine_key, project_id)
        )
        
        logger.info("Unassigned tasks fetched (server-side filter)", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "count": len(unassigned)
        })
        
    except (RedmineValidationError, Exception) as e:
        # Fallback: получаем все открытые задачи и фильтруем client-side
        logger.warning("Server-side filter failed, using client-side filtering", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "error": str(e),
            "filter": "assigned_to_id=!*"
        })
        
        fallback_params = {"status_id": "open"}
        if project_id:
            fallback_params["project_id"] = project_id
        
        all_open, backlog = await asyncio.gather(
            get_issues(redmine_key, fallback_params, use_cache=True),
            workload_module.get_backlog(redmine_key, project_id)
        )
        
        # Client-side фильтрация: оставляем только задачи без assigned_to
        unassigned = [issue for issue in all_open if not issue.get("assigned_to")]
        
        logger.info("Unassigned tasks fetched (client-side filter)", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "count": len(unassigned),
            "total_open": len(all_open)
        })
    
    by_priority = defaultdict(int)
    for issue in unassigned:
        priority = issue.get("priority", {}).get("name", "Unknown")
        by_priority[priority] += 1
    
    percent = (len(unassigned) / backlog["total"] * 100) if backlog["total"] > 0 else 0
    
    return {
        "total": len(unassigned),
        "by_priority": dict(by_priority),
        "percent_of_backlog": round(percent, 1)
    }


async def get_tasks_without_due_date(
    redmine_key: str,
    project_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Задачи без срока выполнения
    Использует fallback, если сервер не поддерживает фильтр due_date=!*
    """
    params = {
        "status_id": "open",
        "due_date": "!*",  # Недокументированный фильтр
    }
    if project_id:
        params["project_id"] = project_id
    
    import asyncio
    from app.core.exceptions import RedmineValidationError
    
    # Пытаемся использовать server-side фильтр
    try:
        without_due, backlog = await asyncio.gather(
            get_issues(redmine_key, params, use_cache=True),
            workload_module.get_backlog(redmine_key, project_id)
        )
        
        logger.info("Tasks without due date fetched (server-side filter)", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "count": len(without_due)
        })
        
    except (RedmineValidationError, Exception) as e:
        # Fallback: получаем все открытые задачи и фильтруем client-side
        logger.warning("Server-side filter failed, using client-side filtering", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "error": str(e),
            "filter": "due_date=!*"
        })
        
        fallback_params = {"status_id": "open"}
        if project_id:
            fallback_params["project_id"] = project_id
        
        all_open, backlog = await asyncio.gather(
            get_issues(redmine_key, fallback_params, use_cache=True),
            workload_module.get_backlog(redmine_key, project_id)
        )
        
        # Client-side фильтрация: оставляем только задачи без due_date
        without_due = [issue for issue in all_open if not issue.get("due_date")]
        
        logger.info("Tasks without due date fetched (client-side filter)", extra={
            "user_id": redmine_key[:8] if redmine_key else "unknown",
            "count": len(without_due),
            "total_open": len(all_open)
        })
    
    percent = (len(without_due) / backlog["total"] * 100) if backlog["total"] > 0 else 0
    
    return {
        "total": len(without_due),
        "percent_of_backlog": round(percent, 1)
    }
