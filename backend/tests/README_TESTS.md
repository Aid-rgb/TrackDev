# Как писать автотесты - Простое объяснение

## Что такое автотесты?

Автотесты - это программы которые проверяют твою программу. Вместо того чтобы вручную открывать браузер и кликать кнопки, тесты делают это автоматически.

## Структура теста

```python
def test_что_проверяем():
    # 1. Подготовка (Arrange)
    client = TestClient(app)
    
    # 2. Действие (Act)
    response = client.get("/health")
    
    # 3. Проверка (Assert)
    assert response.status_code == 200
```

---

## Основные концепции

### 1. Assert (Утверждение)

`assert` - ключевое слово Python. Если условие **True** → тест проходит ✅. Если **False** → тест падает ❌.

```python
# Примеры assert
assert 2 + 2 == 4           # ✅ Проходит (True)
assert 2 + 2 == 5           # ❌ Падает (False)

assert "hello" in "hello world"  # ✅ Проходит
assert "bye" in "hello world"    # ❌ Падает

# В тестах API
assert response.status_code == 200  # Проверяем статус код
assert data["status"] == "healthy"  # Проверяем содержимое
```

### 2. Fixtures (Фикстуры)

Фикстура = переиспользуемый кусок кода для тестов.

**Без фикстуры (плохо - дублирование):**
```python
def test_endpoint_1():
    app = FastAPI()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200

def test_endpoint_2():
    app = FastAPI()
    client = TestClient(app)  # Повторяем код!
    response = client.get("/docs")
    assert response.status_code == 200
```

**С фикстурой (хорошо - переиспользуем):**
```python
@pytest.fixture
def client():
    app = FastAPI()
    return TestClient(app)

def test_endpoint_1(client):  # client приходит из фикстуры
    response = client.get("/health")
    assert response.status_code == 200

def test_endpoint_2(client):  # Переиспользуем!
    response = client.get("/docs")
    assert response.status_code == 200
```

### 3. TestClient

`TestClient` - это фейковый HTTP клиент для тестирования API без запуска реального сервера.

```python
from fastapi.testclient import TestClient

client = TestClient(app)

# Можем делать запросы как к настоящему серверу
response = client.get("/health")
response = client.post("/api/data", json={"key": "value"})
response = client.put("/api/update/1")
response = client.delete("/api/delete/1")
```

---

## Примеры тестов

### Пример 1: Простейший тест

```python
def test_addition():
    """Проверка что 2+2=4"""
    result = 2 + 2
    assert result == 4
```

**Что происходит:**
1. Считаем 2+2
2. Проверяем что результат = 4
3. Если да → тест прошел ✅

### Пример 2: Тест API endpoint

```python
def test_health_endpoint(client):
    """Проверка /health endpoint"""
    # Делаем GET запрос
    response = client.get("/health")
    
    # Проверяем статус код
    assert response.status_code == 200
    
    # Получаем JSON
    data = response.json()
    
    # Проверяем содержимое
    assert data["status"] == "healthy"
```

**Что происходит:**
1. Отправляем GET на `/health`
2. Проверяем что сервер ответил 200 (OK)
3. Парсим JSON ответ
4. Проверяем что в ответе `{"status": "healthy"}`

### Пример 3: Тест с авторизацией

```python
def test_protected_endpoint(client, auth_headers):
    """Проверка защищенного endpoint"""
    # Запрос С авторизацией
    response = client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    
    # Запрос БЕЗ авторизации
    response = client.get("/api/v1/projects")
    assert response.status_code in [401, 403]  # Unauthorized или Forbidden
```

**Что происходит:**
1. Первый запрос с header `X-API-Key: test_key` → должен пройти
2. Второй запрос без header → должен быть отклонен (401 или 403)

### Пример 4: Тест с проверкой данных

```python
def test_get_user(client):
    """Проверка получения пользователя"""
    response = client.get("/api/users/1")
    
    assert response.status_code == 200
    
    user = response.json()
    assert "id" in user
    assert "name" in user
    assert "email" in user
    
    assert user["id"] == 1
    assert isinstance(user["name"], str)  # Проверяем тип
    assert "@" in user["email"]           # Email содержит @
```

