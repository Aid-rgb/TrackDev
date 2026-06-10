"""
Telegram бот для администрирования проектов Redmine
Показывает метрики здоровья проектов и дашборд аналитики
"""
import os
import logging
from typing import Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

from app.core.config import REDMINE_URL
from app.models.database import async_session, init_db
from app.repositories import get_user_by_telegram_id, create_user, update_user_api_key
from app.integrations.redmine_projects import get_projects, get_project
from app.services import get_project_health_score

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# FSM States
class BotStates(StatesGroup):
    waiting_for_api_key = State()


# Keyboards
def get_main_keyboard(api_key: Optional[str] = None) -> ReplyKeyboardMarkup:
    """Главное меню"""
    webapp_url = os.getenv("WEBAPP_URL")
    
    kb = [
        [KeyboardButton(text="🏥 Здоровье проектов")],
    ]
    
    # Если URL настроен, добавляем кнопку открытия дашборда прямо в меню
    if webapp_url and webapp_url.startswith("https://") and api_key:
        dashboard_url = f"{webapp_url}/dashboard#api_key={api_key}"
        kb.append([KeyboardButton(text="📊 Открыть дашборд", web_app=types.WebAppInfo(url=dashboard_url))])
    else:
        kb.append([KeyboardButton(text="📊 Открыть дашборд")])
        
    kb.append([KeyboardButton(text="👤 Профиль")])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ============================================
