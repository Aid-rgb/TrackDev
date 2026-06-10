# 🚀 CI/CD Guide - TrackDev

## Что такое CI/CD?

**CI/CD** = Continuous Integration / Continuous Deployment

- **CI (Continuous Integration)** - автоматическая проверка кода при каждом push
- **CD (Continuous Deployment)** - автоматическое развертывание после успешных проверок

**Зачем это нужно?**
- ✅ Автоматически находит ошибки до попадания в production
- ✅ Гарантирует что код работает на всех версиях Python/Node
- ✅ Проверяет безопасность кода
- ✅ Экономит время на ручном тестировании

---

## 📁 Структура CI/CD

Все workflow файлы находятся в `.github/workflows/`:

```
.github/workflows/
├── backend-ci.yml           # Backend тестирование
├── frontend-ci.yml          # Frontend сборка и тесты
├── integration-tests.yml    # Полные интеграционные тесты
├── deploy.yml               # Автоматический деплой
├── pr-checks.yml            # Проверки Pull Request
├── codeql-analysis.yml      # Анализ безопасности кода
├── dependency-update.yml    # Мониторинг зависимостей
└── release.yml              # Управление релизами
```

---

## 🔄 Когда что запускается?

### При Push в main/develop:
```
✅ Backend CI
✅ Frontend CI
✅ Integration Tests
✅ CodeQL Security Analysis
✅ Deploy (только на main)
```

### При создании Pull Request:
```
✅ Backend CI
✅ Frontend CI
✅ Integration Tests
✅ PR Checks (заголовок, размер, commits)
✅ Security Scans
```

### По расписанию (каждый понедельник):
```
✅ Dependency Updates
✅ CodeQL Security Analysis
```

### При создании тега v*.*.*:
```
✅ Release workflow
✅ Build Docker images
✅ Create GitHub Release
```

---

## 📋 Подробное описание workflows

### 1. backend-ci.yml - Backend CI/CD

**Назначение:** Проверка Python кода backend'а

**Запускается:**
- Push в `main`, `develop`
- Pull Request в `main`, `develop`
- Изменения в `backend/**`

**Что делает:**

#### Job 1: lint-and-test
```yaml
Matrix: Python 3.9, 3.10, 3.11 (тестируем на 3 версиях)
Services: PostgreSQL 15 (для интеграционных тестов)
```

**Шаги:**
1. **Checkout code** - скачивает репозиторий
2. **Setup Python** - устанавливает нужную версию Python
3. **Install dependencies** - `pip install -r requirements.txt`
4. **Run Black** - проверяет форматирование кода
   ```bash
   black --check --diff .
   ```
5. **Run isort** - проверяет сортировку импортов
   ```bash
   isort --check-only --diff .
   ```
6. **Run Flake8** - линтинг (проверка стиля кода)
   ```bash
   flake8 . --count --select=E9,F63,F7,F82  # Критические ошибки
   flake8 . --exit-zero                     # Предупреждения
   ```
7. **Run MyPy** - проверка типов (опционально)
   ```bash
   mypy app --ignore-missing-imports
   ```
8. **Create test .env** - создает тестовое окружение
9. **Run tests** - запускает pytest с coverage
   ```bash
   pytest tests/ -v --cov=app --cov-report=xml
   ```
10. **Upload coverage** - отправляет coverage в Codecov

#### Job 2: security-scan
```yaml
Runs on: Ubuntu latest
```

**Шаги:**
1. **Safety check** - проверка уязвимостей в зависимостях
   ```bash
   safety check --json
   ```
2. **Bandit** - поиск security issues в коде
   ```bash
   bandit -r backend/app -f json
   ```

#### Job 3: docker-build
```yaml
Depends on: lint-and-test
```

**Шаги:**
1. **Build Docker image** - собирает образ
2. **Test Docker image** - тестовый запуск контейнера

**Время выполнения:** ~2-4 минуты

---

### 2. frontend-ci.yml - Frontend CI/CD

