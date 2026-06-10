"""
Services модуль - бизнес-логика приложения (метрики)
"""
from .health import get_project_health_score, get_dashboard_metrics
from .workload import get_backlog, get_backlog_change, get_inflow_ratio, get_velocity, get_old_tasks
from .deadlines import get_on_time_completion, get_overdue_tasks, get_lead_time
from .planning import (
    get_time_tracking_stats,
    get_workload_distribution,
    get_estimation_accuracy,
    get_unassigned_tasks,
    get_tasks_without_due_date
)
from .quality import get_bug_rate, get_bug_metrics, get_bug_fix_ratio, get_reopened_tasks

__all__ = [
    # Health
    "get_project_health_score",
    "get_dashboard_metrics",
    # Workload
    "get_backlog",
    "get_backlog_change",
    "get_inflow_ratio",
    "get_velocity",
    "get_old_tasks",
    # Deadlines
    "get_on_time_completion",
    "get_overdue_tasks",
    "get_lead_time",
    # Planning
    "get_time_tracking_stats",
    "get_workload_distribution",
    "get_estimation_accuracy",
    "get_unassigned_tasks",
    "get_tasks_without_due_date",
    # Quality
    "get_bug_rate",
    "get_bug_metrics",
    "get_bug_fix_ratio",
    "get_reopened_tasks",
]
