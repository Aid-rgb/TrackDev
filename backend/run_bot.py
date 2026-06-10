#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота
"""
import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Запуск Telegram бота"""
    # Check required environment variables
    bot_token = os.getenv("BOT_TOKEN")
    database_url = os.getenv("DATABASE_URL")
    redmine_url = os.getenv("REDMINE_URL")
    
    if not bot_token:
        logger.error("BOT_TOKEN environment variable is required")
        print("❌ Ошибка: BOT_TOKEN не указан в .env файле")
        return
    
    if not database_url:
        logger.error("DATABASE_URL environment variable is required")
        print("❌ Ошибка: DATABASE_URL не указан в .env файле")
        return
    
    if not redmine_url:
        logger.error("REDMINE_URL environment variable is required")
        print("❌ Ошибка: REDMINE_URL не указан в .env файле")
        return
    
    print("=" * 50)
    print("🤖 Redmine Telegram Bot")
    print("=" * 50)
    print(f"Redmine URL: {redmine_url}")
    print(f"Database: {database_url}")
    print(f"Bot Token: {bot_token[:20]}...")
    print("=" * 50)
    print("Для остановки нажмите Ctrl+C")
    print()
    
    # Import and run bot
    from app.bot.bot import main as run_bot
    
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n👋 Бот остановлен")


if __name__ == "__main__":
    main()
