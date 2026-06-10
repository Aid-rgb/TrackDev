# Шпаргалка по тестам - Что они делают

## Сейчас в CI/CD работают 4 теста из 2 файлов

### Файл: `test_main.py` (3 теста)

#### Тест 1: `test_health_check`
```python
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
```

**Простыми словами:**
1. Стучимся на endpoint `/health`
2. Проверяем что ответ = 200 (OK)
3. Проверяем что в JSON написано `{"status": "healthy"}`

**Зачем нужен:**
- В production по этому endpoint мониторинг проверяет жив ли сервер
- Если вернет не 200 или не `healthy` → алерт что сервер упал

---

#### Тест 2: `test_docs_accessible`
```python
def test_docs_accessible(client):
    response = client.get("/docs")
    assert response.status_code == 200
```

**Простыми словами:**
1. Идем на `/docs` (Swagger документация API)
2. Проверяем что страница открылась (200)

**Зачем нужен:**
- FastAPI автоматом генерирует документацию
- Проверяем что она не сломалась
- Разработчики используют /docs чтобы смотреть какие endpoints есть

---

#### Тест 3: `test_openapi_json`
```python
def test_openapi_json(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
```

**Простыми словами:**
1. Запрашиваем `/openapi.json` - схема API в формате OpenAPI
2. Проверяем что получили валидный JSON
3. Проверяем что там есть обязательные поля: "openapi" и "info"

**Зачем нужен:**
- OpenAPI схема используется для автогенерации клиентов
- Если схема невалидная → другие сервисы не смогут работать с API

---

### Файл: `test_config.py` (1 тест)

#### Тест 4: `test_test_mode`
```python
def test_test_mode():
    assert os.getenv("TESTING") == "1"
```

**Простыми словами:**
1. Проверяем переменную окружения `TESTING`
2. Она должна быть равна "1"

**Зачем нужен:**
- Убедиться что тесты запускаются в тестовом режиме
- Приложение может вести себя по-разному в тестах (например не слать реальные email)
- В `conftest.py` мы устанавливаем `os.environ["TESTING"] = "1"`

---

## Что происходит когда запускаешь pytest

### Команда:
```bash
cd backend
pytest
```

### Что делает pytest:

1. **Ищет файлы** `test_*.py` в папке `tests/`
   - Находит: `test_main.py`, `test_config.py`

2. **Ищет функции** начинающиеся с `test_` в этих файлах
   - Находит 4 функции: `test_health_check`, `test_docs_accessible`, `test_openapi_json`, `test_test_mode`

3. **Читает conftest.py**
   - Загружает fixtures: `client`, `test_api_key`, `auth_headers`

4. **Запускает каждый тест**
   - Если все `assert` проходят → тест ✅ PASSED
   - Если хотя бы один `assert` падает → тест ❌ FAILED

5. **Выводит результат**
   ```
   test_main.py::test_health_check PASSED
   test_main.py::test_docs_accessible PASSED
   test_main.py::test_openapi_json PASSED
   test_config.py::test_test_mode PASSED
   
   ======================== 4 passed in 0.52s ========================
   ```

---

## Что происходит в CI/CD (GitHub Actions)

### Workflow: `.github/workflows/backend-ci.yml`

Когда ты делаешь `git push`:

1. **GitHub Actions запускает виртуальную машину** (Ubuntu)

2. **Устанавливает Python 3.9, 3.10, 3.11** (matrix - 3 версии параллельно)

3. **Клонирует твой репозиторий**
   ```bash
   git clone https://github.com/Aid-rgb/TrackDev.git
   ```

4. **Устанавливает зависимости**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. **Создает тестовый .env файл**
   ```bash
   echo "TESTING=1" > .env
   echo "DATABASE_URL=..." >> .env
   # и т.д.
   ```

6. **Запускает линтеры** (проверка стиля кода)
   ```bash
   black --check .      # Проверка форматирования
   isort --check .      # Проверка импортов
   flake8 .             # Проверка ошибок
   ```

7. **Запускает тесты**
   ```bash
   pytest tests/ -v
   ```
   - Запускает все 4 теста
   - Если хотя бы 1 падает → весь CI падает ❌
   - Если все проходят → CI проходит ✅

8. **Если CI прошел** → можно мержить PR в main

---

## Разбор каждого теста - Построчно

### test_health_check

```python
def test_health_check(client):           # 1. Функция получает client из fixture
    response = client.get("/health")     # 2. Делаем GET запрос
    assert response.status_code == 200   # 3. Проверяем статус = 200
    data = response.json()               # 4. Парсим JSON из ответа
    assert data["status"] == "healthy"   # 5. Проверяем поле status
```

**Что проверяется:**
- ✅ Endpoint `/health` существует
- ✅ Возвращает HTTP 200
- ✅ Возвращает JSON
- ✅ В JSON есть поле `status` со значением `"healthy"`

**Что НЕ проверяется:**
- ❌ Не проверяет реальную БД
- ❌ Не проверяет Redmine API
- ❌ Не проверяет Telegram bot

**Если сломается:**
- Кто-то удалил endpoint `/health` из `main.py`
- Кто-то поменял формат ответа (например `{"state": "ok"}` вместо `{"status": "healthy"}`)

---

### test_docs_accessible

```python
def test_docs_accessible(client):       # 1. Получаем client
    response = client.get("/docs")      # 2. GET на /docs
    assert response.status_code == 200  # 3. Проверяем 200
```

**Что проверяется:**
- ✅ Swagger UI доступен

