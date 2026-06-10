"""
API endpoints для Redmine (только для администраторов)
Минимальный набор для получения списка проектов
"""
from fastapi import APIRouter, Request, HTTPException, Query
from app.integrations.redmine_projects import get_projects, get_project
from app.schemas import ProjectsListResponse, ProjectDetailResponse, ErrorResponse
from app.core.exceptions import (
    RedmineException,
    RedmineConnectionError,
    RedmineAuthError,
    RedmineNotFoundError,
    RedmineForbiddenError
)
import logging

router = APIRouter(prefix="/api/v1", tags=["Redmine API"])
logger = logging.getLogger(__name__)


def get_redmine_key(request: Request) -> str:
    """Извлекает Redmine API ключ из запроса"""
    api_key = getattr(request.state, "api_key", None)
    if not api_key:
        logger.warning("API key missing in request", extra={
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown"
        })
        raise HTTPException(status_code=401, detail="API key required")
    return api_key


@router.get(
    "/projects", 
    summary="Список проектов",
    response_model=ProjectsListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверные параметры"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        500: {"model": ErrorResponse, "description": "Ошибка сервера"}
    }
)
async def get_projects_endpoint(
    request: Request, 
    limit: int = Query(100, ge=1, le=500, description="Максимальное количество проектов")
):
    """
    Получение списка всех доступных проектов
    
    **Параметры:**
    - `limit`: Максимальное количество проектов (от 1 до 500, по умолчанию 100)
    
    **Возвращает:**
    - `total`: Количество возвращенных проектов
    - `projects`: Список проектов с основной информацией (id, name, identifier, etc.)
    
    **Пример:**
    ```
    GET /api/v1/projects?limit=10
    ```
    """
    redmine_key = get_redmine_key(request)
    user_id = redmine_key[:8]  # Первые 8 символов для идентификации
    
    logger.info("Fetching projects list", extra={
        "user_id": user_id,
        "limit": limit,
        "endpoint": "/projects"
    })
    
    try:
        projects = await get_projects(redmine_key, limit)
        
        logger.info("Projects fetched successfully", extra={
            "user_id": user_id,
            "count": len(projects),
            "limit": limit
        })
        
        return ProjectsListResponse(
            total=len(projects),
            projects=projects
        )
    except RedmineAuthError as e:
        logger.warning("Authentication failed for projects", extra={
            "user_id": user_id,
            "error": e.message
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineConnectionError as e:
        logger.error("Connection failed for projects", extra={
            "user_id": user_id,
            "error": e.message,
            "details": e.details
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineForbiddenError as e:
        logger.warning("Access forbidden for projects", extra={
            "user_id": user_id,
            "error": e.message
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineException as e:
        logger.error("Redmine error for projects", extra={
            "user_id": user_id,
            "error": e.message,
            "status_code": e.status_code,
            "details": e.details
        })
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error fetching projects", extra={
            "user_id": user_id,
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Внутренняя ошибка сервера при получении списка проектов: {str(e)}"
        )


@router.get(
    "/projects/{project_id}", 
    summary="Информация о проекте",
    response_model=ProjectDetailResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверный project_id"},
        401: {"model": ErrorResponse, "description": "Не авторизован"},
        404: {"model": ErrorResponse, "description": "Проект не найден"},
        500: {"model": ErrorResponse, "description": "Ошибка сервера"}
    }
)
async def get_project_endpoint(
    request: Request, 
    project_id: int
):
    """
    Получение детальной информации о конкретном проекте
    
    **Параметры:**
    - `project_id`: ID проекта в Redmine (должен быть положительным числом)
    
    **Возвращает:**
    - Детальная информация о проекте (название, идентификатор, описание, статус, даты создания/обновления)
    
    **Пример:**
    ```
    GET /api/v1/projects/123
    ```
    """
    if project_id <= 0:
        logger.warning("Invalid project_id requested", extra={
            "project_id": project_id,
            "endpoint": "/projects/{project_id}"
        })
        raise HTTPException(status_code=400, detail="Invalid project_id: must be positive integer")
        
    redmine_key = get_redmine_key(request)
    user_id = redmine_key[:8]
    
    logger.info("Fetching project details", extra={
        "user_id": user_id,
        "project_id": project_id,
        "endpoint": f"/projects/{project_id}"
    })
    
    try:
        proj = await get_project(redmine_key, project_id)
        
        logger.info("Project fetched successfully", extra={
            "user_id": user_id,
            "project_id": project_id,
            "project_name": proj.get("name", "unknown")
        })
        
        return ProjectDetailResponse(project=proj)
    except RedmineNotFoundError as e:
        logger.warning("Project not found", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": e.message
        })
        raise HTTPException(
            status_code=404, 
            detail=f"Проект с ID {project_id} не найден в Redmine. Проверьте ID и права доступа"
        )
    except RedmineAuthError as e:
        logger.warning("Authentication failed for project", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": e.message
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineForbiddenError as e:
        logger.warning("Access forbidden for project", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": e.message
        })
        raise HTTPException(
            status_code=403, 
            detail=f"Доступ к проекту {project_id} запрещен. У вас нет прав на этот проект"
        )
    except RedmineConnectionError as e:
        logger.error("Connection failed for project", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": e.message,
            "details": e.details
        })
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except RedmineException as e:
        logger.error("Redmine error for project", extra={
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
        logger.error("Unexpected error fetching project", extra={
            "user_id": user_id,
            "project_id": project_id,
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Внутренняя ошибка сервера при получении проекта: {str(e)}"
        )
