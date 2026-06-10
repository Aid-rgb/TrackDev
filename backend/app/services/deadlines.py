"""
Метрики сроков и исполнения (асинхронные функции)
"""
from typing import Optional, Dict, Any
from datetime import datetime, date
from collections import defaultdict
from .base import get_issues, get_period_range, parse_date
import logging

logger = logging.getLogger(__name__)


async def get_on_time_completion(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "month"
) -> Dict[str, Any]:
    """Выполнение задач в срок"""
    start_date, end_date = get_period_range(period)
    
    params = {
        "closed_on": f">={start_date.strftime('%Y-%m-%d')}",
        "status_id": "closed",
    }
    if project_id:
        params["project_id"] = project_id
    
    closed_issues = await get_issues(redmine_key, params, use_cache=True)
    
    on_time = 0
    late = 0
    total_with_due_date = 0
    
    for issue in closed_issues:
        due_date_str = issue.get("due_date")
        closed_on_str = issue.get("closed_on")
        
        if due_date_str and closed_on_str:
            total_with_due_date += 1
            
            try:
                due_dt = datetime.strptime(due_date_str, "%Y-%m-%d")
                closed_dt = parse_date(closed_on_str)
                
                if closed_dt:
                    if closed_dt.date() <= due_dt.date():
                        on_time += 1
                    else:
                        late += 1
            except Exception as e:
                logger.error(f"Error comparing dates: {e}")
                continue
    
    on_time_percent = (on_time / total_with_due_date * 100) if total_with_due_date > 0 else 0
    
    return {
        "total_closed": len(closed_issues),
        "total_with_due_date": total_with_due_date,
        "on_time": on_time,
        "late": late,
        "on_time_percent": round(on_time_percent, 1),
        "period": period
    }


async def get_overdue_tasks(redmine_key: str, project_id: Optional[int] = None) -> Dict[str, Any]:
    """Просроченные задачи"""
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    
    params = {
        "status_id": "open",
        "due_date": f"<={today_str}",
    }
    if project_id:
        params["project_id"] = project_id
    
    overdue_issues = await get_issues(redmine_key, params, use_cache=True)
    
    # Фильтруем только реально просроченные
    truly_overdue = []
    for issue in overdue_issues:
        due_date_str = issue.get("due_date")
        if due_date_str:
            try:
                due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                if due < today:
                    truly_overdue.append(issue)
            except ValueError:
                continue
    overdue_days = []
    tasks_details = []
    by_priority = defaultdict(int)
    
    for issue in truly_overdue:
        due_date_str = issue.get("due_date")
        if due_date_str:
            try:
                due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                days_overdue = (today - due).days
                overdue_days.append(days_overdue)
                
                priority = issue.get("priority", {}).get("name", "Unknown")
                by_priority[priority] += 1
                
                tasks_details.append({
                    "id": issue.get("id"),
                    "subject": issue.get("subject"),
                    "due_date": due_date_str,
                    "days_overdue": days_overdue,
                    "priority": priority,
                    "assigned_to": issue.get("assigned_to", {}).get("name", "Не назначен")
                })
            except ValueError:
                continue
    
    tasks_details.sort(key=lambda x: x["days_overdue"], reverse=True)
    avg_overdue = sum(overdue_days) / len(overdue_days) if overdue_days else 0
    
    return {
        "total": len(truly_overdue),
        "by_priority": dict(by_priority),
        "overdue_days_avg": round(avg_overdue, 1),
        "top_overdue": tasks_details[:10]
    }


async def get_lead_time(
    redmine_key: str,
    project_id: Optional[int] = None,
    period: str = "month"
) -> Dict[str, Any]:
    """Время выполнения задачи (Lead Time)"""
    start_date, end_date = get_period_range(period)
    
    params = {
        "closed_on": f">={start_date.strftime('%Y-%m-%d')}",
        "status_id": "closed",
    }
    if project_id:
        params["project_id"] = project_id
    
    closed_issues = await get_issues(redmine_key, params, use_cache=True)
    
    lead_times = []
    
    for issue in closed_issues:
        created_str = issue.get("created_on")
        closed_str = issue.get("closed_on")
        
        if created_str and closed_str:
            created = parse_date(created_str)
            closed = parse_date(closed_str)
            
            if created and closed:
                lead_time = (closed - created).days
                if lead_time >= 0:
                    lead_times.append(lead_time)
    
    if not lead_times:
        return {
            "median_days": 0,
            "percentile_90": 0,
            "avg_days": 0,
            "total_analyzed": 0
        }
    
    lead_times.sort()
    n = len(lead_times)
    
    median = lead_times[n // 2] if n % 2 else (lead_times[n // 2 - 1] + lead_times[n // 2]) / 2
    percentile_90 = lead_times[int(n * 0.9)] if n > 0 else 0
    avg = sum(lead_times) / n
    
    return {
        "median_days": round(median, 1),
        "percentile_90": round(percentile_90, 1),
        "avg_days": round(avg, 1),
        "total_analyzed": n
    }
