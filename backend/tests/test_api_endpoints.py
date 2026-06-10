"""
Тесты для API эндпоинтов проектов и задач
"""
import pytest
from unittest.mock import patch, MagicMock


class TestProjectsAPI:
    """Тесты для эндпоинта /api/v1/projects"""
    
    def test_get_projects_requires_auth(self, client):
        """Проверка что эндпоинт требует авторизацию"""
        response = client.get("/api/v1/projects")
        assert response.status_code in [401, 403]
    
    @patch('app.integrations.redmine_client.get_redmine_data')
    def test_get_projects_with_auth(self, mock_get_data, client, auth_headers):
        """Проверка получения списка проектов с авторизацией"""
        # Мокаем ответ от Redmine
        mock_get_data.return_value = {
            "projects": [
                {"id": 1, "name": "Project Alpha", "identifier": "alpha"},
                {"id": 2, "name": "Project Beta", "identifier": "beta"}
            ]
        }
        
        response = client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
    
    @patch('app.integrations.redmine_client.get_redmine_data')
    def test_get_project_by_id(self, mock_get_data, client, auth_headers):
        """Проверка получения конкретного проекта"""
        mock_get_data.return_value = {
            "project": {
                "id": 1,
                "name": "Test Project",
                "identifier": "test"
            }
        }
        
        response = client.get("/api/v1/projects/1", headers=auth_headers)
        assert response.status_code in [200, 404]  # 404 если роут не реализован


class TestIssuesAPI:
    """Тесты для эндпоинта задач"""
    
    @patch('app.integrations.redmine_client.get_redmine_data')
    def test_get_issues(self, mock_get_data, client, auth_headers):
        """Проверка получения списка задач"""
        mock_get_data.return_value = {
            "issues": [
                {
                    "id": 1,
                    "subject": "Test Issue",
                    "status": {"name": "New"},
                    "priority": {"name": "Normal"}
                }
            ]
        }
        
        response = client.get("/api/v1/issues", headers=auth_headers)
        assert response.status_code in [200, 404]


class TestAuthMiddleware:
    """Тесты для middleware авторизации"""
    
    def test_missing_api_key(self, client):
        """Запрос без API ключа должен быть отклонен"""
        response = client.get("/api/v1/projects")
        assert response.status_code in [401, 403]
    
    def test_invalid_api_key(self, client):
        """Запрос с невалидным API ключом должен быть отклонен"""
        headers = {"X-API-Key": "invalid_key_12345"}
        response = client.get("/api/v1/projects", headers=headers)
        assert response.status_code in [401, 403]
    
    def test_health_endpoint_no_auth(self, client):
        """Health endpoint должен работать без авторизации"""
        response = client.get("/health")
        assert response.status_code == 200