### Пример 5: Тест POST запроса

```python
def test_create_user(client):
    """Проверка создания пользователя"""
    # Данные для создания
    new_user = {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    }
    
    # POST запрос
    response = client.post("/api/users", json=new_user)
    
    # Проверяем что создано (201 Created)
    assert response.status_code == 201
    
    # Проверяем что вернулся созданный пользователь
    created = response.json()
    assert created["name"] == "John Doe"
    assert created["email"] == "john@example.com"
    assert "id" in created  # Сервер должен присвоить ID
```

---

## Моки (Mocks) - Подмена функций

Иногда нужно подменить реальную функцию на фейковую.

### Зачем?
- Не делать реальные запросы к внешним API
- Не изменять реальную БД
- Контролировать что возвращает функция

### Пример без мока (плохо)

```python
def test_get_weather():
    # Делает РЕАЛЬНЫЙ запрос к API погоды
    weather = get_weather_from_api("Moscow")
    assert weather["temp"] > -50
```

**Проблемы:**
- Зависит от интернета
- Зависит от работы внешнего API
- Медленно
- Может изменяться (погода меняется!)

### Пример с моком (хорошо)

```python
from unittest.mock import patch

@patch('app.services.get_weather_from_api')
def test_get_weather(mock_weather):
    # Настраиваем что вернет мок
    mock_weather.return_value = {
        "city": "Moscow",
        "temp": 15,
        "condition": "sunny"
    }
    
    # Вызываем функцию (она получит фейковые данные)
    weather = get_weather_from_api("Moscow")
    
    # Проверяем
    assert weather["temp"] == 15
    assert weather["city"] == "Moscow"
```

**Что происходит:**
1. `@patch` заменяет функцию `get_weather_from_api` на мок
2. `mock_weather.return_value` = что вернет функция
3. Когда код вызывает `get_weather_from_api()` → получает фейковые данные
4. Тест проверяет что код правильно обрабатывает эти данные

### Еще пример мока - Redmine API

```python
@patch('app.integrations.redmine_client.get_redmine_data')
def test_get_projects(mock_redmine, client, auth_headers):
    # Настраиваем фейковый ответ от Redmine
    mock_redmine.return_value = {
        "projects": [
            {"id": 1, "name": "Project Alpha"},
            {"id": 2, "name": "Project Beta"}
        ]
    }
    
    # Делаем запрос к нашему API
    response = client.get("/api/v1/projects", headers=auth_headers)
    
    # Проверяем что наш API правильно обработал данные
    assert response.status_code == 200
    data = response.json()
    assert len(data["projects"]) == 2
```

---

## Как запускать тесты

### Все тесты
```bash
cd backend
pytest
```

### С подробным выводом
```bash
pytest -v
```
Покажет какие тесты проходят/падают

### Один конкретный файл
```bash
pytest tests/test_main.py
```

### Один конкретный тест
```bash
pytest tests/test_main.py::test_health_check
```

### С покрытием кода
```bash
pytest --cov=app
```
Покажет сколько процентов кода покрыто тестами

---

## Структура наших тестов

```
backend/tests/
│
├── conftest.py                    # Настройки pytest и fixtures
│   ├── client                     # Фикстура: тестовый HTTP клиент
│   ├── test_api_key              # Фикстура: "test_key"
│   └── auth_headers              # Фикстура: {"X-API-Key": "test_key"}
│
├── test_main.py                   # Тесты основных endpoints
│   ├── test_health_check         # Проверка /health
│   ├── test_docs_accessible      # Проверка /docs
│   └── test_openapi_json         # Проверка /openapi.json
│
├── test_config.py                 # Тесты конфигурации
│   └── test_test_mode            # Проверка TESTING=1
│
├── test_api_endpoints.py          # Тесты API endpoints (новый)
│   ├── TestProjectsAPI
│   │   ├── test_get_projects_requires_auth
│   │   ├── test_get_projects_with_auth
│   │   └── test_get_project_by_id
│   ├── TestIssuesAPI
│   │   └── test_get_issues
│   └── TestAuthMiddleware
│       ├── test_missing_api_key
│       ├── test_invalid_api_key
│       └── test_health_endpoint_no_auth
│
├── test_metrics.py                # Тесты метрик (новый)
│   ├── TestHealthMetrics
│   ├── TestWorkloadMetrics
│   ├── TestDeadlineMetrics
│   ├── TestPlanningMetrics
│   └── TestQualityMetrics
│
├── test_services.py               # Тесты бизнес-логики (новый)
│   ├── TestHealthService
│   ├── TestWorkloadService
│   ├── TestDeadlineService
│   ├── TestPlanningService
│   └── TestQualityService
│
└── test_redmine_integration.py    # Тесты Redmine API (новый)
    ├── TestRedmineClient
    ├── TestRedmineDataTransformation
    └── TestRedmineProjects
```

