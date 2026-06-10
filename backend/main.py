from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers.api import router
# Импорт новых модульных роутеров метрик
from app.routers.metrics_health import router as health_router
from app.routers.metrics_workload import router as workload_router
from app.routers.metrics_deadlines import router as deadlines_router
from app.routers.metrics_planning import router as planning_router
from app.routers.metrics_quality import router as quality_router
from app.core.config import REDMINE_URL
from app.core.auth import api_key_middleware, get_api_key_scheme
from app.core.logging_config import setup_logging
from app.integrations.redmine_client import close_redmine_client
import logging
import os

# Настраиваем логирование при старте приложения
setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Redmine API & Metrics",
    description="REST API для Redmine с метриками для руководства",
    version="3.0.0"
)

logger.info("FastAPI application initialized", extra={
    "title": app.title,
    "version": app.version
})

# Добавляем middleware в правильном порядке
app.middleware("http")(api_key_middleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Добавляем зависимость безопасности для документации
api_key_scheme = get_api_key_scheme()

# Подключаем роутеры
app.include_router(router, dependencies=[Depends(api_key_scheme)])
app.include_router(health_router, dependencies=[Depends(api_key_scheme)])
app.include_router(workload_router, dependencies=[Depends(api_key_scheme)])
app.include_router(deadlines_router, dependencies=[Depends(api_key_scheme)])
app.include_router(planning_router, dependencies=[Depends(api_key_scheme)])
app.include_router(quality_router, dependencies=[Depends(api_key_scheme)])

# Монтируем статические файлы старого фронтенда, если они есть
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
static_dir = os.path.join(frontend_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Монтируем файлы нового React приложения
react_static_dir = os.path.join(os.path.dirname(__file__), "static-react")
if os.path.exists(react_static_dir):
    # Монтируем assets отдельно, так как они нужны для работы index.html
    assets_dir = os.path.join(react_static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="react-assets")


@app.on_event("startup")
async def startup_event():
    """Инициализация при старте приложения"""
    logger.info("Application startup", extra={
        "redmine_url": REDMINE_URL,
        "static_dirs_mounted": os.path.exists(react_static_dir)
    })


@app.on_event("shutdown")
async def shutdown_event():
    """Закрываем HTTP клиент при остановке приложения"""
    logger.info("Application shutdown initiated")
    await close_redmine_client()
    logger.info("Application shutdown completed")


@app.get("/")
def root():
    """Главная страница - Новый React дашборд"""
    logger.debug("Root endpoint accessed")
    react_index = os.path.join(os.path.dirname(__file__), "static-react", "index.html")
    if os.path.exists(react_index):
        return FileResponse(react_index)
    
    # Fallback на старый фронтенд
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    index_path = os.path.join(frontend_dir, "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # Fallback - информация об API
    return {"status": "ok", "redmine": REDMINE_URL, "docs": "/docs"}

@app.get("/dashboard")
def dashboard():
    """Дашборд метрик - доступен через Telegram Web App (алиас для /)"""
    return root()

@app.get("/old-dashboard")
def old_dashboard():
    """Старый дашборд для сравнения"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Old dashboard not found"}

@app.get("/health")
def health():
    """Health check endpoint"""
    logger.debug("Health check accessed")
    return {"status": "healthy"}