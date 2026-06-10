"""
Интеграция с Redmine API - работа с проектами
"""
from typing import List, Dict, Any
from .redmine_client import RedmineClient


async def get_projects(redmine_key: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Получение списка всех доступных проектов
    
    Args:
        redmine_key: Redmine API ключ пользователя
        limit: Максимальное количество проектов
    
    Returns:
        List[Dict]: Список проектов
    """
    try:
        data = await RedmineClient.request("GET", "projects.json", redmine_key=redmine_key, params={"limit": limit})
        return data.get("projects", [])
    except Exception as e:
        raise Exception(f"Failed to fetch projects: {str(e)}")


async def get_project(redmine_key: str, project_id: int) -> Dict[str, Any]:
    """
    Получение информации о конкретном проекте
    
    Args:
        redmine_key: Redmine API ключ пользователя
        project_id: ID проекта
    
    Returns:
        Dict: Информация о проекте
    """
    try:
        data = await RedmineClient.request("GET", f"projects/{project_id}.json", redmine_key=redmine_key)
        return data.get("project", {})
    except Exception as e:
        raise Exception(f"Failed to fetch project {project_id}: {str(e)}")
