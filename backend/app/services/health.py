"""
Индекс здоровья проекта и сводный дашборд
"""
from typing import Optional
import asyncio
import logging
from app.schemas import HealthScoreResponse, DashboardResponse
from .workload import get_backlog, get_backlog_change, get_old_tasks
from .deadlines import get_overdue_tasks, get_on_time_completion
from .planning import get_estimation_accuracy

logger = logging.getLogger(__name__)


async def get_project_health_score(redmine_key: str, project_id: Optional[int] = None) -> HealthScoreResponse:
    """
    Индекс здоровья проекта (0-100)
    
    Факторы влияния:
    - Просроченные задачи
    - Рост бэклога
    - Процент выполнения в срок
    - Старые задачи (>90 дней)
    - Переоткрытые задачи
    - Точность оценки трудозатрат
    """
    score = 100
    factors = []
    
    try:
        # Параллельно получаем все необходимые метрики
        overdue, backlog_data, backlog_change_data, on_time_data, old_tasks_data = await asyncio.gather(
            get_overdue_tasks(redmine_key, project_id),
            get_backlog(redmine_key, project_id),
            get_backlog_change(redmine_key, project_id, "month"),
            get_on_time_completion(redmine_key, project_id, "month"),
            get_old_tasks(redmine_key, project_id)
        )
        
        # 1. Просроченные задачи (до -30 баллов)
        if backlog_data["total"] > 0:
            overdue_percent = (overdue["total"] / backlog_data["total"]) * 100
            if overdue_percent > 20:
                penalty = min(30, overdue_percent)
                score -= penalty
                factors.append(f"Просроченные задачи: {overdue['total']} ({overdue_percent:.1f}%) - штраф {penalty:.0f} баллов")
            elif overdue_percent > 10:
                penalty = 15
                score -= penalty
                factors.append(f"Просроченные задачи: {overdue['total']} ({overdue_percent:.1f}%) - штраф {penalty} баллов")
        
        # 2. Рост бэклога (до -20 баллов)
        if backlog_change_data["trend"] == "increasing" and backlog_change_data["change"] > 10:
            penalty = min(20, backlog_change_data["change"])
            score -= penalty
            factors.append(f"Бэклог растет: +{backlog_change_data['change']} задач за месяц - штраф {penalty:.0f} баллов")
        
        # 3. Выполнение в срок (до -25 баллов)
        if on_time_data["on_time_percent"] < 80 and on_time_data["total_with_due_date"] > 0:
            penalty = (80 - on_time_data["on_time_percent"]) * 0.5
            score -= penalty
            factors.append(f"Выполнение в срок: {on_time_data['on_time_percent']:.1f}% - штраф {penalty:.0f} баллов")
        
        # 4. Старые задачи (до -15 баллов)
        if old_tasks_data["total_open"] > 0:
            old_percent = (old_tasks_data["older_90_days"] / old_tasks_data["total_open"]) * 100
            if old_percent > 15:
                penalty = min(15, old_percent)
                score -= penalty
                factors.append(f"Старые задачи (>90 дней): {old_tasks_data['older_90_days']} ({old_percent:.1f}%) - штраф {penalty:.0f} баллов")
        
        # 5. Точность оценок (до -10 баллов)
        try:
            accuracy = await get_estimation_accuracy(redmine_key, project_id, "month")
            if accuracy["total_analyzed"] > 5 and accuracy["accuracy_rate"] < 60:
                penalty = (60 - accuracy["accuracy_rate"]) * 0.2
                score -= penalty
                factors.append(f"Точность оценок: {accuracy['accuracy_rate']:.1f}% - штраф {penalty:.0f} баллов")
        except:
            pass
        
    except Exception as e:
        factors.append(f"Ошибка расчета: {str(e)}")
        logger.error(f"Error in get_project_health_score: {e}")
    
    # Ограничиваем диапазон 0-100
    score = max(0, min(100, score))
    
    # Интерпретация
    if score >= 85:
        status = "excellent"
        status_text = "🟢 Проект под контролем"
        recommendations = ["Продолжайте в том же духе", "Поддерживайте текущие процессы"]
    elif score >= 60:
        status = "warning"
        status_text = "🟡 Есть риски, требуется внимание"
        recommendations = [
            "Проанализируйте проблемные области",
            "Составьте план улучшений",
            "Усильте контроль проблемных метрик"
        ]
    else:
        status = "critical"
        status_text = "🔴 Критическая ситуация"
        recommendations = [
            "Требуется немедленное вмешательство руководства",
            "Проведите анализ первопричин проблем",
            "Пересмотрите процессы и распределение ресурсов",
            "Рассмотрите возможность реорганизации команды"
        ]
    
    return HealthScoreResponse(
        score=round(score, 1),
        status=status,
        status_text=status_text,
        factors=factors,
        recommendations=recommendations
    )