**Назначение:** Сборка и проверка React приложения

**Запускается:**
- Push в `main`, `develop`
- Pull Request в `main`, `develop`
- Изменения в `frontend/**`

**Что делает:**

#### Job 1: lint-and-build
```yaml
Matrix: Node.js 20.x, 22.x (2 версии)
```

**Шаги:**
1. **Checkout code**
2. **Setup Node.js** - устанавливает Node.js
3. **Install dependencies** - `npm install`
4. **Run ESLint** - проверяет JavaScript код
   ```bash
   npm run lint
   ```
5. **Security vulnerabilities** - проверяет npm пакеты
   ```bash
   npm audit --audit-level=moderate
   ```
6. **Build project** - собирает production build
   ```bash
   npm run build
   ```
7. **Check build output** - проверяет что dist создался
8. **Upload artifacts** - сохраняет build как artifact
9. **Analyze bundle size** - анализирует размер сборки

#### Job 2: lighthouse-audit (опционально)
```yaml
Depends on: lint-and-build
```

**Шаги:**
1. Запускает preview сервер
2. Проверяет performance, accessibility, SEO

#### Job 3: security-scan
**Шаги:**
1. **npm audit** - детальная проверка безопасности
2. Сохраняет результаты как artifact

**Время выполнения:** ~2-3 минуты

---

### 3. integration-tests.yml - Интеграционные тесты

**Назначение:** Тестирование полного стека (Backend + Frontend + Database)

**Запускается:**
- Push в `main`, `develop`
- Pull Request
- Manual dispatch (можно запустить вручную)

**Что делает:**

#### Job 1: integration-test
```yaml
Services: PostgreSQL 15
```

**Шаги:**
1. **Setup Python** (3.11)
2. **Setup Node.js** (20.x)
3. **Install backend dependencies**
4. **Install frontend dependencies**
5. **Build frontend** - `npm run build`
6. **Copy frontend to backend** - `cp -r frontend/dist backend/static-react`
7. **Create .env** - тестовые переменные окружения
8. **Start backend server** - `uvicorn main:app`
9. **Test API endpoints** - проверяет все endpoints
   ```bash
   curl -f http://localhost:8000/health
   curl -f http://localhost:8000/docs
   curl -f http://localhost:8000/api/v1/projects
   ```
10. **Test frontend static files** - проверяет отдачу фронта
11. **Stop backend server**

#### Job 2: e2e-test (placeholder)
```yaml
Depends on: integration-test
```

Подготовлен для E2E тестов с Playwright (опционально)

**Время выполнения:** ~1-2 минуты

---

### 4. deploy.yml - Deployment Pipeline

**Назначение:** Автоматическое развертывание на production/staging

**Запускается:**
- Push в `main` → Production
- Push в `develop` → Staging
- Manual dispatch (ручной запуск с выбором environment)
- Создание тега `v*` → Production release

**Что делает:**

#### Job 1: build-and-push-docker
```yaml
Permissions: write packages (для ghcr.io)
```

**Шаги:**
1. **Setup Docker Buildx**
2. **Login to GitHub Container Registry** - `ghcr.io`
3. **Extract metadata** - версия, теги
4. **Build frontend** - `npm run build`
5. **Copy frontend to backend**
6. **Build Docker image**
   - FROM python:3.11-slim
   - COPY requirements.txt & install
   - COPY app code
   - EXPOSE 8000
7. **Push to ghcr.io** с тегами:
   ```
   ghcr.io/aid-rgb/trackdev/backend:main
   ghcr.io/aid-rgb/trackdev/backend:sha-abc123
   ghcr.io/aid-rgb/trackdev/backend:v1.0.0
   ```

#### Job 2: deploy-to-staging
```yaml
Environment: staging
Depends on: build-and-push-docker
Runs if: branch == develop
```

#### Job 3: deploy-to-production
```yaml
Environment: production
Depends on: build-and-push-docker
Runs if: branch == main
```