**Если сломается:**
- FastAPI не настроен правильно
- Кто-то отключил docs (`docs_url=None`)

---

### test_openapi_json

```python
def test_openapi_json(client):          # 1. Получаем client
    response = client.get("/openapi.json")  # 2. GET схему
    assert response.status_code == 200  # 3. Проверяем 200
    data = response.json()              # 4. Парсим JSON
    assert "openapi" in data            # 5. Есть поле "openapi"
    assert "info" in data               # 6. Есть поле "info"
```

**Что проверяется:**
- ✅ OpenAPI схема генерируется
- ✅ Содержит обязательные поля

**Если сломается:**
- FastAPI не может сгенерировать схему
- Неправильная конфигурация API

---

### test_test_mode

```python
def test_test_mode():                   # 1. Без параметров
    assert os.getenv("TESTING") == "1"  # 2. Проверяем переменную
```

**Что проверяется:**
- ✅ Переменная `TESTING=1` установлена

**Если сломается:**
- `conftest.py` не загрузился
- Кто-то удалил `os.environ["TESTING"] = "1"` из conftest

---

## Как понять что тест делает - Алгоритм

### 1. Посмотри на имя
```python
test_health_check    # Проверяет health endpoint
test_docs_accessible # Проверяет доступность docs
test_user_login      # Проверяет логин пользователя
```

### 2. Посмотри на параметры
```python
def test_something(client):         # Использует HTTP клиент
def test_something(auth_headers):   # Использует авторизацию
def test_something():               # Просто логика, без HTTP
```

### 3. Посмотри на asserts
```python
assert response.status_code == 200   # Проверяет HTTP статус
assert data["key"] == "value"        # Проверяет содержимое
assert len(items) > 0                # Проверяет количество
```

### 4. Посмотри на моки (если есть)
```python
@patch('app.services.get_data')      # Подменяет функцию get_data
def test_something(mock_get_data):
    mock_get_data.return_value = {}  # Что вернет функция
```

---

## Практика - Попробуй сам

### Задание 1: Запусти тесты локально

```bash
cd backend
pytest -v
```

Ожидаемый вывод:
```
tests/test_main.py::test_health_check PASSED
tests/test_main.py::test_docs_accessible PASSED
tests/test_main.py::test_openapi_json PASSED
tests/test_config.py::test_test_mode PASSED

====== 4 passed in 0.52s ======
```

### Задание 2: Сломай тест

Открой `backend/main.py` и найди:
```python
@app.get("/health")
def health():
    return {"status": "healthy"}
```

Измени на:
```python
@app.get("/health")
def health():
    return {"status": "broken"}
```

Запусти тесты:
```bash
pytest tests/test_main.py::test_health_check -v
```

Результат:
```
FAILED tests/test_main.py::test_health_check
AssertionError: assert 'broken' == 'healthy'
```

Верни обратно:
```python
return {"status": "healthy"}
```

### Задание 3: Напиши свой тест

Создай `backend/tests/test_my.py`:

```python
def test_math():
    """Мой первый тест"""
    result = 2 + 2
    assert result == 4
    
def test_string():
    """Проверка строк"""
    text = "hello world"
    assert "hello" in text
    assert text.startswith("hello")
    assert text.endswith("world")
```

Запусти:
```bash
pytest tests/test_my.py -v
```

### Задание 4: Тест для нового endpoint

Добавь в `backend/main.py`:
```python
@app.get("/api/test")
def test_endpoint():
    return {"message": "test successful", "code": 42}
```

Добавь в `backend/tests/test_main.py`:
```python
def test_test_endpoint(client):
    """Проверка тестового endpoint"""
    response = client.get("/api/test")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "test successful"
    assert data["code"] == 42
```

Запусти:
```bash
pytest tests/test_main.py::test_test_endpoint -v
```

---

## Частые вопросы

### Q: Зачем тесты если можно проверить руками в браузере?
**A:** 
- Тесты быстрее (секунды вместо минут)
- Тесты проверяют ВСЕ каждый раз
- Тесты не забывают проверить что-то
- Тесты можно запускать автоматически в CI/CD

### Q: Почему тест прошел локально но упал в CI?
**A:**
- Разные версии Python (CI тестирует на 3.9, 3.10, 3.11)
- Разные переменные окружения
- Разные зависимости

### Q: Нужно ли 100% coverage?
**A:** Нет. 70-80% достаточно. Важнее покрыть критичные части.

### Q: Что делать если тест падает?
**A:**
1. Прочитай ошибку
2. Запусти тест локально
3. Добавь `print()` чтобы понять что происходит
4. Проверь что код делает то что должен

---

## Резюме - Что ты должен понимать

✅ **Assert** - проверяет условие, если False → тест падает  
✅ **Fixture** - переиспользуемый код для тестов  
✅ **TestClient** - фейковый HTTP клиент для тестирования API  
✅ **Mock** - подмена реальных функций на фейковые  
✅ **CI/CD** - автоматический запуск тестов при push  

✅ **test_health_check** - проверяет что `/health` работает  
✅ **test_docs_accessible** - проверяет что `/docs` работает  
✅ **test_openapi_json** - проверяет что OpenAPI схема валидная  
✅ **test_test_mode** - проверяет что `TESTING=1`  

✅ Как запустить: `pytest`  
✅ Как запустить один тест: `pytest tests/test_main.py::test_health_check`  
✅ Как сломать тест и починить обратно  
✅ Как написать свой простой тест  

Если понимаешь это - ты готов объяснить проверяющему! 💪
