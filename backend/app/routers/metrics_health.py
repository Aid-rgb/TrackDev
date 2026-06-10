"""
API endpoints для индекса здоровья проекта и сводного дашборда
"""
from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional
from app.core.auth import get_redmine_key_from_api_key
from app.services import get_project_health_score, get_dashboard_metrics
from app.schemas import HealthScoreResponse, DashboardResponse, ErrorResponse, MetricQueryParams
from app.core.exceptions import (
    RedmineException,
    RedmineConnectionError,
    RedmineAuthError,
    RedmineForbiddenError
)
import logging

router = APIRouter(prefix="/api/v1/metrics", tags=["Индекс здоровья и дашборд"])
logger = logging.getLogger(__name__)


def get_redmine_key(request: Request) -> Optional[str]:
    """Извлекает Redmine API ключ из запроса"""
    api_key = getattr(request.state, "api_key", None)
    return get_redmine_key_from_api_key(api_key)


@router.get(
    "/dashboard", 
    summary="Сводный дашборд со всеми метриками",
    response_model=DashboardResponse,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def dashboard(
    request: Request, 
    project_id: Optional[int] = Query(None, description="ID проекта (None = все проекты)"),
    period: str = Query("month", description="Период: week/month/quarter/year или YYYY-MM-DD|YYYY-MM-DD")
):
    """
    **Сводный дашборд для руководства**
    
    Возвращает все ключевые метрики проекта в одном запросе:
    
    - 🏥 Индекс здоровья проекта (0-100)
    - 📊 Нагрузка и объем работы
    - ⏰ Сроки и исполнение  
    - ⏱ Учет времени
    - 👥 Распределение нагрузки
    - 🎯 Качество
    
    **Параметры:**
    - `project_id`: ID проекта в Redmine. Если не указан - данные по всем проектам
    - `period`: Период (week, month, quarter, year или кастомный YYYY-MM-DD|YYYY-MM-DD)
    
    **Использование:** Основной endpoint для получения полной картины состояния проекта
    
    **Пример:**
    ```
    GET /api/v1/metrics/dashboard?project_id=123&period=month
    GET /api/v1/metrics/dashboard?period=2024-01-01|2024-12-31
    ```
    """
    # Валидация параметров через Pydantic
    try:
        params = MetricQueryParams(project_id=project_id, period=period)
    except ValueError as e:
        logger.warning("Invalid dashboard parameters", extra={
            "project_id": project_id,
            "period": period,
            "error": str(e)
        })
        raise HTTPException(status_code=400, detail=str(e))
    
    redmine_key = get_redmine_key(request)
    user_id = redmine_key[:8] if redmine_key else "unknown"
    
    logger.info("Fetching dashboard metrics", extra={
        "user_id": user_id,
        "project_id": params.project_id,
        "period": params.period,
        "endpoint": "/metrics/dashboard"
    })
    
    try:
        result = await get_dashboard_metrics(redmine_key, params.project_id, params.period)
        
        logger.info("Dashboard metrics calculated successfully", extra={
            "user_id": user_id,
            "project_id": params.project_id,
            "period": params.period,
            "health_score": result.health_score.score
        })
        
        return result
    except RedmineAuthError as e:
        logger.warning("Authentication failed for dashboard", extra={
            "user_id": user_id,
            "project_id": params.project_id,
            "error": e.message
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineConnectionError as e:
        logger.error("Connection failed for dashboard", extra={
            "user_id": user_id,
            "project_id": params.project_id,
            "error": e.message,
            "details": e.details
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineForbiddenError as e:
        logger.warning("Access forbidden for dashboard", extra={
            "user_id": user_id,
            "project_id": params.project_id,
            "error": e.message
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineException as e:
        logger.error("Redmine error for dashboard", extra={
            "user_id": user_id,
            "project_id": params.project_id,
            "error": e.message,
            "status_code": e.status_code,
            "details": e.details
        })
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error calculating dashboard metrics", extra={
            "user_id": user_id,
            "project_id": params.project_id,
            "period": params.period,
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        raise HTTPException(500, f"Внутренняя ошибка при расчете метрик: {str(e)}")


@router.get(
    "/health-score", 
    summary="Индекс здоровья проекта",
    response_model=HealthScoreResponse,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def health_score(
    request: Request, 
    project_id: Optional[int] = Query(None, description="ID проекта (None = все проекты)")
):
    """
    **Индекс здоровья проекта (0-100)**
    
    Интегральная оценка состояния проекта на основе всех ключевых метрик.
    
    **Интерпретация:**
    - 🟢 **85-100** — проект под контролем, все показатели в норме
    - 🟡 **60-84** — есть риски, требуется внимание к проблемным областям
    - 🔴 **<60** — критическая ситуация, требуется немедленное вмешательство руководства
    
    **Факторы влияния:**
    - Просроченные задачи (штраф до -30 баллов)
    - Рост бэклога (штраф до -20 баллов)
    - Процент выполнения в срок (штраф до -25 баллов)
    - Старые задачи >90 дней (штраф до -15 баллов)
    - Точность оценки трудозатрат (штраф до -10 баллов)
    
    **Включает рекомендации** по улучшению показателей
    
    **Пример:**
    ```
    GET /api/v1/metrics/health-score?project_id=123
    ```
    """
    if project_id is not None and project_id <= 0:
        logger.warning("Invalid project_id for health score", extra={
            "project_id": project_id
        })
        raise HTTPException(status_code=400, detail="Invalid project_id")
    
    redmine_key = get_redmine_key(request)
    user_id = redmine_key[:8] if redmine_key else "unknown"
    
    logger.info("Calculating health score", extra={
        "user_id": user_id,
        "project_id": project_id,
        "endpoint": "/metrics/health-score"
    })
    
    try:
        result = await get_project_health_score(redmine_key, project_id)
        
        logger.info("Health score calculated", extra={
            "user_id": user_id,
            "project_id": project_id,
            "score": result.score,
            "status": result.status
        })
        
        return result
    except RedmineAuthError as e:
        logger.warning("Authentication failed for health score", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": e.message
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineConnectionError as e:
        logger.error("Connection failed for health score", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": e.message,
            "details": e.details
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineForbiddenError as e:
        logger.warning("Access forbidden for health score", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": e.message
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineException as e:
        logger.error("Redmine error for health score", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": e.message,
            "status_code": e.status_code,
            "details": e.details
        })
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error calculating health score", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        raise HTTPException(500, f"Внутренняя ошибка при расчете индекса здоровья: {str(e)}")
