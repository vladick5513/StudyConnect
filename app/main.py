import asyncio
from aiogram import Bot, Dispatcher

from app.config import settings
from app.handlers.auth import router as auth_router
from app.handlers.match import router as match_router

# Создание бота
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Функция для запуска бота
async def main():
    dp.include_routers(auth_router, match_router) #добавить роутеры
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")