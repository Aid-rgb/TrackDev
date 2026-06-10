# CI/CD Documentation

## Обзор

Проект использует GitHub Actions для автоматизации тестирования, сборки и развертывания. Все workflow файлы находятся в `.github/workflows/`.

## Workflow файлы

### 1. `backend-ci.yml` - Backend CI/CD

**Когда запускается:**
- Push в ветки `main` или `develop`
- Pull request в ветки `main` или `develop`
- Только при изменениях в `backend/` или самого workflow файла

**Что делает:**
- Проверяет код на Python 3.9, 3.10, 3.11
- Запускает линтеры:
  - Black (форматирование)
  - isort (сортировка импортов)
  - Flake8 (проверка стиля кода)
  - MyPy (проверка типов)
- Запускает тесты через pytest
- Проверяет безопасность зависимостей (Safety, Bandit)

**Результат:** Гарантирует качество Python кода

---

### 2. `frontend-ci.yml` - Frontend CI/CD

**Когда запускается:**
- Push в ветки `main` или `develop`
- Pull request в ветки `main` или `develop`
- Только при изменениях в `frontend/` или самого workflow файла

**Что делает:**
- Проверяет код на Node.js 20.x и 22.x
- Запускает ESLint для проверки JavaScript/React кода
- Собирает production build через `npx vite build`
- Проверяет безопасность зависимостей (`npm audit`)
- Анализирует размер бандла
- Запускает Lighthouse audit для проверки производительности
- Сохраняет артефакты сборки

**Результат:** Гарантирует качество и производительность фронтенда

---

### 3. `integration-tests.yml` - Интеграционные тесты

**Когда запускается:**
- Push в ветки `main` или `develop`
- Pull request в ветки `main` или `develop`
- Можно запустить вручную через `workflow_dispatch`

**Что делает:**
- Поднимает PostgreSQL 15 как service
- Устанавливает Python 3.11 и Node.js 20.x
- Собирает фронтенд и копирует в `backend/static-react/`
- Создает `.env` файл с тестовыми credentials
- Запускает backend сервер (uvicorn)
- Тестирует API endpoints:
  - `/health` - проверка здоровья
  - `/` - главная страница
  - `/docs` - документация API
  - `/api/v1/projects` - API с авторизацией
  - `/dashboard` - фронтенд
- Останавливает сервер и сохраняет логи при ошибках
- Запускает E2E тесты (placeholder для Playwright)

**Результат:** Проверяет работу всего стека вместе

---

### 4. `deploy.yml` - Деплой

**Когда запускается:**
- Push в ветку `main`
- Можно запустить вручную через `workflow_dispatch`

**Что делает:**
- Собирает фронтенд
- Копирует сборку в `backend/static-react/`
- Строит Docker образ
- Публикует образ в GitHub Container Registry (ghcr.io)
- Создает tag с версией на основе даты

**Результат:** Docker образ готов к развертыванию

---

### 5. `pr-checks.yml` - PR валидация

**Когда запускается:**
- Pull request в любую ветку

**Что делает:**
- Проверяет формат коммитов (semantic commits: feat, fix, docs и т.д.)
- Проверяет размер PR (предупреждает если >500 строк)
- Проверяет наличие описания в PR

**Результат:** Гарантирует качество PR

---

### 6. `codeql-analysis.yml` - Анализ безопасности

**Когда запускается:**
- Push в ветку `main`
- Pull request в ветку `main`
- По расписанию: каждый понедельник в 12:00 UTC

**Что делает:**
- Запускает CodeQL анализ для Python и JavaScript
- Ищет уязвимости безопасности
- Создает alerts в GitHub Security

**Результат:** Выявляет потенциальные проблемы безопасности

---

### 7. `dependency-update.yml` - Мониторинг зависимостей

**Когда запускается:**
- По расписанию: каждый понедельник в 09:00 UTC
- Можно запустить вручную

**Что делает:**
- Проверяет устаревшие Python зависимости (`pip list --outdated`)
- Проверяет устаревшие npm зависимости (`npm outdated`)
- Сохраняет отчет как артефакт

