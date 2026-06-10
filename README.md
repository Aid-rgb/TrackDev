# 🚀 TrackDev - Redmine Project Management Tool

[![Backend CI/CD](https://github.com/Aid-rgb/TrackDev/workflows/Backend%20CI%2FCD/badge.svg)](https://github.com/Aid-rgb/TrackDev/actions/workflows/backend-ci.yml)
[![Frontend CI/CD](https://github.com/Aid-rgb/TrackDev/workflows/Frontend%20CI%2FCD/badge.svg)](https://github.com/Aid-rgb/TrackDev/actions/workflows/frontend-ci.yml)
[![Integration Tests](https://github.com/Aid-rgb/TrackDev/workflows/Integration%20Tests/badge.svg)](https://github.com/Aid-rgb/TrackDev/actions/workflows/integration-tests.yml)
[![CodeQL](https://github.com/Aid-rgb/TrackDev/workflows/CodeQL%20Security%20Analysis/badge.svg)](https://github.com/Aid-rgb/TrackDev/actions/workflows/codeql-analysis.yml)

> REST API, Telegram Bot и Web Dashboard для работы с Redmine - всё в одном месте!

## ✨ Особенности

- 🌐 **REST API** - полноценный API для работы с Redmine
- 🤖 **Telegram Bot** - удобный интерфейс в Telegram
- 📊 **Web Dashboard** - интерактивные графики и метрики
- 🔒 **Безопасность** - аутентификация по API ключам
- 🐳 **Docker** - готовые контейнеры для деплоя
- ⚡ **CI/CD** - полностью автоматизированный pipeline
- 📈 **Метрики проекта** - индекс здоровья, загрузка команды, дедлайны

## 🏗️ Технологии

**Backend:**
- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy
- aiogram (Telegram Bot)

**Frontend:**
- React 19
- Vite
- Tailwind CSS 4
- Recharts
- Framer Motion

**DevOps:**
- Docker & Docker Compose
- GitHub Actions
- pytest & coverage
- ESLint & Prettier

## 🚀 Быстрый старт

### Вариант 1: Docker (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com/Aid-rgb/TrackDev.git
cd TrackDev

# Настройте переменные окружения
cp backend/.env.example backend/.env
# Отредактируйте backend/.env

# Запустите всё одной командой!
docker-compose up -d

# Готово! 🎉
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Вариант 2: Локальная разработка

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env
uvicorn main:app --reload

# Frontend (в новом терминале)
cd frontend
npm install
npm run dev

# Telegram Bot (в новом терминале)
cd backend
python run_bot.py
```

### Вариант 3: Makefile

```bash
make install      # Установить зависимости
make dev-backend  # Запустить backend
make dev-frontend # Запустить frontend
make dev-bot      # Запустить bot
```

## 📚 Документация

- 📘 [Backend README](backend/README.md) - Полная документация API и бота
- 🧪 [TESTING.md](TESTING.md) - **Логика автотестирования и CI/CD** ⭐
- 📗 [CI/CD Setup Guide](CI_CD_SETUP.md) - Детальная настройка CI/CD

## 🎯 Основные возможности

### REST API

```bash
# Health check
curl http://localhost:8000/health

# Получить проекты
curl -H "X-API-Key: your_key" \
  http://localhost:8000/api/v1/projects

# Залогировать время
curl -X POST http://localhost:8000/api/v1/time \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_key" \
  -d '{"issue_id": 123, "hours": 2.5}'
```

**Документация:** http://localhost:8000/docs

### Telegram Bot

Основные команды:
- `/start` - Начать работу
- `/help` - Справка
- `/settings` - Настройки

Функции:
- 📁 Просмотр проектов
- 📋 Список задач (все / мои)
- ⏱ Трекер времени
- 📊 Метрики проекта
- 🌐 Web Dashboard

### Web Dashboard

Откройте прямо в Telegram или в браузере:

- 📊 Индекс здоровья проекта (0-100)
- 📈 Динамика бэклога
- 👥 Загрузка команды
- ⏰ Просроченные задачи
- 📉 Графики и аналитика

## 🔧 Конфигурация

Создайте `backend/.env`:

```env
# Redmine
REDMINE_URL=https://your-redmine.com
REDMINE_API_KEY=your_api_key

# Telegram
BOT_TOKEN=your_telegram_bot_token

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db

# API Security
ALLOWED_API_KEYS=user1:key1,user2:key2

# Web App
WEBAPP_URL=https://your-domain.com

# Server
HOST=0.0.0.0
PORT=8000
```

## 🧪 Тестирование

```bash
# Все тесты
make test

# Backend тесты
make test-backend
pytest --cov=app

# Frontend тесты
make test-frontend

# Линтинг
make lint

# Форматирование
make format

# CI/CD локально
make ci
```

## 🐳 Docker

```bash
# Сборка
docker-compose build

# Запуск
docker-compose up -d

# Логи
docker-compose logs -f

# Остановка
docker-compose down

# Очистка
docker-compose down -v
```

## 🚀 Deployment

### GitHub Container Registry (автоматически)

При push в `main`:
```bash
# Docker образ автоматически публикуется:
ghcr.io/aid-rgb/trackdev/backend:main
```

### Manual Deploy

```bash
# Pull образ
docker pull ghcr.io/aid-rgb/trackdev/backend:main

# Запуск
docker run -d \
  --name trackdev \
  -p 8000:8000 \
  --env-file .env \
  ghcr.io/aid-rgb/trackdev/backend:main
```

## 📊 CI/CD Pipeline

Полностью автоматизированный pipeline включает:

### При Pull Request:
- ✅ Проверка commit messages
- ✅ Backend lint & tests (Python 3.9, 3.10, 3.11)
- ✅ Frontend lint & build (Node 18.x, 20.x, 22.x)
- ✅ Integration tests
- ✅ Security scans
- ✅ Docker build test
- ✅ Code coverage reports

### При Merge:
- ✅ Full CI/CD pipeline
- ✅ Build & push Docker images
- ✅ CodeQL security analysis
- ✅ Deploy to staging/production

### Weekly:
- ✅ Dependency updates (Dependabot)
- ✅ Security vulnerability scans
- ✅ CodeQL analysis

**Детали:** См. [CI_CD_SETUP.md](CI_CD_SETUP.md)

## 🛠️ Development

### Project Structure

```
TrackDev/
├── .github/
│   ├── workflows/          # CI/CD pipelines
│   ├── ISSUE_TEMPLATE/     # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
├── backend/
│   ├── app/                # Application code
│   │   ├── bot/           # Telegram bot
│   │   ├── core/          # Core functionality
│   │   ├── integrations/  # Redmine integration
│   │   ├── models/        # Database models
│   │   ├── repositories/  # Data access
│   │   ├── routers/       # API routes
│   │   └── services/      # Business logic
│   ├── tests/             # Tests
│   ├── Dockerfile         # Docker image
│   └── requirements.txt   # Dependencies
├── frontend/
│   ├── src/               # React source
│   │   ├── components/   # React components
│   │   ├── App.jsx       # Main app
│   │   └── api.js        # API client
│   └── package.json       # Dependencies
├── docker-compose.yml     # Docker orchestration
├── Makefile               # Development commands
└── README.md              # This file
```

### Local Development

```bash
# Backend с hot reload
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend с hot reload
cd frontend
npm run dev

# Telegram Bot
cd backend
python run_bot.py

# PostgreSQL
docker-compose up -d postgres
```

## 🤝 Contributing

Мы рады вашему вкладу! См. [CONTRIBUTING.md](CONTRIBUTING.md)

### Workflow

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing`)
3. Commit изменения (`git commit -m 'feat: add amazing feature'`)
4. Push в branch (`git push origin feature/amazing`)
5. Создайте Pull Request

### Commit Convention

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: новая функция
fix: исправление бага
docs: документация
test: тесты
ci: CI/CD
chore: обслуживание
```

## 📝 License

MIT License - см. [LICENSE](LICENSE)

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) - современный Python web framework
- [React](https://react.dev/) - UI library
- [aiogram](https://aiogram.dev/) - Telegram Bot framework
- [PostgreSQL](https://www.postgresql.org/) - база данных

## 📞 Контакты

- GitHub: [@Aid-rgb](https://github.com/Aid-rgb)
- Issues: [TrackDev Issues](https://github.com/Aid-rgb/TrackDev/issues)

## 🗺️ Roadmap

- [ ] Поддержка нескольких Redmine инстансов
- [ ] Расширенная аналитика и отчеты
- [ ] Mobile приложение
- [ ] Интеграция с Jira, GitHub
- [ ] Уведомления в реальном времени
- [ ] Экспорт данных в Excel/PDF

---

**Сделано с ❤️ для автотестеров и разработчиков**

⭐ Если проект полезен - поставьте звезду на GitHub!