async def get_dashboard_metrics(redmine_key: str, project_id: Optional[int] = None, period: str = "month") -> DashboardResponse:
    """
    Сводный дашборд со всеми ключевыми метриками
    
    Возвращает все метрики в одном запросе для удобства
    Использует параллельные запросы для максимальной производительности
    """
    from .workload import get_inflow_ratio, get_velocity
    from .deadlines import get_lead_time
    from .planning import get_time_tracking_stats, get_workload_distribution, get_unassigned_tasks, get_tasks_without_due_date, get_estimation_accuracy
    from .quality import get_bug_rate, get_bug_metrics, get_bug_fix_ratio
    
    try:
        # Параллельно получаем индекс здоровья и все основные метрики
        health_score, workload_metrics, deadline_metrics, planning_metrics, quality_metrics = await asyncio.gather(
            # Индекс здоровья
            get_project_health_score(redmine_key, project_id),
            
            # Нагрузка и объем работы (все метрики параллельно)
            asyncio.gather(
                get_backlog(redmine_key, project_id),
                get_backlog_change(redmine_key, project_id, period),
                get_inflow_ratio(redmine_key, project_id, period),
                get_velocity(redmine_key, project_id, period),
                get_old_tasks(redmine_key, project_id)
            ),
            
            # Сроки и исполнение
            asyncio.gather(
                get_on_time_completion(redmine_key, project_id, period),
                get_overdue_tasks(redmine_key, project_id),
                get_lead_time(redmine_key, project_id, period)
            ),
            
            # Планирование
            asyncio.gather(
                get_time_tracking_stats(redmine_key, project_id, period),
                get_workload_distribution(redmine_key, project_id),
                get_unassigned_tasks(redmine_key, project_id),
                get_tasks_without_due_date(redmine_key, project_id)
            ),
            
            # Качество
            asyncio.gather(
                get_bug_rate(redmine_key, project_id, period),
                get_bug_metrics(redmine_key, project_id, period),
                get_bug_fix_ratio(redmine_key, project_id, period)
            )
        )

        
        # Формируем итоговый ответ с использованием Pydantic схемы
        return DashboardResponse(
            health_score=health_score,
            workload={
                "backlog": workload_metrics[0],
                "backlog_change": workload_metrics[1],
                "inflow_ratio": workload_metrics[2],
                "velocity": workload_metrics[3],
                "old_tasks": workload_metrics[4]
            },
            deadlines={
                "on_time_completion": deadline_metrics[0],
                "overdue_tasks": deadline_metrics[1],
                "lead_time": deadline_metrics[2]
            },
            planning={
                "time_tracking": planning_metrics[0],
                "workload_distribution": planning_metrics[1],
                "unassigned_tasks": planning_metrics[2],
                "tasks_without_due_date": planning_metrics[3],
                "estimation_accuracy": planning_metrics[4] if len(planning_metrics) > 4 else None
            },
            quality={
                "bug_rate": quality_metrics[0],
                "bug_metrics": quality_metrics[1],
                "bug_fix_ratio": quality_metrics[2]
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_dashboard_metrics: {e}")
        # Возвращаем пустой dashboard с ошибкой в health_score
        return DashboardResponse(
            health_score=HealthScoreResponse(
                score=0.0,
                status="critical",
                status_text=f"🔴 Ошибка: {str(e)}",
                factors=[str(e)],
                recommendations=["Проверьте соединение с Redmine", "Обратитесь к администратору"]
            ),
            workload={},
            deadlines={},
            planning={},
            quality={}
        )