---

## Что проверяют старые тесты (которые работают в CI)

### 1. conftest.py
**Роль:** Настройки для всех тестов
- Добавляет backend в путь импорта
- Устанавливает `TESTING=1`
- Создает fixtures (client, test_api_key, auth_headers)

### 2. test_main.py (3 теста)
**Что проверяют:**
- ✅ `/health` возвращает 200 и `{"status": "healthy"}`
- ✅ `/docs` доступен (Swagger UI)
- ✅ `/openapi.json` возвращает валидную OpenAPI схему

**Запускаются в CI:** Да, в `backend-ci.yml`

### 3. test_config.py (1 тест)
**Что проверяет:**
- ✅ Переменная `TESTING=1` установлена

**Запускаются в CI:** Да

---

## Как написать свой тест - Пошагово

### Шаг 1: Создай файл test_*.py

```bash
touch backend/tests/test_my_feature.py
```

### Шаг 2: Импортируй pytest

```python
import pytest
```

### Шаг 3: Напиши функцию test_*

```python
def test_my_function():
    # Твой код
    result = 2 + 2
    assert result == 4
```

### Шаг 4: Запусти тест

```bash
pytest tests/test_my_feature.py
```

### Пример - Тест для нового endpoint

```python
# backend/tests/test_my_api.py

def test_get_users(client, auth_headers):
    """Проверка получения списка пользователей"""
    
    # 1. Делаем запрос
    response = client.get("/api/v1/users", headers=auth_headers)
    
    # 2. Проверяем статус
    assert response.status_code == 200
    
    # 3. Проверяем структуру ответа
    data = response.json()
    assert "users" in data
    assert isinstance(data["users"], list)
```

---

## Частые ошибки

### 1. Забыл импортировать pytest
```python
# ❌ Неправильно
def test_something():
    assert True

# ✅ Правильно
import pytest

def test_something():
    assert True
```

### 2. Неправильное имя функции
```python
# ❌ Неправильно (pytest не найдет)
def check_health():
    assert True

# ✅ Правильно (начинается с test_)
def test_health():
    assert True
```

### 3. Забыл добавить client в параметры
```python
# ❌ Неправильно
def test_endpoint():
    response = client.get("/health")  # client не определен!

# ✅ Правильно
def test_endpoint(client):
    response = client.get("/health")
```

### 4. Неправильный assert
```python
# ❌ Неправильно (сравниваем response с 200)
response = client.get("/health")
assert response == 200

# ✅ Правильно (проверяем status_code)
response = client.get("/health")
assert response.status_code == 200
```

---

## Проверка понимания

Попробуй ответить:

1. **Что делает assert?**
   - Проверяет условие. Если True → тест проходит, если False → падает

2. **Зачем нужны fixtures?**
   - Переиспользовать код в разных тестах

3. **Что делает TestClient?**
   - Создает фейковый HTTP клиент для тестирования API

4. **Зачем нужны моки?**
   - Подменять реальные функции на фейковые в тестах

5. **Как запустить все тесты?**
   - `pytest`

6. **Как запустить один тест?**
   - `pytest tests/test_main.py::test_health_check`

---

## Что дальше?

1. ✅ Прочитай этот файл
2. ✅ Посмотри на тесты в test_main.py
3. ✅ Запусти тесты локально: `cd backend && pytest -v`
4. ✅ Измени один тест и посмотри как он падает
5. ✅ Напиши свой простой тест
6. ✅ Добавь новый endpoint в main.py и напиши тест для него

Удачи! 🚀
