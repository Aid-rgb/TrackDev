"""
API endpoints для метрик планирования и управления
"""
from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
from app.core.auth import get_redmine_key_from_api_key
from app.services import (
    get_estimation_accuracy,
    get_time_tracking_stats,
    get_workload_distribution,
    get_unassigned_tasks,
    get_tasks_without_due_date
)

router = APIRouter(prefix="/api/v1/metrics", tags=["Метрики планирования и управления"])


def get_redmine_key_helper(request: Request) -> Optional[str]:
    """Извлекает Redmine API ключ из запроса"""
    api_key = getattr(request.state, "api_key", None)
    return get_redmine_key_from_api_key(api_key)


@router.get("/estimation-accuracy", summary="Точность оценки трудозатрат")
async def estimation_accuracy(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("month", pattern="^(week|month|quarter)$")
):
    """
    **Качество планирования**
    
    Сравнивает плановые трудозатраты (estimated_hours) с фактическими (time_entries).
    
    **Возвращает:**
    - Среднее отклонение в %
    - Недооцененных задач (факт > план + 20%)
    - Переоцененных задач (факт < план - 20%)
    - Точных оценок (отклонение ±20%)
    - Процент точности
    - Топ-10 худших оценок с деталями
    
    **Интерпретация:**
    - **>70% точности** — хорошее планирование ✅
    - **50-70%** — среднее качество оценок ⚠️
    - **<50%** — проблемы с оценкой, нужны улучшения ❌
    
    **Используйте для:** Обучения команды оценке, улучшения точности планирования
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_estimation_accuracy(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error calculating estimation accuracy: {str(e)}")


@router.get("/time-tracking", summary="Статистика учета времени")
async def time_tracking(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("month", pattern="^(week|month|quarter)$")
):
    """
    **Учет рабочего времени**
    
    Анализ затраченного времени на основе time_entries.
    
    **Возвращает:**
    - Общее количество часов
    - Количество записей времени
    - Задачи с учетом времени
    - Среднее время в день
    - Распределение по пользователям
    - Распределение по типам активностей (разработка, тестирование, ревью и т.д.)
    - Топ-10 пользователей по времени
    
    **Используйте для:**
    - Анализа загрузки команды
    - Выявления перегруженных сотрудников
    - Отчетности для клиента
    - Расчета стоимости работ
    
    **Норма:** 6-8 часов продуктивного времени в день
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_time_tracking_stats(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error getting time tracking stats: {str(e)}")


@router.get("/workload-distribution", summary="Распределение нагрузки по команде")
async def workload_distribution_endpoint(request: Request, project_id: Optional[int] = None):
    """
    **Нагрузка на исполнителей**
    
    Показывает, как распределены активные задачи между членами команды.
    
    **Возвращает:**
    - Всего пользователей в работе
    - Задачи без исполнителя
    - Среднюю нагрузку на человека
    - Детальную нагрузку по каждому:
      - Количество активных задач
      - Оценочное время на задачи
      - Среднее время на задачу
      - Топ-5 задач пользователя
    
    **Используйте для:**
    - Балансировки нагрузки
    - Выявления перегруженных сотрудников
    - Планирования отпусков
    - Распределения новых задач
    
    **Проблемные индикаторы:**
    - Большой разброс в нагрузке между сотрудниками
    - >15 активных задач на человека
    - >100 часов estimated_hours на человека
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_workload_distribution(redmine_key, project_id)
    except Exception as e:
        raise HTTPException(500, f"Error getting workload distribution: {str(e)}")


@router.get("/unassigned-tasks", summary="Задачи без исполнителя")
async def unassigned_tasks(request: Request, project_id: Optional[int] = None):
    """
    **Задачи без назначенного исполнителя**
    
    Открытые задачи, которые никому не назначены.
    
    **Возвращает:**
    - Общее количество
    - Распределение по приоритетам
    - Процент от общего бэклога
    
    **Проблемные индикаторы:**
    - >10% задач без исполнителя — проблемы с распределением
    - Высокоприоритетные задачи без исполнителя — критично
    
    **Рекомендации:**
    - Еженедельный разбор незакрепленных задач
    - Назначение ответственного на планировании
    - Автоматические правила назначения
    
    **Используйте для:** Контроля организационных процессов
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_unassigned_tasks(redmine_key, project_id)
    except Exception as e:
        raise HTTPException(500, f"Error getting unassigned tasks: {str(e)}")


@router.get("/tasks-without-due-date", summary="Задачи без срока выполнения")
async def tasks_without_due_date(request: Request, project_id: Optional[int] = None):
    """
    **Задачи без установленного дедлайна**
    
    Открытые задачи, для которых не определена дата завершения.
    
    **Возвращает:**
    - Общее количество
    - Процент от общего бэклога
    
    **Целевые показатели:**
    - **<20%** — хорошее планирование ✅
    - **20-40%** — среднее качество планирования ⚠️
    - **>40%** — слабое планирование, нужны улучшения ❌
    
    **Проблемы:**
    - Невозможно контролировать сроки
    - Сложно приоритизировать работу
    - Риск "вечных" задач
    
    **Рекомендации:**
    - Установить дедлайны для всех задач
    - Использовать плановые даты даже для второстепенных задач
    - Регулярно пересматривать сроки
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_tasks_without_due_date(redmine_key, project_id)
    except Exception as e:
        raise HTTPException(500, f"Error getting tasks without due date: {str(e)}")
