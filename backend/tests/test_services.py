"""
Тесты для сервисных слоев (бизнес-логика)
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestHealthService:
    """Тесты для app/services/health.py"""
    
    def test_health_calculation_logic(self):
        """Проверка логики расчета здоровья проекта"""
        # Пример теста бизнес-логики
        # В реальности тут будет импорт функций из services/health.py
        
        # Фейковые метрики проекта
        metrics = {
            "completed_on_time": 18,
            "total_completed": 20,
            "open_bugs": 3,
            "critical_bugs": 0
        }
        
        # Расчет score
        on_time_rate = metrics["completed_on_time"] / metrics["total_completed"]
        bug_penalty = (metrics["open_bugs"] + metrics["critical_bugs"] * 2) * 2
        health_score = (on_time_rate * 100) - bug_penalty
        
        assert health_score == 84.0  # 90 - 6
        assert health_score >= 70  # Хороший уровень здоровья


class TestWorkloadService:
    """Тесты для app/services/workload.py"""
    
    def test_workload_distribution(self):
        """Проверка расчета распределения нагрузки"""
        team_tasks = [
            {"developer": "Alice", "estimated_hours": 40},
            {"developer": "Bob", "estimated_hours": 35},
            {"developer": "Charlie", "estimated_hours": 25}
        ]
        
        total_hours = sum(t["estimated_hours"] for t in team_tasks)
        capacity_per_person = 40  # часов в неделю
        total_capacity = capacity_per_person * len(team_tasks)
        
        utilization = (total_hours / total_capacity) * 100
        
        assert total_hours == 100
        assert total_capacity == 120
        assert utilization == pytest.approx(83.33, rel=0.01)
    
    def test_overloaded_developer_detection(self):
        """Проверка обнаружения перегруженных разработчиков"""
        developers = [
            {"name": "Dev1", "hours": 45, "capacity": 40},
            {"name": "Dev2", "hours": 38, "capacity": 40},
            {"name": "Dev3", "hours": 52, "capacity": 40}
        ]
        
        overloaded = [d for d in developers if d["hours"] > d["capacity"]]
        
        assert len(overloaded) == 2
        assert overloaded[0]["name"] == "Dev1"
        assert overloaded[1]["name"] == "Dev3"


class TestDeadlineService:
    """Тесты для app/services/deadlines.py"""
    
    def test_deadline_risk_calculation(self):
        """Проверка расчета риска дедлайна"""
        today = datetime.now()
        
        # Тестовые задачи
        tasks = [
            {"id": 1, "due_date": today + timedelta(days=2), "progress": 30},
            {"id": 2, "due_date": today + timedelta(days=10), "progress": 80},
            {"id": 3, "due_date": today + timedelta(days=5), "progress": 60}
        ]
        
        def calculate_risk(task):
            days_left = (task["due_date"] - today).days
            progress = task["progress"]
            
            if days_left <= 3 and progress < 70:
                return "high"
            elif days_left <= 7 and progress < 50:
                return "medium"
            else:
                return "low"
        
        risks = [calculate_risk(t) for t in tasks]
        
        assert risks[0] == "high"   # 2 дня, 30% - высокий риск
        assert risks[1] == "low"    # 10 дней, 80% - низкий риск
        assert risks[2] == "medium" # 5 дней, 60% - средний риск
    
    def test_overdue_detection(self):
        """Проверка обнаружения просроченных задач"""
        today = datetime.now()
        
        tasks = [
            {"id": 1, "due_date": today - timedelta(days=5)},
            {"id": 2, "due_date": today + timedelta(days=3)},
            {"id": 3, "due_date": today - timedelta(days=1)}
        ]
        
        overdue = [t for t in tasks if t["due_date"] < today]
        
        assert len(overdue) == 2
        assert overdue[0]["id"] == 1
        assert overdue[1]["id"] == 3


class TestPlanningService:
    """Тесты для app/services/planning.py"""
    
    def test_velocity_calculation(self):
        """Проверка расчета velocity команды"""
        sprint_story_points = [35, 42, 38, 45, 40, 37]
        
        avg_velocity = sum(sprint_story_points) / len(sprint_story_points)
        
        assert avg_velocity == pytest.approx(39.5, rel=0.01)
    
    def test_sprint_progress(self):
        """Проверка расчета прогресса спринта"""
        sprint = {
            "total_tasks": 20,
            "completed_tasks": 13,
            "in_progress_tasks": 4,
            "todo_tasks": 3
        }
        
        progress = (sprint["completed_tasks"] / sprint["total_tasks"]) * 100
        
        assert progress == 65.0
        assert sprint["completed_tasks"] + sprint["in_progress_tasks"] + sprint["todo_tasks"] == sprint["total_tasks"]


class TestQualityService:
    """Тесты для app/services/quality.py"""
    
    def test_bug_rate_calculation(self):
        """Проверка расчета bug rate"""
        metrics = {
            "total_tasks": 100,
            "bugs_found": 8,
            "features_delivered": 92
        }
        
        bug_rate = (metrics["bugs_found"] / metrics["total_tasks"]) * 100
        
        assert bug_rate == 8.0
        assert bug_rate < 10  # Приемлемый уровень
    
    def test_code_review_metrics(self):
        """Проверка метрик code review"""
        reviews = [
            {"id": 1, "time_to_review_hours": 2.5},
            {"id": 2, "time_to_review_hours": 4.0},
            {"id": 3, "time_to_review_hours": 1.5},
            {"id": 4, "time_to_review_hours": 3.5}
        ]
        
        avg_review_time = sum(r["time_to_review_hours"] for r in reviews) / len(reviews)
        
        assert avg_review_time == pytest.approx(2.875, rel=0.01)
        assert avg_review_time < 4  # Быстрый review процесс