**Результат:** Информирует об устаревших зависимостях

---

### 8. `release.yml` - Управление релизами

**Когда запускается:**
- При создании тега версии (например, `v1.0.0`)

**Что делает:**
- Запускает все тесты (backend, frontend, integration)
- Строит Docker образ с тегом версии
- Публикует в Container Registry
- Создает GitHub Release с changelog

**Результат:** Автоматизирует процесс релиза

---

## GitHub Secrets

Для работы CI/CD нужны следующие secrets (Settings → Secrets and variables → Actions):

### Обязательные:
- `REDMINE_URL` - URL вашего Redmine сервера
- `REDMINE_API_KEY` - API ключ для доступа к Redmine
- `BOT_TOKEN` - Telegram bot token
- `DATABASE_URL` - PostgreSQL connection string
- `ALLOWED_API_KEYS` - API ключи для доступа к backend (формат: `name:key,name2:key2`)
- `WEBAPP_URL` - URL вашего web приложения

### Автоматические (создаются GitHub):
- `GITHUB_TOKEN` - для доступа к API и Container Registry

---

## Как работает типичный workflow

### Pull Request:
1. Разработчик создает PR
2. Запускаются: `pr-checks.yml`, `backend-ci.yml`, `frontend-ci.yml`, `codeql-analysis.yml`
3. Если все проверки прошли → PR можно мержить
4. Если есть ошибки → нужно исправить

### Push в main:
1. Код попадает в `main`
2. Запускаются: `backend-ci.yml`, `frontend-ci.yml`, `integration-tests.yml`, `deploy.yml`
3. Если все ОК → Docker образ публикуется в ghcr.io

### Релиз:
1. Создаете тег: `git tag v1.0.0 && git push origin v1.0.0`
2. Запускается `release.yml`
3. Проходят все тесты
4. Создается GitHub Release с Docker образом

---

## Просмотр результатов

### GitHub Actions:
```
Repository → Actions → выбираете workflow → видите историю запусков
```

### Артефакты:
После запуска workflow могут быть сохранены артефакты:
- Frontend builds
- Test logs
- Dependency reports

Скачать можно из: `Actions → конкретный запуск → Artifacts (внизу)`

### Логи:
Каждый шаг workflow имеет развернутые логи. Кликните на название шага чтобы увидеть вывод.

---

## Локальный запуск тестов

Перед push рекомендуется запускать тесты локально:

### Backend:
```bash
cd backend
pip install -r requirements.txt
pytest
black . --check
isort . --check
flake8 .
```

### Frontend:
```bash
cd frontend
npm install
npm run lint
npx vite build
```

### Integration (через Docker):
```bash
docker-compose up --build
```

---

## Troubleshooting

### Тесты падают локально но проходят в CI (или наоборот)
- Проверьте версии Python/Node.js
- Убедитесь что все зависимости установлены
- Проверьте переменные окружения

### Docker build fails
- Проверьте что frontend собрался и `dist/` существует
- Убедитесь что все secrets настроены

### Integration tests timeout
- PostgreSQL service может не успеть запуститься
- Увеличьте `sleep` время в workflow

### npm audit находит уязвимости
- Обновите зависимости: `npm update`
- Для breaking changes может потребоваться ручное обновление

---

## Рекомендации

1. **Не пушьте напрямую в main** - используйте feature branches и PR
2. **Следите за размером PR** - большие PR сложно ревьювить
3. **Пишите semantic commit messages**: 
   - `feat: добавил новый endpoint`
   - `fix: исправил баг в авторизации`
   - `docs: обновил README`
4. **Проверяйте CI перед merge** - все галочки должны быть зелеными
5. **Обновляйте зависимости регулярно** - проверяйте еженедельный отчет

---

## Контакты

При проблемах с CI/CD:
1. Проверьте логи в GitHub Actions
2. Поищите похожие issues
3. Создайте issue с описанием проблемы и логами
