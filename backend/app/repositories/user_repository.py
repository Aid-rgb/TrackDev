from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
    """Получить пользователя по Telegram ID"""
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Получить пользователя по username"""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    redmine_api_key: str
) -> User:
    """Создать нового пользователя"""
    user = User(
        telegram_id=telegram_id,
        username=username,
        redmine_api_key=redmine_api_key
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_api_key(
    db: AsyncSession,
    telegram_id: int,
    redmine_api_key: str
) -> Optional[User]:
    """Обновить API ключ пользователя"""
    user = await get_user_by_telegram_id(db, telegram_id)
    if user:
        user.redmine_api_key = redmine_api_key
        await db.commit()
        await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, telegram_id: int) -> bool:
    """Удалить пользователя"""
    user = await get_user_by_telegram_id(db, telegram_id)
    if user:
        await db.delete(user)
        await db.commit()
        return True
    return False