# КОМАНДЫ
# ============================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Приветствие и регистрация"""
    await state.clear()
    
    telegram_id = message.from_user.id
    username = message.from_user.username or f"user_{telegram_id}"
    
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        
        if not user:
            # Новый пользователь
            await message.answer(
                f"👋 Привет, {message.from_user.first_name}!\n\n"
                f"🤖 Я бот для администрирования проектов Redmine.\n\n"
                f"📊 Я помогу отслеживать здоровье ваших проектов и предоставлю доступ к аналитическому дашборду.\n\n"
                f"🔑 Для начала работы отправьте ваш Redmine API ключ.\n\n"
                f"Как получить API ключ:\n"
                f"1. Зайдите в Redmine: {REDMINE_URL}\n"
                f"2. Перейдите в: Моя учетная запись → API ключ\n"
                f"3. Скопируйте и отправьте мне ключ",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.set_state(BotStates.waiting_for_api_key)
        else:
            # Существующий пользователь
            if user.is_active and user.redmine_api_key:
                await message.answer(
                    f"👋 С возвращением, {message.from_user.first_name}!\n\n"
                    f"🏥 Здоровье проектов - посмотрите индекс здоровья всех проектов\n"
                    f"📊 Открыть дашборд - полная аналитика в веб-интерфейсе\n"
                    f"👤 Профиль - управление API ключом",
                    reply_markup=get_main_keyboard(user.redmine_api_key)
                )
            else:
                await message.answer(
                    f"👋 С возвращением!\n\n"
                    f"⚠️ Ваш API ключ не активен.\n"
                    f"Отправьте новый Redmine API ключ для продолжения работы.",
                    reply_markup=ReplyKeyboardRemove()
                )
                await state.set_state(BotStates.waiting_for_api_key)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Помощь"""
    help_text = (
        "🤖 <b>Бот для администрирования проектов Redmine</b>\n\n"
        
        "<b>Основные функции:</b>\n\n"
        
        "🏥 <b>Здоровье проектов</b>\n"
        "Показывает индекс здоровья (0-100) для каждого проекта.\n"
        "Индикаторы:\n"
        "• 🟢 85-100: Проект под контролем\n"
        "• 🟡 60-84: Есть риски\n"
        "• 🔴 <60: Критическая ситуация\n\n"
        
        "📊 <b>Открыть дашборд</b>\n"
        "Открывает веб-дашборд с подробной аналитикой:\n"
        "• Графики и диаграммы\n"
        "• Детальные метрики\n"
        "• Исторические данные\n\n"
        
        "👤 <b>Профиль</b>\n"
        "Управление вашим аккаунтом:\n"
        "• Просмотр API ключа\n"
        "• Изменение API ключа\n\n"
        
        "<b>Команды:</b>\n"
        "/start - Начать работу\n"
        "/help - Справка\n"
        "/cancel - Отменить текущее действие"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нечего отменять.", reply_markup=get_main_keyboard())
        return
    
    telegram_id = message.from_user.id
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        api_key = user.redmine_api_key if user else None

    await state.clear()
    await message.answer("✅ Действие отменено.", reply_markup=get_main_keyboard(api_key))


# ============================================
# РЕГИСТРАЦИЯ И АВТОРИЗАЦИЯ
# ============================================

@dp.message(BotStates.waiting_for_api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    """Обработка API ключа"""
    api_key = message.text.strip()
    
    # Удаляем сообщение с ключом (безопасность)
    try:
        await message.delete()
    except Exception:
        pass
    
    if len(api_key) < 20:
        await message.answer(
            "❌ API ключ слишком короткий.\n"
            "Пожалуйста, отправьте корректный Redmine API ключ."
        )
        return
    
    telegram_id = message.from_user.id
    # Исправление бага: используем только username из Telegram, не перезаписываем его ключом
    username = message.from_user.username or f"user_{telegram_id}"
    
    logger.info(f"Processing API key for user", extra={
        "telegram_id": telegram_id,
        "username": username,
        "api_key_length": len(api_key)
    })
    
    # Проверяем ключ
    try:
        test_projects = await get_projects(api_key, limit=1)
        
        async with async_session() as session:
            user = await get_user_by_telegram_id(session, telegram_id)
            
            if user:
                # Обновляем ключ
                logger.info(f"Updating API key for existing user", extra={
                    "telegram_id": telegram_id,
                    "username": username
                })
                await update_user_api_key(session, telegram_id, api_key)
                await message.answer(
                    "✅ API ключ успешно обновлен!\n\n"
                    "Теперь вы можете использовать бота.",
                    reply_markup=get_main_keyboard(api_key)
                )
            else:
                # Создаем нового пользователя
                logger.info(f"Creating new user", extra={
                    "telegram_id": telegram_id,
                    "username": username
                })
                await create_user(session, telegram_id, username, api_key)
                await message.answer(
                    "✅ Регистрация успешна!\n\n"
                    "Вы можете начать работу с ботом.",
                    reply_markup=get_main_keyboard(api_key)
                )
            
            await state.clear()
            
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        await message.answer(
            "❌ Не удалось проверить API ключ.\n\n"
            "Возможные причины:\n"
            "• Неверный ключ\n"
            "• Нет доступа к Redmine\n"
            "• Ключ не активен\n\n"
            "Попробуйте снова или используйте /cancel для отмены."
        )


# ============================================
# ЗДОРОВЬЕ ПРОЕКТОВ
# ============================================

@dp.message(F.text == "🏥 Здоровье проектов")
async def show_projects_health(message: types.Message):
    """Показать здоровье всех проектов"""
    telegram_id = message.from_user.id
    
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        
        if not user or not user.redmine_api_key:
            await message.answer(
                "❌ Вы не авторизованы.\n"
                "Используйте /start для регистрации."
            )
            return
        
        api_key = user.redmine_api_key
    
    try:
        # Получаем список проектов
        projects = await get_projects(api_key, limit=50)
        
        if not projects:
            await message.answer("📋 У вас нет доступных проектов.")
            return
        
        # Создаем inline клавиатуру с проектами
        builder = InlineKeyboardBuilder()
        
        for proj in projects:
            proj_id = proj.get("id")
            proj_name = proj.get("name", "Без названия")
            
            # Ограничиваем длину названия
            if len(proj_name) > 30:
                proj_name = proj_name[:27] + "..."
            
            builder.button(
                text=f"📁 {proj_name}",
                callback_data=f"health_{proj_id}"
            )
        
        builder.adjust(1)  # По одной кнопке в ряд
        
        await message.answer(
            "🏥 <b>Здоровье проектов</b>\n\n"
            "Выберите проект для просмотра индекса здоровья:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        await message.answer(
            "❌ Ошибка при получении списка проектов.\n"
            "Проверьте ваш API ключ в профиле."
        )


@dp.callback_query(F.data.startswith("health_"))
async def show_project_health(callback: types.CallbackQuery):
    """Показать здоровье конкретного проекта"""
    await callback.answer()
    
    project_id = int(callback.data.split("_")[1])
    telegram_id = callback.from_user.id
    
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        api_key = user.redmine_api_key
    
    try:
        # Получаем информацию о проекте
        proj = await get_project(api_key, project_id)
        proj_name = proj.get("name", "Проект")
        
        # Получаем метрики здоровья
        health = await get_project_health_score(api_key, project_id)
        
        # health - это Pydantic модель HealthScoreResponse, не dict
        score = health.score
        status_text = health.status_text
        factors = health.factors
        recommendations = health.recommendations
        
        # Форматируем сообщение
        message_text = f"🏥 <b>{proj_name}</b>\n\n"
        message_text += f"{status_text}\n"
        message_text += f"<b>Индекс здоровья:</b> {score}/100\n\n"
        
        if factors:
            message_text += "<b>📉 Факторы влияния:</b>\n"
            for factor in factors:
                message_text += f"• {factor}\n"
            message_text += "\n"
        
        if recommendations:
            message_text += "<b>💡 Рекомендации:</b>\n"
            for rec in recommendations:
                message_text += f"• {rec}\n"
        
        # Кнопки для действий
        # Изменение: открываем дашборд сразу, без промежуточного экрана
        webapp_url = os.getenv("WEBAPP_URL")
        dashboard_url = f"{webapp_url}/dashboard#project_id={project_id}&api_key={api_key}" if webapp_url else None
        
        builder = InlineKeyboardBuilder()
        if dashboard_url and dashboard_url.startswith("https://"):
            builder.button(
                text="📊 Подробная аналитика", 
                web_app=types.WebAppInfo(url=dashboard_url)
            )
        else:
            # Fallback, если HTTPS URL не настроен
            builder.button(text="📊 Подробная аналитика", callback_data=f"dashboard_{project_id}")
            
        builder.button(text="◀️ Назад к списку", callback_data="back_to_projects")
        builder.adjust(1)
        
        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error getting project health: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при получении метрик проекта.\n\n"
            f"Попробуйте позже или проверьте доступ к проекту."
        )


@dp.callback_query(F.data == "back_to_projects")
async def back_to_projects(callback: types.CallbackQuery):
    """Вернуться к списку проектов"""
    await callback.answer()
    
    telegram_id = callback.from_user.id
    
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        api_key = user.redmine_api_key
    
    try:
        projects = await get_projects(api_key, limit=50)
        
        builder = InlineKeyboardBuilder()
        
        for proj in projects:
            proj_id = proj.get("id")
            proj_name = proj.get("name", "Без названия")
            
            if len(proj_name) > 30:
                proj_name = proj_name[:27] + "..."
            
            builder.button(
                text=f"📁 {proj_name}",
                callback_data=f"health_{proj_id}"
            )
        
        builder.adjust(1)
        
        await callback.message.edit_text(
            "🏥 <b>Здоровье проектов</b>\n\n"
            "Выберите проект для просмотра индекса здоровья:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await callback.message.edit_text("❌ Ошибка при загрузке проектов.")


# ============================================
# ДАШБОРД
# ============================================

@dp.message(F.text == "📊 Открыть дашборд")
async def open_dashboard(message: types.Message):
    """Открыть веб-дашборд"""
    telegram_id = message.from_user.id
    
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        
        if not user or not user.redmine_api_key:
            await message.answer(
                "❌ Вы не авторизованы.\n"
                "Используйте /start для регистрации."
            )
            return
        
        api_key = user.redmine_api_key
    
    # URL дашборда из переменной окружения (корневой путь)
    webapp_url = os.getenv("WEBAPP_URL")
    
    # Проверяем, что URL настроен и использует HTTPS
    if not webapp_url or not webapp_url.startswith("https://"):
        await message.answer(
            "⚠️ <b>Дашборд не настроен</b>\n\n"
            "Web App дашборд требует HTTPS соединение.\n\n"
            "<b>Для администратора:</b>\n"
            "1. Установите ngrok (см. SETUP_NGROK_NOW.md)\n"
            "2. Запустите: <code>ngrok http 8000</code>\n"
            "3. Добавьте HTTPS URL в .env:\n"
            "   <code>WEBAPP_URL=https://your-url.ngrok-free.app</code>\n"
            "4. Перезапустите бота",
            parse_mode="HTML"
        )
        return
    
    # Используем URL-фрагмент (#) вместо query-параметров для безопасности
    # Фрагмент не отправляется на сервер и не попадает в логи
    dashboard_url = f"{webapp_url}/dashboard#api_key={api_key}"
    
    # Создаем Web App кнопку
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🌐 Открыть дашборд",
        web_app=types.WebAppInfo(url=dashboard_url)
    )
    
    await message.answer(
        "📊 <b>Аналитический дашборд</b>\n\n"
        "Полная аналитика ваших проектов:\n"
        "• 📈 Графики и диаграммы\n"
        "• 📊 Все метрики в одном месте\n"
        "• 🔄 Данные в реальном времени\n\n"
        "Нажмите кнопку ниже для открытия:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("dashboard_"))
async def open_project_dashboard(callback: types.CallbackQuery):
    """Открыть дашборд конкретного проекта"""
    await callback.answer()
    
    project_id = int(callback.data.split("_")[1])
    telegram_id = callback.from_user.id
    
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        api_key = user.redmine_api_key
    
    # URL дашборда из переменной окружения
    webapp_url = os.getenv("WEBAPP_URL")
    
    # Проверяем HTTPS
    if not webapp_url or not webapp_url.startswith("https://"):
        await callback.message.edit_text(
            "⚠️ <b>Дашборд не настроен</b>\n\n"
            "Требуется HTTPS соединение для Web App.\n"
            "Обратитесь к администратору.",
            parse_mode="HTML"
        )
        return
    
    # Используем URL-фрагмент (#) вместо query-параметров для безопасности
    dashboard_url = f"{webapp_url}/dashboard#project_id={project_id}&api_key={api_key}"
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🌐 Открыть дашборд проекта",
        web_app=types.WebAppInfo(url=dashboard_url)
    )
    builder.button(text="◀️ Назад", callback_data=f"health_{project_id}")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "📊 <b>Дашборд проекта</b>\n\n"
        "Откройте веб-интерфейс для детальной аналитики:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


# ============================================
# ПРОФИЛЬ
# ============================================

@dp.message(F.text == "👤 Профиль")
async def show_profile(message: types.Message):
    """Показать профиль пользователя"""
    telegram_id = message.from_user.id
    
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        
        if not user:
            await message.answer(
                "❌ Профиль не найден.\n"
                "Используйте /start для регистрации."
            )
            return
        
        # Маскируем API ключ
        api_key = user.redmine_api_key
        masked_key = f"{api_key[:8]}...{api_key[-8:]}" if api_key else "Не установлен"
        
        profile_text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"<b>Telegram ID:</b> {user.telegram_id}\n"
            f"<b>Username:</b> @{user.username}\n"
            f"<b>API ключ:</b> <code>{masked_key}</code>\n"
            f"<b>Статус:</b> {'✅ Активен' if user.is_active else '❌ Неактивен'}\n"
            f"<b>Регистрация:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Изменить API ключ", callback_data="change_api_key")
        builder.adjust(1)
        
        await message.answer(
            profile_text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "change_api_key")
async def change_api_key(callback: types.CallbackQuery, state: FSMContext):
    """Изменить API ключ"""
    await callback.answer()
    
    await callback.message.edit_text(
        "🔑 <b>Изменение API ключа</b>\n\n"
        "Отправьте новый Redmine API ключ.\n\n"
        "Или используйте /cancel для отмены.",
        parse_mode="HTML"
    )
    
    await state.set_state(BotStates.waiting_for_api_key)


# ============================================
# ЗАПУСК БОТА
# ============================================

async def main():
    """Запуск бота"""
    logger.info("Starting Redmine Admin Bot...")
    
    # Инициализация БД
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Bot started successfully!")
    
    # Запуск polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
