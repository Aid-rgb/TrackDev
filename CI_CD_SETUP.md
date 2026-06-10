# 🚀 CI/CD Setup для TrackDev

Полная настройка Continuous Integration и Continuous Deployment для вашего проекта на GitHub.

## 📋 Оглавление

- [Обзор](#обзор)
- [Структура Pipeline](#структура-pipeline)
- [Быстрый старт](#быстрый-старт)
- [Настройка GitHub Secrets](#настройка-github-secrets)
- [Workflows](#workflows)
- [Docker & Deployment](#docker--deployment)
- [Troubleshooting](#troubleshooting)

## 🎯 Обзор

CI/CD система для TrackDev включает:

- ✅ **Backend CI** - тестирование, линтинг Python кода
- ✅ **Frontend CI** - сборка, тестирование React приложения
- ✅ **Integration Tests** - полные интеграционные тесты
- ✅ **Security Scans** - проверка уязвимостей
- ✅ **Docker Build** - сборка и публикация образов
- ✅ **Automated Deployment** - автоматический деплой
- ✅ **CodeQL Analysis** - анализ безопасности кода
- ✅ **Dependency Updates** - мониторинг зависимостей

## 🏗 Структура Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                    Pull Request                         │
├─────────────────────────────────────────────────────────┤
│  1. PR Checks (metadata, size, commits)                │
│  2. Backend CI (lint, test, security)                  │
│  3. Frontend CI (lint, build, lighthouse)              │
│  4. Integration Tests                                   │
│  5. Docker Build Test                                   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Merge to develop/main                      │
├─────────────────────────────────────────────────────────┤
│  1. Full CI/CD Pipeline                                 │
│  2. Build & Push Docker Images                          │
│  3. Deploy to Staging/Production                        │
│  4. Security Scans                                       │
└─────────────────────────────────────────────────────────┘
```

## ⚡ Быстрый старт

### 1. Подготовка репозитория

```bash
# Клонируйте репозиторий
git clone https://github.com/Aid-rgb/TrackDev.git
cd TrackDev

# Убедитесь что все файлы на месте
ls -la .github/workflows/
```

### 2. Настройка GitHub Actions

GitHub Actions уже настроен! Файлы workflow находятся в `.github/workflows/`:

- `backend-ci.yml` - Backend CI/CD
- `frontend-ci.yml` - Frontend CI/CD
- `integration-tests.yml` - Интеграционные тесты
- `deploy.yml` - Деплой
- `pr-checks.yml` - Проверки Pull Request
- `codeql-analysis.yml` - Анализ безопасности
- `dependency-update.yml` - Обновления зависимостей

### 3. Первый запуск

```bash
# Создайте ветку и сделайте commit
git checkout -b feature/ci-cd-setup
git add .
git commit -m "ci: add CI/CD pipeline"
git push origin feature/ci-cd-setup

# Создайте Pull Request на GitHub
```

CI/CD автоматически запустится! 🎉

## 🔐 Настройка GitHub Secrets

### Обязательные Secrets

Перейдите в **Settings → Secrets and variables → Actions** и добавьте:

```
REDMINE_URL          # URL вашего Redmine (https://your-redmine.com)
REDMINE_API_KEY      # API ключ Redmine
BOT_TOKEN            # Токен Telegram бота
DATABASE_URL         # URL базы данных для production
ALLOWED_API_KEYS     # API ключи для доступа (user1:key1,user2:key2)
WEBAPP_URL           # URL веб-приложения
```

### Опциональные Secrets (для деплоя)

```
# Для SSH деплоя
SSH_PRIVATE_KEY      # SSH ключ для доступа к серверу
SSH_HOST             # IP/hostname сервера
SSH_USER             # Пользователь SSH

# Для облачных провайдеров
AWS_ACCESS_KEY_ID    # AWS credentials
AWS_SECRET_ACCESS_KEY
DOCKER_HUB_USERNAME  # Docker Hub (если используете)
DOCKER_HUB_TOKEN
```

### Как добавить Secret

1. Откройте ваш репозиторий на GitHub
2. Перейдите в **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Введите имя и значение
5. Нажмите **Add secret**

## 📝 Workflows

### Backend CI (`backend-ci.yml`)

**Триггеры:**
- Push в `main`, `develop`
- Pull Request в `main`, `develop`
- Изменения в `backend/**`

**Что делает:**
```
1. Lint & Test
   - Black (форматирование)
   - isort (сортировка импортов)
   - Flake8 (линтинг)
   - MyPy (проверка типов)
   - Pytest (тесты + coverage)

2. Security Scan
   - Safety (уязвимости зависимостей)
   - Bandit (безопасность кода)

3. Docker Build
   - Сборка образа
   - Тестовый запуск
```

**Python версии:** 3.9, 3.10, 3.11 (matrix build)

### Frontend CI (`frontend-ci.yml`)

**Триггеры:**
- Push в `main`, `develop`
- Pull Request в `main`, `develop`
- Изменения в `frontend/**`

**Что делает:**
```
1. Lint & Build
   - ESLint (линтинг)
   - npm audit (уязвимости)
   - npm build (сборка)
   - Bundle size analysis

2. Lighthouse Audit
   - Performance
   - Accessibility
   - Best Practices
   - SEO

3. Security Scan
   - npm audit
```

**Node версии:** 18.x, 20.x, 22.x (matrix build)

### Integration Tests (`integration-tests.yml`)

**Триггеры:**
- Push в `main`, `develop`
- Pull Request
- Manual dispatch

**Что делает:**
```
1. Full Stack Test
   - Запуск PostgreSQL
   - Сборка frontend
   - Запуск backend
   - Тестирование API endpoints
   - Проверка static files

2. E2E Tests (опционально)
   - Playwright тесты
```

### Deploy (`deploy.yml`)

**Триггеры:**
- Push в `main` → Production
- Push в `develop` → Staging
- Manual dispatch (выбор environment)
- Tags `v*` → Production

**Что делает:**
```
1. Build & Push Docker Images
   - Сборка backend образа
   - Включение frontend build
   - Публикация в GitHub Container Registry

2. Deploy to Environment
   - Staging или Production
   - Health checks
   - Deployment summary
```

### PR Checks (`pr-checks.yml`)

**Триггеры:**
- Pull Request события

**Что делает:**
```
1. PR Metadata
   - Проверка заголовка (semantic)
   - Размер PR
   
2. Validate Changes
   - Проверка измененных файлов
   - Предупреждения о тестах
   - Breaking changes detection

3. Lint Commits
   - Commitlint (conventional commits)

4. Auto Comment
   - Автоматический комментарий с summary
```

### CodeQL Analysis (`codeql-analysis.yml`)

**Триггеры:**
- Push в `main`, `develop`
- Pull Request
- Weekly schedule (Monday)

**Что делает:**
```
- Анализ Python кода
- Анализ JavaScript кода
- Security vulnerability detection
- Code quality checks
```

### Dependency Updates (`dependency-update.yml`)

**Триггеры:**
- Weekly schedule (Monday)
- Manual dispatch

**Что делает:**
```
- Python dependencies audit (pip-audit)
- NPM dependencies audit
- Создание отчетов
```

## 🐳 Docker & Deployment

### Локальная разработка с Docker

```bash
# Создайте .env файл
cp backend/.env.example backend/.env
# Отредактируйте .env

# Запустите все сервисы
docker-compose up -d

# Проверьте статус
docker-compose ps

# Логи
docker-compose logs -f backend
docker-compose logs -f bot

# Остановка
docker-compose down
```

### Production Deployment

#### Вариант 1: GitHub Container Registry

Образы автоматически публикуются в `ghcr.io`:

```bash
# Pull образ
docker pull ghcr.io/aid-rgb/trackdev/backend:main

# Запуск
docker run -d \
  --name trackdev-backend \
  -p 8000:8000 \
  --env-file .env \
  ghcr.io/aid-rgb/trackdev/backend:main
```

#### Вариант 2: SSH Deploy (требует настройки)

Добавьте в `deploy.yml` шаг SSH:

```yaml
- name: Deploy via SSH
  uses: appleboy/ssh-action@master
  with:
    host: ${{ secrets.SSH_HOST }}
    username: ${{ secrets.SSH_USER }}
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    script: |
      cd /path/to/app
      docker-compose pull
      docker-compose up -d
```

#### Вариант 3: Cloud Providers

**Heroku:**
```yaml
- name: Deploy to Heroku
  uses: akhileshns/heroku-deploy@v3.12.14
  with:
    heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
    heroku_app_name: "trackdev-app"
    heroku_email: "your@email.com"
```

**Railway/Render:**
- Подключите GitHub репозиторий
- Настройте переменные окружения
- Автоматический деплой при push

**AWS/GCP/Azure:**
- Используйте соответствующие GitHub Actions
- Настройте credentials в Secrets

### Environments на GitHub

Настройте environments для staging и production:

1. **Settings** → **Environments** → **New environment**
2. Создайте `staging` и `production`
3. Настройте **Protection rules**:
   - Required reviewers (для production)
   - Wait timer (опционально)
   - Deployment branches (только main для production)

## 🧪 Тестирование

### Локальный запуск тестов

**Backend:**
```bash
cd backend

# Установите dev зависимости
pip install pytest pytest-asyncio pytest-cov flake8 black isort mypy

# Запустите тесты
pytest

# С coverage
pytest --cov=app --cov-report=html

# Линтинг
flake8 .
black --check .
isort --check-only .
mypy app
```

**Frontend:**
```bash
cd frontend

# Установите зависимости
npm ci

# Линтинг
npm run lint

# Сборка
npm run build
```

### CI тестирование

Тесты запускаются автоматически в CI. Проверьте результаты в:
- **Actions** tab на GitHub
- **Pull Request** checks
- **Coverage reports** в artifacts

## 📊 Мониторинг

### GitHub Actions

Проверяйте статус workflows:
```
Repository → Actions → выберите workflow
```

### Artifacts

Скачайте artifacts для анализа:
- Build artifacts
- Test coverage reports
- Audit reports
- Lighthouse reports

### Notifications

Настройте уведомления:
1. **Settings** → **Notifications**
2. Включите уведомления для **Actions**
3. Выберите способ: email, mobile, web

### Badges

Добавьте badges в README:

```markdown
![Backend CI](https://github.com/Aid-rgb/TrackDev/workflows/Backend%20CI%2FCD/badge.svg)
![Frontend CI](https://github.com/Aid-rgb/TrackDev/workflows/Frontend%20CI%2FCD/badge.svg)
![Integration Tests](https://github.com/Aid-rgb/TrackDev/workflows/Integration%20Tests/badge.svg)
```

## 🔧 Troubleshooting

### Pipeline fails на первом запуске

**Проблема:** Отсутствуют secrets

**Решение:**
```
1. Добавьте все обязательные secrets
2. Re-run workflow
```

### Tests fail в CI

**Проблема:** PostgreSQL connection

**Решение:**
```yaml
# Проверьте DATABASE_URL в .env:
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/redmine_bot_test
```

### Docker build fails

**Проблема:** Missing dependencies

**Решение:**
```bash
# Проверьте requirements.txt
# Добавьте недостающие пакеты
pip freeze > backend/requirements.txt
```

### Deploy fails

**Проблема:** Missing secrets или неправильный deploy script

**Решение:**
1. Проверьте secrets
2. Обновите deploy.yml с вашей deployment стратегией
3. Тестируйте локально с docker-compose

### Frontend build size too large

**Проблема:** Large bundle size

**Решение:**
```bash
# Анализируйте bundle
npm run build
# Оптимизируйте импорты
# Используйте code splitting
# Проверьте dependencies
```

## 📚 Best Practices

### Commit Messages

Используйте Conventional Commits:

```
feat: add new feature
fix: fix bug
docs: update documentation
style: formatting changes
refactor: code refactoring
test: add tests
ci: CI/CD changes
chore: maintenance
```

### Pull Requests

1. Создавайте feature branches
2. Пишите описательные заголовки
3. Добавляйте описание изменений
4. Ждите успешного прохождения CI
5. Запрашивайте review

### Branch Strategy

```
main (production)
  └── develop (staging)
       └── feature/* (features)
       └── fix/* (bugfixes)
       └── hotfix/* (urgent fixes)
```

### Environment Variables

- **Никогда** не коммитьте secrets в git
- Используйте `.env.example` для документации
- Храните secrets в GitHub Secrets
- Используйте разные значения для staging/production

### Testing

- Пишите тесты для новых features
- Поддерживайте coverage > 80%
- Тестируйте локально перед push
- Проверяйте CI перед merge

## 🎓 Дополнительные ресурсы

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [React Testing Library](https://testing-library.com/react)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 🤝 Поддержка

Если возникли вопросы:

1. Проверьте логи в GitHub Actions
2. Изучите документацию выше
3. Создайте Issue на GitHub
4. Свяжитесь с командой

---

**Автор:** TrackDev Team  
**Версия:** 1.0.0  
**Последнее обновление:** 2026-06-10
