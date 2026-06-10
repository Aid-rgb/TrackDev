"""
API endpoints для метрик качества
"""
from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
from app.core.auth import get_redmine_key_from_api_key
from app.services import get_bug_rate, get_bug_metrics, get_bug_fix_ratio, get_reopened_tasks

router = APIRouter(prefix="/api/v1/metrics", tags=["Метрики качества"])


def get_redmine_key_helper(request: Request) -> Optional[str]:
    """Извлекает Redmine API ключ из запроса"""
    api_key = getattr(request.state, "api_key", None)
    return get_redmine_key_from_api_key(api_key)


@router.get("/bug-rate", summary="Доля ошибок в проекте")
async def bug_rate(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("month", pattern="^(week|month|quarter)$")
):
    """
    **Bug Rate - доля дефектов**
    
    Процент задач типа Bug от общего количества задач.
    
    **Возвращает:**
    - Количество багов
    - Общее количество задач
    - Процент багов
    
    **Целевые показатели:**
    - **<15%** — хорошее качество продукта ✅
    - **15-25%** — среднее качество, есть что улучшать ⚠️
    - **>25%** — проблемы с качеством, требуется анализ ❌
    
    **Высокий Bug Rate может означать:**
    - Недостаточное тестирование
    - Сложный/устаревший код
    - Слабые требования
    - Недостаток code review
    
    **Используйте для:** Отслеживания качества продукта в динамике
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_bug_rate(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error calculating bug rate: {str(e)}")


@router.get("/bug-metrics", summary="Метрики по ошибкам")
async def bug_metrics(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("month", pattern="^(week|month|quarter)$")
):
    """
    **Динамика ошибок**
    
    Новые, закрытые и открытые баги за период.
    
    **Возвращает:**
    - Новые баги (зарегистрированные за период)
    - Закрытые баги (исправленные за период)
    - Открытые баги (текущий бэклог багов)
    
    **Анализ тренда:**
    - Новых > Закрытых — качество ухудшается ⚠️
    - Новых < Закрытых — качество улучшается ✅
    - Открытых багов растет — технический долг накапливается
    
    **Используйте для:** 
    - Мониторинга качества релизов
    - Планирования исправлений
    - Анализа эффективности тестирования
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_bug_metrics(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error getting bug metrics: {str(e)}")


@router.get("/bug-fix-ratio", summary="Коэффициент устранения ошибок")
async def bug_fix_ratio(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("month", pattern="^(week|month|quarter)$")
):
    """
    **Способность команды устранять ошибки**
    
    Соотношение закрытых багов к новым.
    
    **Формула:** `закрытые баги / новые баги`
    
    **Интерпретация:**
    - **>= 1.0** — команда успевает устранять все новые ошибки ✅
    - **0.8-1.0** — баланс близок к равновесию ⚖️
    - **< 0.8** — ошибки накапливаются быстрее, чем исправляются ❌
    
    **Действия при ratio < 0.8:**
    - Увеличить приоритет исправления багов
    - Выделить время на bug fixing
    - Провести анализ причин появления багов
    - Улучшить процессы QA
    
    **Используйте для:** Контроля технического долга и качества
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_bug_fix_ratio(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error calculating bug fix ratio: {str(e)}")


@router.get("/reopened-tasks", summary="Переоткрытые задачи")
async def reopened_tasks(
    request: Request,
    project_id: Optional[int] = None,
    period: str = Query("month", pattern="^(week|month|quarter)$")
):
    """
    **Качество выполнения задач**
    
    Задачи, которые после закрытия пришлось возвращать в работу.
    
    **Возвращает:**
    - Количество переоткрытых
    - Проанализировано задач
    - Процент переоткрытий
    
    **Целевые показатели:**
    - **<5%** — отличное качество выполнения ✅
    - **5-10%** — приемлемо ⚠️
    - **>10%** — проблемы с качеством работы или тестирования ❌
    
    **Высокий процент переоткрытий означает:**
    - Недостаточная проверка перед закрытием
    - Слабое тестирование
    - Неполное выполнение требований
    - Спешка при закрытии задач
    
    **Note:** Требует доступ к journals API (медленная операция)
    """
    redmine_key = get_redmine_key_helper(request)
    
    try:
        return await get_reopened_tasks(redmine_key, project_id, period)
    except Exception as e:
        raise HTTPException(500, f"Error getting reopened tasks: {str(e)}")
