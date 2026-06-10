"""
API endpoints для метрик сроков и исполнения
"""
from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
from app.core.auth import get_redmine_key_from_api_key
from app.services import get_on_time_completion, get_overdue_tasks, get_lead_time

router = APIRouter(prefix="/api/v1/metrics", tags=["Метрики сроков и исполнения"])


def get_redmine_key_helper(request: Request) -> Optional[str]:
    """Извлекает Redmine API ключ из запроса"""
    api_key = getattr(request.state, "api_key", None)
    return get_redmine_key_from_api_key(api_key)


@router.get("/on-time-completion", summary="Выполнение задач в срок")
async def on_time_completion_endpoint(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("month", pattern="^(week|month|quarter)$")
):
    """
    **Дисциплина исполнения сроков**
    
    Доля задач, выполненных в установленные сроки.
    
    **Возвращает:**
    - Всего закрытых задач
    - Задачи с дедлайном
    - Выполнено в срок (количество и %)
    - Выполнено с опозданием
    
    **Целевые показатели:**
    - **>80%** — отличная дисциплина ✅
    - **60-80%** — приемлемо, но есть что улучшать ⚠️
    - **<60%** — проблемы с планированием или выполнением ❌
    
    **Анализируются только задачи** с установленным due_date
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_on_time_completion(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error calculating on-time completion: {str(e)}")


@router.get("/overdue-tasks", summary="Просроченные задачи")
async def overdue_tasks(request: Request, project_id: Optional[int] = None):
    """
    **Просроченные задачи**
    
    Активные задачи, у которых срок выполнения уже прошел.
    
    **Возвращает:**
    - Общее количество просроченных
    - Распределение по приоритетам
    - Среднюю просрочку в днях
    - Топ-10 самых просроченных задач с деталями
    
    **Критические показатели:**
    - Задачи с просрочкой >30 дней требуют срочного разбора
    - Высокий приоритет + большая просрочка = критично
    
    **Используйте для:** Еженедельного контроля и планирования приоритетов
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_overdue_tasks(redmine_key, project_id)
    except Exception as e:
        raise HTTPException(500, f"Error getting overdue tasks: {str(e)}")


@router.get("/lead-time", summary="Время выполнения задачи")
async def lead_time_endpoint(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("month", pattern="^(week|month|quarter)$")
):
    """
    **Lead Time - время от создания до завершения**
    
    Показывает, как быстро команда выполняет задачи.
    
    **Возвращает:**
    - Медиана (типичное время выполнения)
    - 90-й перцентиль (90% задач выполняются быстрее)
    - Среднее время
    - Количество проанализированных задач
    
    **Почему медиана, а не среднее?**
    - Медиана не искажается выбросами (очень долгими задачами)
    - Дает более реалистичную картину
    
    **Используйте для:**
    - SLA по времени реакции
    - Прогнозирования сроков
    - Выявления проблем в процессах
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_lead_time(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error calculating lead time: {str(e)}")