**Примечание:** Deployment шаги нужно настроить под ваш сервер (SSH/Heroku/AWS/etc)

**Время выполнения:** ~3-5 минут

---

### 5. pr-checks.yml - Pull Request проверки

**Назначение:** Автоматическая проверка качества PR

**Запускается:**
- Создание PR
- Обновление PR

**Что делает:**

#### Job 1: pr-metadata
**Шаги:**
1. **Check PR title** - проверяет формат заголовка
   ```
   Правильно: feat: add new feature
   Неправильно: added new feature
   ```
   Использует Conventional Commits
   
2. **PR size check** - предупреждает о больших PR
   ```
   > 1000 строк → Warning: разбейте на меньшие PR
   ```

#### Job 2: validate-changes
**Шаги:**
1. **Get changed files** - определяет что изменилось
2. **Check if tests needed** - проверяет есть ли тесты
3. **Check for breaking changes** - ищет в описании PR

#### Job 3: lint-commit-messages
**Шаги:**
1. **Validate commits** - проверяет все commit messages
   ```bash
   npx commitlint --from BASE --to HEAD
   ```

#### Job 4: comment-summary
**Шаги:**
1. Добавляет автоматический комментарий в PR с результатами

**Время выполнения:** ~30 секунд

---

### 6. codeql-analysis.yml - Security Analysis

**Назначение:** Автоматический поиск уязвимостей в коде

**Запускается:**
- Push в `main`, `develop`
- Pull Request
- Weekly (каждый понедельник)

**Что делает:**

#### Job: analyze
```yaml
Matrix: 
  - language: python
  - language: javascript
```

**Шаги:**
1. **Initialize CodeQL** - инициализация для языка
2. **Autobuild** - автоматическая сборка проекта
3. **Perform CodeQL Analysis** - анализ кода
   - SQL injection
   - XSS vulnerabilities
   - Hardcoded secrets
   - Weak cryptography
   - И другие OWASP Top 10

**Результат:** Находит потенциальные уязвимости и создает Security Alerts

**Время выполнения:** ~3-5 минут

---

### 7. dependency-update.yml - Dependency Monitoring

**Назначение:** Еженедельная проверка зависимостей

**Запускается:**
- Weekly (понедельник, 00:00)
- Manual dispatch

**Что делает:**

#### Job: update-dependencies
**Шаги:**
1. **Check Python dependencies**
   ```bash
   pip-audit -r requirements.txt --format markdown
   ```
2. **Check npm dependencies**
   ```bash
   npm audit --json
   ```
3. **Upload results** - сохраняет отчеты

**Время выполнения:** ~1 минута

---

### 8. release.yml - Release Management

**Назначение:** Автоматическое создание релизов

**Запускается:**
- Создание тега `v*.*.*` (например: `v1.0.0`)

**Что делает:**

#### Job 1: create-release
**Шаги:**
1. **Generate changelog** - автоматически из commit messages
2. **Create GitHub Release** - публикует релиз

#### Job 2: build-and-publish
```yaml
Depends on: create-release
```

**Шаги:**
1. Собирает Docker образ с версионным тегом
2. Публикует как `latest` и `v1.0.0`

**Время выполнения:** ~5 минут

---

## 🔐 GitHub Secrets

Для работы CI/CD нужны следующие secrets:

### Обязательные:
```
REDMINE_URL          - URL Redmine сервера
REDMINE_API_KEY      - API ключ Redmine
BOT_TOKEN            - Токен Telegram бота
DATABASE_URL         - Строка подключения к PostgreSQL
ALLOWED_API_KEYS     - API ключи для авторизации
WEBAPP_URL           - URL веб-приложения
```

### Опциональные (для деплоя):
```
SSH_PRIVATE_KEY      - SSH ключ для деплоя
SSH_HOST             - IP сервера
SSH_USER             - Пользователь SSH
DOCKER_HUB_USERNAME  - Docker Hub логин
DOCKER_HUB_TOKEN     - Docker Hub токен
```

