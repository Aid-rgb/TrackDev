"""
Pydantic схемы для валидации данных
Схемы для всех метрик и ответов API
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


# ============================================
# БАЗОВЫЕ СХЕМЫ
# ============================================

class ProjectBase(BaseModel):
    """Базовая схема проекта"""
    id: int
    name: str
    identifier: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None
    is_public: Optional[bool] = None
    created_on: Optional[str] = None
    updated_on: Optional[str] = None


class ProjectsListResponse(BaseModel):
    """Список проектов"""
    total: int = Field(..., ge=0, description="Количество проектов")
    projects: List[Dict[str, Any]] = Field(..., description="Список проектов")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "projects": [
                    {"id": 1, "name": "Project A"},
                    {"id": 2, "name": "Project B"}
                ]
            }
        }


class ProjectDetailResponse(BaseModel):
    """Детальная информация о проекте"""
    project: Dict[str, Any] = Field(..., description="Информация о проекте")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project": {
                    "id": 1,
                    "name": "Project A",
                    "identifier": "project-a",
                    "description": "Project description"
                }
            }
        }


class HealthStatus(str, Enum):
    """Статусы здоровья проекта"""
    EXCELLENT = "excellent"
    WARNING = "warning"
    CRITICAL = "critical"


class PeriodType(str, Enum):
    """Типы периодов для метрик"""
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


# ============================================
# HEALTH METRICS
# ============================================

class HealthScoreResponse(BaseModel):
    """Схема ответа индекса здоровья проекта"""
    score: float = Field(..., ge=0, le=100, description="Индекс здоровья от 0 до 100")
    status: HealthStatus = Field(..., description="Статус проекта")
    status_text: str = Field(..., description="Текстовое описание статуса")
    factors: List[str] = Field(default_factory=list, description="Факторы, влияющие на здоровье")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации по улучшению")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 85.5,
                "status": "excellent",
                "status_text": "🟢 Проект под контролем",
                "factors": [],
                "recommendations": ["Продолжайте в том же духе"]
            }
        }


# ============================================
# WORKLOAD METRICS
# ============================================

class BacklogResponse(BaseModel):
    """Бэклог: открытые задачи"""
    total: int = Field(..., ge=0, description="Общее количество открытых задач")
    open: int = Field(..., ge=0, description="Новые задачи")
    in_progress: int = Field(..., ge=0, description="Задачи в работе")
    by_status: Dict[str, int] = Field(default_factory=dict, description="Распределение по статусам")
    by_priority: Dict[str, int] = Field(default_factory=dict, description="Распределение по приоритетам")


class BacklogChangeResponse(BaseModel):
    """Изменение бэклога за период"""
    new_tasks: int = Field(..., ge=0, description="Новые задачи")
    closed_tasks: int = Field(..., ge=0, description="Закрытые задачи")
    change: int = Field(..., description="Изменение (+ рост, - снижение)")
    trend: str = Field(..., description="Тренд: increasing/decreasing/stable")


class InflowRatioResponse(BaseModel):
    """Коэффициент притока задач"""
    new_tasks: int = Field(..., ge=0)
    closed_tasks: int = Field(..., ge=0)
    ratio: float = Field(..., description="Отношение новых к закрытым")
    interpretation: str = Field(..., description="Интерпретация коэффициента")


class VelocityResponse(BaseModel):
    """Скорость выполнения задач"""
    total_closed: int = Field(..., ge=0, description="Всего закрыто задач")
    closed_per_day: Dict[str, int] = Field(default_factory=dict, description="По дням")
    by_week: Dict[str, int] = Field(default_factory=dict, description="По неделям")
    avg_per_day: float = Field(..., ge=0, description="Средняя скорость в день")


class OldTasksResponse(BaseModel):
    """Статистика старых задач"""
    total_open: int = Field(..., ge=0, description="Всего открытых задач")
    older_30_days: int = Field(..., ge=0, description="Старше 30 дней")
    older_90_days: int = Field(..., ge=0, description="Старше 90 дней")
    older_180_days: int = Field(..., ge=0, description="Старше 180 дней")


# ============================================
# DEADLINE METRICS
# ============================================

class OnTimeCompletionResponse(BaseModel):
    """Выполнение в срок"""
    total_with_due_date: int = Field(..., ge=0, description="Задач со сроком")
    on_time: int = Field(..., ge=0, description="Выполнено в срок")
    late: int = Field(..., ge=0, description="Выполнено с опозданием")
    on_time_percent: float = Field(..., ge=0, le=100, description="Процент в срок")


class OverdueTasksResponse(BaseModel):
    """Просроченные задачи"""
    total: int = Field(..., ge=0, description="Всего просроченных")
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="Список задач")
    by_priority: Dict[str, int] = Field(default_factory=dict, description="По приоритетам")
    avg_overdue_days: float = Field(..., ge=0, description="Средняя просрочка в днях")


class LeadTimeResponse(BaseModel):
    """Время выполнения задачи"""
    avg_days: float = Field(..., ge=0, description="Среднее время в днях")
    median_days: float = Field(..., ge=0, description="Медианное время")
    total_analyzed: int = Field(..., ge=0, description="Проанализировано задач")


# ============================================
# PLANNING METRICS
# ============================================

class TimeTrackingResponse(BaseModel):
    """Статистика по времени"""
    total_hours: float = Field(..., ge=0, description="Всего часов")
    avg_hours_per_day: float = Field(..., ge=0, description="Среднее в день")
    by_activity: Dict[str, float] = Field(default_factory=dict, description="По видам деятельности")
    by_tracker: Dict[str, float] = Field(default_factory=dict, description="По типам задач")
    by_priority: Dict[str, float] = Field(default_factory=dict, description="По приоритетам задач")
    user_detailed: List[Dict[str, Any]] = Field(default_factory=list, description="Детализация по пользователям")


class WorkloadDistributionResponse(BaseModel):
    """Распределение нагрузки"""
    total_users: int = Field(..., ge=0, description="Всего пользователей")
    workload: List[Dict[str, Any]] = Field(default_factory=list, description="Нагрузка по пользователям")


class EstimationAccuracyResponse(BaseModel):
    """Точность оценок"""
    total_analyzed: int = Field(..., ge=0, description="Проанализировано задач")
    accurate: int = Field(..., ge=0, description="Точные оценки (±20%)")
    underestimated: int = Field(..., ge=0, description="Недооценено")
    overestimated: int = Field(..., ge=0, description="Переоценено")
    accuracy_rate: float = Field(..., ge=0, le=100, description="Процент точности")
    avg_deviation_percent: float = Field(..., description="Среднее отклонение %")


class UnassignedTasksResponse(BaseModel):
    """Задачи без исполнителя"""
    total: int = Field(..., ge=0, description="Всего задач")
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="Список задач")


class TasksWithoutDueDateResponse(BaseModel):
    """Задачи без срока"""
    total: int = Field(..., ge=0, description="Всего задач")
    open: int = Field(..., ge=0, description="Открытых")
    in_progress: int = Field(..., ge=0, description="В работе")


# ============================================
# QUALITY METRICS
# ============================================

class BugRateResponse(BaseModel):
    """Доля ошибок"""
    total_tasks: int = Field(..., ge=0, description="Всего задач")
    bug_tasks: int = Field(..., ge=0, description="Багов")
    bug_rate_percent: float = Field(..., ge=0, le=100, description="Процент багов")


class BugMetricsResponse(BaseModel):
    """Метрики по багам"""
    new_bugs: int = Field(..., ge=0, description="Новые баги")
    closed_bugs: int = Field(..., ge=0, description="Закрытые баги")
    open_bugs: int = Field(..., ge=0, description="Открытые баги")
    by_priority: Dict[str, int] = Field(default_factory=dict, description="По приоритетам")


class BugFixRatioResponse(BaseModel):
    """Коэффициент устранения багов"""
    new_bugs: int = Field(..., ge=0)
    closed_bugs: int = Field(..., ge=0)
    ratio: float = Field(..., description="Отношение закрытых к новым")
    interpretation: str = Field(..., description="Интерпретация")


class ReopenedTasksResponse(BaseModel):
    """Переоткрытые задачи"""
    total_reopened: int = Field(..., ge=0, description="Всего переоткрытых")
    reopened_percent: float = Field(..., ge=0, le=100, description="Процент переоткрытых")
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="Список задач")


# ============================================
# DASHBOARD
# ============================================

class DashboardResponse(BaseModel):
    """Сводный дашборд со всеми метриками"""
    health_score: HealthScoreResponse
    workload: Dict[str, Any] = Field(default_factory=dict, description="Метрики нагрузки")
    deadlines: Dict[str, Any] = Field(default_factory=dict, description="Метрики сроков")
    planning: Dict[str, Any] = Field(default_factory=dict, description="Метрики планирования")
    quality: Dict[str, Any] = Field(default_factory=dict, description="Метрики качества")
    
    class Config:
        json_schema_extra = {
            "example": {
                "health_score": {
                    "score": 85.5,
                    "status": "excellent",
                    "status_text": "🟢 Проект под контролем",
                    "factors": [],
                    "recommendations": ["Продолжайте в том же духе"]
                },
                "workload": {"backlog": {"total": 50}},
                "deadlines": {},
                "planning": {},
                "quality": {}
            }
        }


# ============================================
# REQUEST SCHEMAS
# ============================================

class ProjectQueryParams(BaseModel):
    """Параметры запроса списка проектов"""
    limit: int = Field(default=100, ge=1, le=500, description="Максимум проектов")
    
    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v: int) -> int:
        if v > 500:
            raise ValueError('Limit cannot exceed 500')
        return v


class MetricQueryParams(BaseModel):
    """Параметры запроса метрик"""
    project_id: Optional[int] = Field(None, description="ID проекта (None = все проекты)")
    period: str = Field(default="month", description="Период: week/month/quarter/year/custom")
    
    @field_validator('period')
    @classmethod
    def validate_period(cls, v: str) -> str:
        # Поддержка кастомного периода: "2024-01-01|2024-12-31"
        if "|" in v:
            try:
                start, end = v.split("|")
                datetime.strptime(start, "%Y-%m-%d")
                datetime.strptime(end, "%Y-%m-%d")
                return v
            except ValueError:
                raise ValueError('Custom period must be in format: YYYY-MM-DD|YYYY-MM-DD')
        
        valid_periods = ["week", "month", "quarter", "year"]
        if v not in valid_periods:
            raise ValueError(f'Period must be one of: {", ".join(valid_periods)} or custom format')
        return v


# ============================================
# ERROR SCHEMAS
# ============================================

class ErrorResponse(BaseModel):
    """Стандартная схема ошибки"""
    error: str = Field(..., description="Тип ошибки")
    detail: str = Field(..., description="Детали ошибки")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время ошибки")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "detail": "Invalid project_id",
                "timestamp": "2024-01-01T12:00:00"
            }
        }
