from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.bot.crud import UserRepository
from app.database import async_session_factory

router = Router()


@router.message(Command("search"))
async def cmd_search(message: Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="По возрасту", callback_data="search_age"))
    builder.add(InlineKeyboardButton(text="По стране", callback_data="search_location"))
    builder.add(InlineKeyboardButton(text="По предметам", callback_data="search_subjects"))

    await message.answer(
        "Выберите критерий поиска:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("search_"))
async def process_search(callback: CallbackQuery):
    search_type = callback.data.split("_")[1]

    async with async_session_factory() as session:
        repo = UserRepository(session)
        current_user = await repo.get_user_by_telegram_id(callback.from_user.id)

        if not current_user:
            await callback.message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /register")
            await callback.answer()
            return

        if search_type == "age":
            matches = await repo.find_matches_by_age(callback.from_user.id, current_user.age)
        elif search_type == "location":
            matches = await repo.find_matches_by_location(callback.from_user.id, current_user.location)
        elif search_type == "subjects":
            matches = await repo.find_matches_by_subjects(callback.from_user.id, current_user.subjects)

        if not matches:
            await callback.message.answer("К сожалению, подходящих партнеров не найдено.")
            await callback.answer()
            return

        # Формируем ответ с найденными партнерами
        response = "Найдены следующие партнеры:\n\n"
        for match in matches:
            response += f"🎓 Партнер\n"
            response += f"Страна: {match.location}\n"
            response += f"Язык: {match.language}\n"
            response += f"Возраст: {match.age}\n"
            response += f"Предметы: {', '.join(match.subjects)}\n"

            # Добавляем ссылку на профиль пользователя
            if match.username:
                response += f"Профиль: @{match.username}\n"
            else:
                response += f"Telegram ID: {match.telegram_id}\n"

            response += "\n"

        await callback.message.answer(response)
        await callback.answer()