**Где добавить:** Settings → Secrets and variables → Actions → New repository secret

---

## 📊 Как читать результаты CI/CD

### ✅ Успешный запуск (зеленая галочка)
```
✅ All checks have passed
8 successful checks
```
Все хорошо - можно мержить PR или деплоить!

### ❌ Неуспешный запуск (красный крестик)
```
❌ Some checks were not successful
2 failing, 6 successful

Backend CI/CD / Lint and Test Backend (3.11) ❌
  → Details
```

**Что делать:**
1. Нажать **Details**
2. Найти красный текст с ошибкой
3. Исправить код
4. Запушить - CI перезапустится автоматически

### ⏸️ Skipped (серая иконка)
```
⏸️ Deploy to Production / Deploy to Production - Skipped
```
Workflow не запустился, потому что условие не выполнено (например, не та ветка)

### 🔄 In Progress (желтая иконка)
```
🔄 Backend CI/CD / Lint and Test Backend (3.11) - In progress
```
Workflow выполняется прямо сейчас, подождите...

---

## 🚀 Как использовать CI/CD в работе

### Сценарий 1: Разработка новой фичи

```bash
# 1. Создаете ветку
git checkout -b feature/new-api-endpoint

# 2. Пишете код
# ... редактируете файлы ...

# 3. Локально проверяете (опционально)
cd backend
pytest
flake8 .

# 4. Коммитите
git add .
git commit -m "feat: add new API endpoint for user stats"

# 5. Пушите
git push origin feature/new-api-endpoint

# 6. CI/CD запускается автоматически!
```

**Что происходит на GitHub:**
- ✅ Backend CI проверяет ваш код
- ✅ Тесты запускаются
- ✅ Security scan проверяет безопасность

**Если всё ОК:**
- Создаете PR → CI/CD запускается снова для PR
- После approve → мержите → Deploy запускается

### Сценарий 2: Исправление бага

```bash
git checkout -b fix/login-error
# ... исправляете баг ...
git commit -m "fix: resolve login error on mobile devices"
git push origin fix/login-error

# CI/CD проверит что баг исправлен и ничего не сломалось
```

### Сценарий 3: Обновление зависимостей

```bash
# Обновили requirements.txt
git commit -m "chore: update fastapi to 0.110.0"
git push

# CI/CD проверит что новая версия не ломает код
```

---

## 🐛 Частые проблемы и решения

### Проблема 1: Tests failed
```
FAILED tests/test_api.py::test_user_endpoint
AssertionError: assert 500 == 200
```

**Решение:**
1. Смотрите полный лог ошибки в Details
2. Запустите тест локально: `pytest tests/test_api.py::test_user_endpoint -v`
3. Исправьте код
4. Запушите - CI перезапустится

### Проблема 2: Flake8 errors
```
./backend/app/main.py:15:80: E501 line too long (95 > 79 characters)
```

**Решение:**
```bash
# Автофикс многих проблем:
black .
isort .

# Проверка перед push:
flake8 .
```

### Проблема 3: Security vulnerabilities found
```
Safety check found 2 vulnerabilities
```

**Решение:**
```bash
# Обновите уязвимые пакеты:
pip install --upgrade package-name

# Или обновите requirements.txt
```

### Проблема 4: Frontend build failed
```
vite build failed
```

**Решение:**
1. Проверьте что `npm install` проходит локально
2. Проверьте версию Node.js (нужна 20.19+ или 22.12+)
3. Исправьте ошибки в коде

### Проблема 5: Docker build failed
```
Error: failed to solve: failed to compute cache key
```

**Решение:**
1. Проверьте Dockerfile
2. Убедитесь что requirements.txt корректен
3. Проверьте что frontend/dist существует

---

## 📈 Метрики и мониторинг

### Где смотреть результаты:

**1. GitHub Actions Tab**
- https://github.com/Aid-rgb/TrackDev/actions
- Все запуски всех workflows
- История за последние 90 дней

