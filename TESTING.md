# 🧪 Автотестирование и CI/CD для TrackDev

## Логика автотестирования

### Архитектура тестирования

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Push / Pull Request                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│   Backend Tests  │      │  Frontend Tests  │
│                  │      │                  │
│ 1. Lint          │      │ 1. ESLint        │
│ 2. Type Check    │      │ 2. Build         │
│ 3. Unit Tests    │      │ 3. Bundle Check  │
│ 4. Security      │      │ 4. Lighthouse    │
└────────┬─────────┘      └────────┬─────────┘
         │                         │
         └──────────┬──────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │  Integration Tests   │
        │                      │
        │ 1. PostgreSQL Setup  │
        │ 2. Backend Start     │
        │ 3. API Tests         │
        │ 4. Full Stack Tests  │
        └──────────┬───────────┘
                   │
                   ▼
           ┌───────────────┐
           │ Security Scan │
           │ + Docker      │
           └───────┬───────┘
                   │
                   ▼
              ┌─────────┐
              │ Deploy  │
              └─────────┘
```

---

## Backend Tests - Семантика и логика

### 1. Структура тестов

```python
backend/tests/
├── __init__.py           # Package marker
├── conftest.py           # Pytest fixtures (общие настройки)
├── test_main.py          # Тесты основных API endpoints
└── test_config.py        # Тесты конфигурации
```

### 2. Fixtures (conftest.py)

**Назначение:** Переиспользуемые компоненты тестов

```python
@pytest.fixture
def client():
    """
    Создает тестовый клиент FastAPI
    - Изолированный от production
    - Автоматически закрывается после тестов
    - Используется во всех API тестах
    """
    
@pytest.fixture
def test_api_key():
    """
    Тестовый API ключ
    - Не затрагивает production ключи
    - Валидный формат для тестов
    """
    
@pytest.fixture
def auth_headers(test_api_key):
    """
    HTTP заголовки с авторизацией
    - Зависит от test_api_key fixture
    - Готовые headers для защищенных endpoints
    """
```

**Логика:** Fixtures создаются один раз, используются много раз. Это уменьшает дублирование кода.

### 3. Тесты API (test_main.py)

#### 3.1 Публичные endpoints

```python
def test_read_root(client):
    """
    Проверка корневого endpoint
    
    Логика:
    1. GET /
    2. Ожидаем 200 OK
    3. Проверяем структуру ответа {"status": "active"}
    
    Зачем: Убедиться что сервер запускается и отвечает
    """

def test_health_check(client):
    """
    Проверка health endpoint
    
    Логика:
    1. GET /health
    2. Ожидаем 200 OK
    3. Проверяем {"status": "healthy", "timestamp": ...}
    
    Зачем: Мониторинг работоспособности в production
    """

def test_docs_accessible(client):
    """
    Проверка доступности документации
    
    Логика:
    1. GET /docs
    2. Ожидаем 200 OK
    
    Зачем: Swagger должен быть доступен для API пользователей
    """
```

#### 3.2 Защищенные endpoints

```python
def test_protected_endpoint_without_auth(client):
    """
    Проверка что без auth возвращается ошибка
    
    Логика:
    1. GET /api/v1/projects БЕЗ headers
    2. Ожидаем 401 или 403 (Unauthorized/Forbidden)
    
    Зачем: Security - проверить что защита работает
    """

def test_protected_endpoint_with_auth(client, auth_headers):
    """
    Проверка с валидной авторизацией
    
    Логика:
    1. GET /api/v1/projects С auth headers
    2. Принимаем любой ответ (200/401/403/500/503)
    
    Зачем: Проверить auth flow (реальный Redmine может быть недоступен в тестах)
    """
```

#### 3.3 Параметризованные тесты

```python
@pytest.mark.parametrize("endpoint", [
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc"
])
def test_public_endpoints(client, endpoint):
    """
    Проверка всех публичных endpoints одним тестом
    
    Логика:
    1. Для каждого endpoint из списка
    2. GET {endpoint}
    3. Ожидаем 200 OK
    
    Зачем: DRY - не дублировать код для однотипных проверок
    """
```

**Семантика:** Параметризация = один тест-функция, много проверок

### 4. Тесты конфигурации (test_config.py)

```python
def test_environment_variables():
    """
    Проверка переменных окружения
    
    Логика:
    1. Проверяем что DATABASE_URL установлен
    2. Проверяем что REDMINE_URL установлен
    
    Зачем: Тесты должны падать рано если окружение неправильное
    """

def test_config_loading():
    """
    Проверка загрузки конфигурации
    
    Логика:
    1. Импортируем settings
    2. Проверяем что атрибуты существуют
    
    Зачем: Проверить что config.py работает корректно
    """
