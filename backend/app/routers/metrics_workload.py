"""
API endpoints для метрик нагрузки и объема работы
"""
from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
from app.core.auth import get_redmine_key_from_api_key
from app.services import get_backlog, get_backlog_change, get_inflow_ratio, get_velocity, get_old_tasks

router = APIRouter(prefix="/api/v1/metrics", tags=["Метрики нагрузки и объема работы"])


def get_redmine_key_helper(request: Request) -> Optional[str]:
    """Извлекает Redmine API ключ из запроса"""
    api_key = getattr(request.state, "api_key", None)
    return get_redmine_key_from_api_key(api_key)


@router.get("/backlog", summary="Бэклог - количество открытых задач")
async def backlog(request: Request, project_id: Optional[int] = None):
    """
    **Бэклог проекта**
    
    Общее количество невыполненных задач с разбивкой по категориям.
    
    **Возвращает:**
    - Общее количество открытых задач
    - Распределение по приоритетам (Critical, High, Normal, Low)
    - Распределение по типам задач (Bug, Feature, Task и т.д.)
    - Распределение по статусам (New, In Progress, On Hold и т.д.)
    
    **Зачем нужна:** Позволяет оценить общий объем накопленной работы и понять структуру задач
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_backlog(redmine_key, project_id)
    except Exception as e:
        raise HTTPException(500, f"Error getting backlog: {str(e)}")


@router.get("/backlog-change", summary="Изменение бэклога за период")
async def backlog_change(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("week", pattern="^(week|month|quarter)$")
):
    """
    **Динамика бэклога**
    
    Сравнение новых и закрытых задач за выбранный период.
    
    **Возвращает:**
    - Количество новых задач
    - Количество закрытых задач
    - Изменение (разница)
    - Тренд: увеличение / уменьшение / стабильно
    
    **Интерпретация:**
    - Тренд **"увеличение"** — объем работ растет, команда не справляется
    - Тренд **"уменьшение"** — команда сокращает накопленный объем
    - Тренд **"стабильно"** — команда успевает закрывать столько же, сколько приходит
    
    **Параметры:**
    - `period`: week (7 дней), month (30 дней), quarter (90 дней)
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_backlog_change(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error calculating backlog change: {str(e)}")


@router.get("/inflow-ratio", summary="Коэффициент притока задач")
async def inflow_ratio(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("week", pattern="^(week|month|quarter)$")
):
    """
    **Коэффициент притока задач**
    
    Отношение новых задач к выполненным. Ранний индикатор перегрузки проекта.
    
    **Формула:** `новые задачи / закрытые задачи`
    
    **Интерпретация:**
    - **< 0.8** — команда активно сокращает накопленный объем работ ✅
    - **0.8-1.2** — стабильная ситуация, баланс ⚖️
    - **> 1.2** — объем работ растет, возможна перегрузка ⚠️
    
    **Рекомендации при ratio > 1.2:**
    - Увеличить команду
    - Снизить приток новых задач
    - Оптимизировать процессы
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_inflow_ratio(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error calculating inflow ratio: {str(e)}")


@router.get("/velocity", summary="Скорость выполнения задач")
async def velocity_endpoint(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("week", pattern="^(week|month|quarter)$")
):
    """
    **Velocity - скорость команды**
    
    Количество задач, которое команда успевает закрыть за период.
    
    **Возвращает:**
    - Общее количество закрытых задач
    - Разбивку по неделям (для месячного периода)
    
    **Зачем нужна:**
    - Отслеживание производительности команды в динамике
    - Планирование спринтов и релизов
    - Выявление периодов спада/роста производительности
    
    **Нормальная velocity зависит от:**
    - Размера команды
    - Сложности задач
    - Зрелости процессов
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_velocity(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error calculating velocity: {str(e)}")


@router.get("/old-tasks", summary="Старые задачи")
async def old_tasks(request: Request, project_id: Optional[int] = None):
    """
    **Зависшие задачи**
    
    Открытые задачи, которые долго находятся в работе.
    
    **Возвращает:**
    - Задачи старше 30 дней
    - Задачи старше 90 дней  
    - Задачи старше 180 дней
    - Общее количество открытых
    
    **Проблемные индикаторы:**
    - Задачи >90 дней часто "потерянные" или заблокированные
    - Задачи >180 дней — технический долг или забытые задачи
    
    **Рекомендации:**
    - Еженедельный разбор старых задач
    - Либо закрыть, либо актуализировать
    - Выявить причины зависания
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_old_tasks(redmine_key, project_id)
    except Exception as e:
        raise HTTPException(500, f"Error getting old tasks: {str(e)}")
