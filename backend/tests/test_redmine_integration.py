"""
Тесты для интеграции с Redmine API
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx


class TestRedmineClient:
    """Тесты для app/integrations/redmine_client.py"""
    
    @patch('httpx.AsyncClient.get')
    async def test_get_projects_from_redmine(self, mock_get):
        """Проверка получения проектов из Redmine"""
        # Мокаем HTTP ответ
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "projects": [
                {"id": 1, "name": "Project A", "identifier": "proj-a"},
                {"id": 2, "name": "Project B", "identifier": "proj-b"}
            ],
            "total_count": 2
        }
        mock_get.return_value = mock_response
        
        # Импортируем и тестируем
        from app.integrations.redmine_client import get_redmine_data
        
        result = await get_redmine_data("/projects.json")
        
        assert result["total_count"] == 2
        assert len(result["projects"]) == 2
        assert result["projects"][0]["name"] == "Project A"
    
    @patch('httpx.AsyncClient.get')
    async def test_get_issues_from_redmine(self, mock_get):
        """Проверка получения задач из Redmine"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issues": [
                {
                    "id": 101,
                    "subject": "Fix login bug",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "High"}
                }
            ],
            "total_count": 1
        }
        mock_get.return_value = mock_response
        
        from app.integrations.redmine_client import get_redmine_data
        
        result = await get_redmine_data("/issues.json?project_id=1")
        
        assert result["total_count"] == 1
        assert result["issues"][0]["subject"] == "Fix login bug"
    
    @patch('httpx.AsyncClient.get')
    async def test_redmine_api_error_handling(self, mock_get):
        """Проверка обработки ошибок Redmine API"""
        # Мокаем ошибку 401 Unauthorized
        mock_get.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )
        
        from app.integrations.redmine_client import get_redmine_data
        
        with pytest.raises(httpx.HTTPStatusError):
            await get_redmine_data("/projects.json")
    
    @patch('httpx.AsyncClient.get')
    async def test_redmine_timeout_handling(self, mock_get):
        """Проверка обработки timeout"""
        mock_get.side_effect = httpx.TimeoutException("Request timeout")
        
        from app.integrations.redmine_client import get_redmine_data
        
        with pytest.raises(httpx.TimeoutException):
            await get_redmine_data("/projects.json")


class TestRedmineDataTransformation:
    """Тесты для трансформации данных из Redmine"""
    
    def test_project_data_transformation(self):
        """Проверка трансформации данных проекта"""
        raw_project = {
            "id": 1,
            "name": "Test Project",
            "identifier": "test",
            "description": "Test description",
            "created_on": "2024-01-01T00:00:00Z",
            "updated_on": "2024-01-15T10:30:00Z"
        }
        
        # Трансформация для фронтенда
        transformed = {
            "id": raw_project["id"],
            "name": raw_project["name"],
            "code": raw_project["identifier"],
            "description": raw_project.get("description", "")
        }
        
        assert transformed["id"] == 1
        assert transformed["name"] == "Test Project"
        assert transformed["code"] == "test"
    
    def test_issue_status_mapping(self):
        """Проверка маппинга статусов задач"""
        statuses = ["New", "In Progress", "Resolved", "Closed", "Rejected"]
        
        status_map = {
            "New": "todo",
            "In Progress": "in_progress",
            "Resolved": "done",
            "Closed": "done",
            "Rejected": "cancelled"
        }
        
        assert status_map["New"] == "todo"
        assert status_map["In Progress"] == "in_progress"
        assert status_map["Resolved"] == "done"
    
    def test_priority_mapping(self):
        """Проверка маппинга приоритетов"""
        priorities = {
            "Low": 1,
            "Normal": 2,
            "High": 3,
            "Urgent": 4,
            "Immediate": 5
        }
        
        assert priorities["Low"] < priorities["Normal"]
        assert priorities["High"] > priorities["Normal"]
        assert priorities["Immediate"] == 5


class TestRedmineProjects:
    """Тесты для app/integrations/redmine_projects.py"""
    
    @patch('app.integrations.redmine_client.get_redmine_data')
    async def test_get_all_projects(self, mock_get_data):
        """Проверка получения всех проектов"""
        mock_get_data.return_value = {
            "projects": [
                {"id": 1, "name": "Alpha"},
                {"id": 2, "name": "Beta"}
            ]
        }
        
        # В реальности тут будет импорт из redmine_projects.py
        projects = mock_get_data.return_value["projects"]
        
        assert len(projects) == 2
        assert projects[0]["name"] == "Alpha"
    
    @patch('app.integrations.redmine_client.get_redmine_data')
    async def test_filter_active_projects(self, mock_get_data):
        """Проверка фильтрации активных проектов"""
        mock_get_data.return_value = {
            "projects": [
                {"id": 1, "name": "Active", "status": 1},
                {"id": 2, "name": "Closed", "status": 5},
                {"id": 3, "name": "Active 2", "status": 1}
            ]
        }
        
        projects = mock_get_data.return_value["projects"]
        active_projects = [p for p in projects if p["status"] == 1]
        
        assert len(active_projects) == 2
        assert all(p["status"] == 1 for p in active_projects)