**2. Pull Request**
- Внизу PR показывается статус всех checks
- Можно кликнуть Details для деталей

**3. Commit**
- Рядом с каждым commit есть иконка (✅/❌)
- Показывает статус CI/CD для этого commit

**4. Badges в README**
```markdown
![Backend CI](https://github.com/Aid-rgb/TrackDev/workflows/Backend%20CI%2FCD/badge.svg)
```

### Artifacts (артефакты)

После каждого запуска доступны:
- **Frontend build** - собранный frontend (retention: 7 дней)
- **Coverage reports** - отчеты о покрытии тестами
- **Security audit results** - результаты проверок безопасности
- **Integration test logs** - логи интеграционных тестов

**Где скачать:** Actions → выберите workflow → Artifacts секция внизу

---

## ⚙️ Настройка и кастомизация

### Как изменить что проверяется?

**Добавить новый тест:**
```bash
# Создайте test файл
echo "def test_new_feature(): assert True" > backend/tests/test_new.py

# Push - CI автоматически запустит новый тест
```

**Изменить версии Python:**
```yaml
# В .github/workflows/backend-ci.yml:
matrix:
  python-version: ['3.9', '3.10', '3.11', '3.12']  # Добавили 3.12
```

**Добавить новый check в PR:**
```yaml
# В .github/workflows/pr-checks.yml добавьте новый job
```

**Отключить workflow:**
```yaml
# В начале любого .yml файла закомментируйте on:
# on:
#   push:
#     branches: [ main ]
```

### Как добавить deploy на свой сервер?

**Отредактируйте `.github/workflows/deploy.yml`:**

```yaml
- name: Deploy to Production
  run: |
    # SSH deploy
    ssh user@server 'cd /app && docker-compose pull && docker-compose up -d'
    
    # Или Heroku
    heroku container:release web
    
    # Или Kubernetes
    kubectl apply -f k8s/deployment.yml
```

---

## 📞 FAQ

**Q: Сколько это стоит?**  
A: Для публичных репо - **бесплатно**. Для приватных - 2000 минут/месяц бесплатно.

**Q: Можно ли запустить workflow вручную?**  
A: Да! Actions → выберите workflow → Run workflow

**Q: Как добавить больше версий Python/Node для тестирования?**  
A: Измените `matrix` секцию в соответствующем workflow

**Q: CI/CD слишком медленный, как ускорить?**  
A:
- Используйте кеширование (уже настроено)
- Запускайте тесты параллельно
- Используйте `continue-on-error` для неважных проверок

**Q: Как отключить определенную проверку?**  
A: Добавьте `if: false` в job или закомментируйте весь job

**Q: Workflow не запускается, почему?**  
A: Проверьте `paths:` и `branches:` - возможно ваши изменения не попадают под условия

**Q: Можно ли видеть coverage прямо в PR?**  
A: Да, настройте интеграцию с Codecov или добавьте comment bot

**Q: Как получить уведомления о failed workflows?**  
A: Settings → Notifications → GitHub Actions → включите уведомления

---

## 📚 Дополнительные ресурсы

- **TESTING.md** - Подробная логика и семантика автотестов
- **CI_CD_SETUP.md** - Полное руководство по настройке CI/CD
- **CONTRIBUTING.md** - Правила работы с репозиторием

**Официальная документация:**
- [GitHub Actions](https://docs.github.com/en/actions)
- [Workflow syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Security hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

---

## 🎓 Обучение команды

### Для начинающих:
1. Прочитайте этот файл
2. Посмотрите несколько PR с успешными checks
3. Создайте тестовый PR и посмотрите как работает CI/CD

### Для продвинутых:
1. Изучите файлы в `.github/workflows/`
2. Кастомизируйте под свои нужды
3. Добавляйте новые проверки

---

**Последнее обновление:** 2026-06-10  
**Версия:** 1.0.0  
**Контакты:** [@Aid-rgb](https://github.com/Aid-rgb)

🚀 Happy CI/CD!
