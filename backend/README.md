# Redmine API & Telegram Bot

REST API и Telegram Bot для работы с Redmine.

## 📋 Содержание

- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [REST API](#rest-api)
- [Telegram Bot](#telegram-bot)
- [🌐 Web App Dashboard](#web-app-dashboard)
- [База данных](#база-данных)

## Установка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows - скачайте с https://www.postgresql.org/download/windows/
```

### 3. Создание базы данных

```sql
CREATE DATABASE redmine_bot;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE redmine_bot TO postgres;
```

## Конфигурация

Создайте файл `.env` на основе `.env.example`:

```env
# Redmine Configuration
REDMINE_URL=https://your-redmine.com
REDMINE_API_KEY=your_key

# API Security Configuration
ALLOWED_API_KEYS=user1:abc123,user2:def456

# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/redmine_bot

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Получение Telegram Bot Token

1. Откройте [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен

## REST API

### Запуск API сервера

```bash
# Инициализация базы данных (первый раз)
python init_db.py

# Запуск API
python run.py
# или
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Документация: http://localhost:8000/docs

### Авторизация

API использует авторизацию по Redmine API ключу. Каждый пользователь должен использовать свой личный Redmine API ключ.

#### Как получить Redmine API ключ

1. Зайдите в свой Redmine аккаунт
2. Перейдите в "Моя учётная запись" (My account)
3. В правой части страницы найдите "API ключ доступа"
4. Скопируйте ключ

#### Использование API ключа

Добавьте заголовок в запросы:

```
X-API-Key: ваш_redmine_api_ключ
```

**Важно:** Каждый пользователь использует свой Redmine API ключ. Это позволяет:
- `/my-tasks` показывать задачи конкретного пользователя
- `/time` логировать время от имени конкретного пользователя
- Все операции выполняются с правами соответствующего пользователя

**Публичные пути** (не требуют авторизации):
- `/` - статус
- `/health` - проверка здоровья
- `/docs` - документация Swagger
- `/openapi.json` - OpenAPI спецификация
- `/redoc` - документация ReDoc

**Защищенные пути** (требуют API ключ):
- Все эндпоинты `/api/v1/*`

### API Endpoints

- `GET /api/v1/projects` - проекты
- `GET /api/v1/tasks` - задачи
- `GET /api/v1/tasks/{id}` - детали задачи
- `GET /api/v1/my-tasks` - мои задачи
- `GET /api/v1/activities` - типы активностей
- `POST /api/v1/time` - залогировать время

### Примеры

#### Без авторизации (публичный эндпоинт)
```bash
curl http://localhost:8000/health
```

#### С авторизацией
```bash
curl -X POST http://localhost:8000/api/v1/time \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ваш_redmine_api_ключ" \
  -d '{"issue_id": 7875, "hours": 2.5}'
```

#### Получение проектов
```bash
curl -H "X-API-Key: ваш_redmine_api_ключ" \
  http://localhost:8000/api/v1/projects?limit=5
```

## Telegram Bot

### Запуск бота

```bash
# Инициализация базы данных (первый раз)
python init_db.py

# Запуск бота
python run_bot.py
```

### Функции бота

- 📁 **Проекты** - просмотр списка проектов Redmine
- 📋 **Все задачи** - просмотр всех задач
- 👤 **Мои задачи** - просмотр ваших задач
- ⏱ **Трекер времени** - запись затраченного времени на задачи
- ❓ **Помощь** - справка по боту

### Авторизация в боте

При первом запуске бот запросит ваш Redmine API ключ:

1. Введите команду `/start`
2. Бот проверит, есть ли вы в базе данных
3. Если нет - попросит ввести API ключ
4. После успешной авторизации вы получите доступ ко всем функциям

### Трекер времени

Для записи времени:

1. Нажмите "⏱ Трекер времени"
2. Выберите задачу из списка
3. Введите количество часов (например: 2.5)
4. Выберите дату (сегодня, вчера, позавчера или введите вручную)
5. Добавьте комментарий (или пропустите, введя "-")

### Команды бота

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- `/settings` - Настройки аккаунта (изменить API ключ)

## База данных

### Структура таблиц

#### users

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| telegram_id | Integer | Telegram ID пользователя |
| username | String | Telegram username |
| redmine_api_key | String | Redmine API ключ |
| is_active | Boolean | Активен ли пользователь |
| created_at | DateTime | Дата создания |
| updated_at | DateTime | Дата обновления |

### Миграции

При изменении моделей:

```bash
# Если используете Alembic
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Разработка

### Структура проекта

```
backend/
├── app/
│   ├── bot/
│   │   ├── __init__.py
│   │   └── bot.py              # Telegram Bot
│   ├── crud/
│   │   ├── base.py             # Base CRUD
│   │   ├── issue.py            # Issue operations
│   │   ├── project.py          # Project operations
│   │   ├── time_entry.py       # Time entry operations
│   │   └── user.py             # User CRUD
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # Database configuration
│   │   └── users.py            # User model
│   ├── routers/
│   │   └── api.py              # API routes
│   ├── __init__.py
│   ├── auth.py                 # Authorization
│   ├── config.py               # Configuration
│   └── schemas.py              # Pydantic schemas
├── main.py                     # FastAPI app
├── run.py                      # Run API server
├── run_bot.py                  # Run Telegram bot
├── init_db.py                  # Initialize database
├── requirements.txt
├── .env.example
└── README.md
```

## Troubleshooting

### Ошибка подключения к базе данных

```
❌ Ошибка: DATABASE_URL не указан в .env файле
```

**Решение:** Проверьте файл `.env` и убедитесь, что `DATABASE_URL` указан корректно.

### Ошибка авторизации в Redmine

```
❌ Неверный API ключ или ошибка подключения к Redmine
```

**Решение:**
1. Проверьте правильность Redmine API ключа
2. Убедитесь, что `REDMINE_URL` указан правильно
3. Проверьте доступность Redmine сервера

### Бот не запускается

```
❌ Ошибка: BOT_TOKEN не указан в .env файле
```

**Решение:** Получите токен у @BotFather и добавьте в `.env` файл.

## Лицензия

MIT


## 🌐 Web App Dashboard

### Что это?

Web App Dashboard - это интерактивный дашборд с графиками и таблицами, который открывается прямо в Telegram через Web App API.

### Возможности

- 📊 **Индекс здоровья проекта** (0-100) с gauge chart
- 📈 **6 ключевых метрик** в карточках
- 📉 **Графики** - динамика бэклога, нагрузка команды
- 📋 **Таблицы** - просроченные задачи, распределение нагрузки
- 🔍 **Фильтры** - по проектам и периодам
- 📱 **Адаптивный дизайн** для мобильных устройств

### Быстрый старт

#### 1. Установите ngrok (для локальной разработки)

```bash
# Windows (Chocolatey)
choco install ngrok

# Mac (Homebrew)
brew install ngrok

# Или скачайте с https://ngrok.com/download
```

#### 2. Зарегистрируйтесь на ngrok

1. Создайте аккаунт: https://dashboard.ngrok.com/signup
2. Получите authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
3. Добавьте authtoken:
```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
```

#### 3. Запустите FastAPI сервер

```bash
python run.py
# Сервер запустится на http://localhost:8000
```

#### 4. Запустите ngrok (в новом терминале)

```bash
ngrok http 8000
```

Скопируйте HTTPS URL, например: `https://abc123.ngrok-free.app`

#### 5. Обновите .env

```env
WEBAPP_URL=https://abc123.ngrok-free.app
```

⚠️ **Важно:** URL меняется при каждом запуске ngrok (бесплатная версия)

#### 6. Запустите бота

```bash
python run_bot.py
```

#### 7. Откройте в Telegram

1. Найдите вашего бота
2. Нажмите "📊 Метрики"
3. Нажмите "🌐 Открыть Web Dashboard"
4. 🎉 Готово!

### Автоматический запуск

**Windows:**
```bash
..\start_with_ngrok.bat
```

Этот скрипт автоматически запустит FastAPI и ngrok.

### Проверка работы

#### Тест 1: Health check
```
https://your-ngrok-url.ngrok-free.app/health
```
Должно вернуться: `{"status":"healthy"}`

#### Тест 2: Dashboard
```
https://your-ngrok-url.ngrok-free.app/dashboard?api_key=YOUR_KEY
```
Должен загрузиться дашборд.

#### Тест 3: API документация
```
https://your-ngrok-url.ngrok-free.app/docs
```
Должна открыться Swagger документация.

### Production развертывание

Для production не используйте ngrok! Используйте:

**VPS с nginx:**
```bash
# Установите nginx и certbot
sudo apt install nginx certbot python3-certbot-nginx

# Настройте nginx reverse proxy
sudo nano /etc/nginx/sites-available/redmine-bot

# Получите SSL сертификат
sudo certbot --nginx -d yourdomain.com
```

**Или используйте:**
- Heroku (бесплатный HTTPS)
- Railway / Render (современные платформы)
- AWS / Google Cloud / Azure (для больших проектов)

### Документация

- 📚 **Подробная инструкция:** `../WEBAPP_SETUP.md`
- ⚡ **Быстрый старт:** `../QUICK_START_WEBAPP.md`
- 🎨 **Frontend документация:** `../frontend/README.md`

### Решение проблем

#### Проблема: "your-domain.com" в URL

Вы забыли обновить `WEBAPP_URL` в `.env`:
```env
WEBAPP_URL=https://your-actual-ngrok-url.ngrok-free.app
```

#### Проблема: Dashboard не открывается

1. Убедитесь что FastAPI запущен: `python run.py`
2. Убедитесь что ngrok запущен: `ngrok http 8000`
3. Проверьте что используете HTTPS (не HTTP)
4. Проверьте что `WEBAPP_URL` правильный в `.env`

#### Проблема: Пустой дашборд

1. Проверьте API ключ в боте: "👤 Профиль"
2. Откройте Console в браузере (F12) для ошибок
3. Проверьте Network tab на ошибки API запросов

### Безопасность

⚠️ API ключ передается через URL параметр. Для production:

1. Используйте **только HTTPS** (обязательно!)
2. Рассмотрите более безопасную авторизацию через Telegram initData
3. Ограничьте время жизни сессии
4. Не делитесь ссылками на dashboard

---