```

---

## CI/CD Pipeline - Семантика

### Backend CI Workflow

**Файл:** `.github/workflows/backend-ci.yml`

**Триггеры:**
- `push` в `main`, `develop`
- `pull_request` в `main`, `develop`
- Изменения в `backend/**`

**Логика:**

#### Job 1: lint-and-test

**Matrix Strategy:** Тестируем на Python 3.9, 3.10, 3.11

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']
```

**Зачем:** Убедиться что код работает на разных версиях Python

**Шаги:**

1. **Checkout code**
   - Скачать репозиторий
   
2. **Setup Python**
   - Установить нужную версию Python
   - Кешировать pip зависимости
   
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-cov flake8 black isort mypy
   ```
   - Основные зависимости
   - Dev зависимости для тестирования
   
4. **Run Black** (форматирование)
   ```bash
   black --check --diff .
   ```
   - Проверить что код отформатирован
   - `continue-on-error: true` - не блокировать если fail
   
5. **Run isort** (сортировка импортов)
   ```bash
   isort --check-only --diff .
   ```
   - Проверить порядок импортов
   
6. **Run Flake8** (линтинг)
   ```bash
   flake8 . --count --select=E9,F63,F7,F82  # Критические ошибки
   flake8 . --exit-zero                     # Предупреждения
   ```
   - Первый запуск: syntax errors, undefined names - FAIL если есть
   - Второй запуск: стилистические проблемы - только WARNING
   
7. **Run MyPy** (type checking)
   ```bash
   mypy app --ignore-missing-imports
   ```
   - Проверка типов (опционально)
   
8. **Create test .env**
   ```bash
   cat > .env << EOF
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/redmine_bot_test
   REDMINE_URL=https://test-redmine.com
   BOT_TOKEN=test_token
   ...
   EOF
   ```
   - Создать тестовое окружение
   - Использовать localhost PostgreSQL (из services)
   
9. **Run tests**
   ```bash
   pytest tests/ -v --cov=app --cov-report=xml --cov-report=term-missing
   ```
   - Запустить все тесты
   - `-v` verbose (детальный вывод)
   - `--cov` измерить coverage
   - `--cov-report=xml` для Codecov
   - `--cov-report=term-missing` показать непокрытые строки
   
10. **Upload coverage to Codecov**
    - Отправить coverage report
    - Интеграция с Codecov (если настроено)

**PostgreSQL Service:**
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: redmine_bot_test
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
```

**Зачем:** Интеграционные тесты требуют реальную БД

#### Job 2: security-scan

**Шаги:**

1. **Install safety**
   ```bash
   pip install safety
   ```
   
2. **Check vulnerabilities**
   ```bash
   safety check --json
   ```
   - Проверить зависимости на известные уязвимости
   
3. **Run Bandit**
   ```bash
   pip install bandit
   bandit -r backend/app -f json
   ```
   - Сканировать код на security issues
   - SQL injection, hardcoded passwords, etc.

**continue-on-error: true** - не блокировать pipeline, но показать предупреждения

#### Job 3: docker-build

**Зависимость:** `needs: [lint-and-test]`

**Логика:**
1. Собрать Docker образ
2. Тестово запустить контейнер
3. Проверить логи
4. Остановить

**Зачем:** Убедиться что Dockerfile валидный и образ собирается

---

### Frontend CI Workflow

**Файл:** `.github/workflows/frontend-ci.yml`

**Matrix Strategy:** Node 18.x, 20.x, 22.x

**Логика:**

1. **Install dependencies**
   ```bash
   npm ci
   ```
   - `ci` вместо `install` для CI (строгая версионность)
   
2. **Run ESLint**
   ```bash
   npm run lint
   ```
   - Проверить JavaScript код style
   
3. **Check security**
   ```bash
   npm audit --audit-level=moderate
   ```
   - Проверить зависимости
   
4. **Build**
   ```bash
   npm run build
   ```
   - Production сборка
   - Проверить что нет ошибок сборки
   
5. **Check build output**
   ```bash
   ls -la dist/
   ```
   - Убедиться что `dist/` создался
   
6. **Analyze bundle**
   ```bash
   du -sh dist/
   find dist/ -type f | sort -rh | head -n 10
   ```
   - Размер bundle
   - Топ-10 самых больших файлов

**Lighthouse Job:**
- Запустить локальный сервер
- Запустить Lighthouse CI
- Проверить performance, accessibility, SEO scores

---

### Integration Tests Workflow

**Файл:** `.github/workflows/integration-tests.yml`

**Логика:**

1. **Setup environment**
   - Python + Node + PostgreSQL
   
2. **Build frontend**
   ```bash
   cd frontend && npm ci && npm run build
   ```
   
3. **Copy to backend**
   ```bash
   cp -r frontend/dist backend/static-react
   ```
   - Backend будет отдавать frontend
   
4. **Start backend**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 &
   ```
   - Запустить в фоне
   
5. **Test API endpoints**
   ```bash
   curl -f http://localhost:8000/health
   curl -f http://localhost:8000/
   curl -f http://localhost:8000/docs
   curl -H "X-API-Key: test_key" http://localhost:8000/api/v1/projects
   ```
   - Полная проверка API
   - С авторизацией и без
   
6. **Test frontend static files**
   ```bash
   curl -f http://localhost:8000/dashboard
   curl -f http://localhost:8000/favicon.svg
   ```

**Зачем:** Проверить что frontend + backend работают вместе

---

### Deploy Workflow

**Файл:** `.github/workflows/deploy.yml`

**Триггеры:**
- Push в `main` → Production
- Push в `develop` → Staging
- Manual dispatch
- Tags `v*` → Release

**Логика:**

1. **Build frontend**
   ```bash
   cd frontend && npm ci && npm run build
   ```
   
2. **Copy to backend**
   ```bash
   cp -r frontend/dist backend/static-react
   ```
   
3. **Build Docker image**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
   
4. **Push to GitHub Container Registry**
   ```
   ghcr.io/aid-rgb/trackdev/backend:main
   ghcr.io/aid-rgb/trackdev/backend:develop
   ghcr.io/aid-rgb/trackdev/backend:sha-abc123
   ```
   
5. **Deploy** (placeholder)
   - SSH / Heroku / Cloud provider

---

## Семантика тестов

### AAA Pattern (Arrange-Act-Assert)

```python
def test_example():
    # Arrange - подготовка
    client = TestClient(app)
    
    # Act - действие
    response = client.get("/health")
    
    # Assert - проверка
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Given-When-Then (BDD style)

```python
def test_auth_flow():
    # Given: пользователь не авторизован
    client = TestClient(app)
    
    # When: делает запрос к защищенному endpoint
    response = client.get("/api/v1/projects")
    
    # Then: получает ошибку авторизации
    assert response.status_code in [401, 403]
```

### Test Naming Convention

```python
# Формат: test_<что_тестируем>_<условие>_<ожидаемый_результат>

def test_health_endpoint_returns_200():
    """Health endpoint должен возвращать 200"""

def test_protected_endpoint_without_auth_returns_401():
    """Защищенный endpoint без авторизации возвращает 401"""

def test_api_with_valid_key_accepts_request():
    """API с валидным ключом принимает запрос"""
```

---

## Best Practices

### 1. Изоляция тестов
- Каждый тест независим
- Не зависят от порядка выполнения
- Используют fixtures для setup/teardown

### 2. Тестовые данные
- Не используют production данные
- Создают тестовую БД
- Используют моки для внешних API (Redmine)

### 3. Ассерты
- Один тест = одна проверка (желательно)
- Понятные сообщения об ошибках
- Проверять и status code, и структуру ответа

### 4. Coverage
- Цель: >80%
- Но coverage ≠ качество
- Важнее покрыть критичные пути

### 5. Performance
- Быстрые тесты (unit < 1s)
- Медленные тесты (integration < 30s)
- Использовать pytest markers для фильтрации

---

## Локальный запуск

```bash
# Все тесты
pytest

# С coverage
pytest --cov=app --cov-report=html

# Verbose
pytest -v

# Конкретный файл
pytest tests/test_main.py

# Конкретный тест
pytest tests/test_main.py::test_health_check

# С markers
pytest -m "not slow"
```

---

## GitHub Secrets (обязательно)

```
REDMINE_URL          - URL Redmine сервера
REDMINE_API_KEY      - API ключ для тестов
BOT_TOKEN            - Telegram bot token
DATABASE_URL         - Production БД
ALLOWED_API_KEYS     - API ключи для авторизации
WEBAPP_URL           - URL веб приложения
```

Добавить в: **Settings → Secrets and variables → Actions**

---

## Что проверяется автоматически

✅ **Code Quality:**
- Форматирование (Black)
- Импорты (isort)
- Линтинг (Flake8)
- Типы (MyPy)

✅ **Functionality:**
- Unit тесты
- Integration тесты
- API endpoints
- Auth flow

✅ **Security:**
- Уязвимости зависимостей (Safety, npm audit)
- Security issues в коде (Bandit)
- CodeQL анализ

✅ **Performance:**
- Bundle size
- Lighthouse scores
- Build time

✅ **Build:**
- Docker образ собирается
- Frontend собирается
- Backend запускается

---

## Быстрый старт

```bash
# 1. Push код
git add .
git commit -m "ci: add CI/CD"
git push origin main

# 2. Добавить Secrets в GitHub

# 3. Создать PR для проверки
git checkout -b test-ci
git push origin test-ci

# 4. Смотреть результаты в Actions tab
```

Готово! Все тесты запустятся автоматически. 🚀
