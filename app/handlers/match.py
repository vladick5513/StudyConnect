from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.bot.crud import UserRepository
from app.database import async_session_factory

router = Router()


# Состояния для поиска
class SearchStates(StatesGroup):
    waiting_for_age = State()
    waiting_for_location = State()
    waiting_for_subjects = State()


# Словарь для хранения ID последнего сообщения "Не найдено"
last_not_found_message = {}


@router.message(Command("search"))
async def cmd_search(message: Message):
    async with async_session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_user_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer("❌ Вы не зарегистрированы! Пожалуйста, сначала используйте команду /register.")
            return

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="По возрасту", callback_data="search_age"))
    builder.add(InlineKeyboardButton(text="По стране", callback_data="search_location"))
    builder.add(InlineKeyboardButton(text="По предметам", callback_data="search_subjects"))

    await message.answer(
        "🔍 Выберите критерий поиска:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("search_"))
async def process_search_selection(callback: CallbackQuery, state: FSMContext):
    search_type = callback.data.split("_")[1]

    # Проверяем регистрацию пользователя
    async with async_session_factory() as session:
        repo = UserRepository(session)
        if not await repo.get_user_by_telegram_id(callback.from_user.id):
            await callback.message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /register")
            await callback.answer()
            return

    # Запрашиваем параметры поиска в зависимости от выбранного критерия
    if search_type == "age":
        await callback.message.answer("Введите желаемый возраст для поиска партнера:")
        await state.set_state(SearchStates.waiting_for_age)
    elif search_type == "location":
        await callback.message.answer("Введите страну для поиска партнера:")
        await state.set_state(SearchStates.waiting_for_location)
    elif search_type == "subjects":
        await callback.message.answer(
            "Введите предмет или предметы для поиска партнера (через запятую):"
        )
        await state.set_state(SearchStates.waiting_for_subjects)

    await callback.answer()


@router.message(StateFilter(SearchStates.waiting_for_age))
async def process_age_search(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный возраст (число):")
        return

    age = int(message.text)
    if age < 13 or age > 80:
        await message.answer("Пожалуйста, введите реалистичный возраст (от 13 до 80):")
        return

    await perform_search(message, "age", age)
    await state.clear()


@router.message(StateFilter(SearchStates.waiting_for_location))
async def process_location_search(message: Message, state: FSMContext):
    await perform_search(message, "location", message.text)
    await state.clear()


@router.message(StateFilter(SearchStates.waiting_for_subjects))
async def process_subjects_search(message: Message, state: FSMContext):
    subjects = [s.strip() for s in message.text.split(",")]
    await perform_search(message, "subjects", subjects)
    await state.clear()


async def perform_search(message: Message, search_type: str, search_param):
    user_id = message.from_user.id

    # Удаляем предыдущее сообщение "Не найдено"
    if user_id in last_not_found_message:
        try:
            await message.bot.delete_message(
                chat_id=user_id,
                message_id=last_not_found_message[user_id]
            )
        except Exception as e:
            print(f"Ошибка удаления сообщения: {e}")
        del last_not_found_message[user_id]

    async with async_session_factory() as session:
        repo = UserRepository(session)

        # Выполняем поиск в зависимости от типа
        if search_type == "age":
            matches = await repo.find_matches_by_age_param(user_id, search_param)
        elif search_type == "location":
            matches = await repo.find_matches_by_location_param(user_id, search_param)
        elif search_type == "subjects":
            matches = await repo.find_matches_by_subjects_param(user_id, search_param)

        if not matches:
            msg = await message.answer("К сожалению, подходящих партнеров не найдено.")
            last_not_found_message[user_id] = msg.message_id
            return

        # Формируем ответ с найденными партнерами
        response = "Найдены следующие партнеры:\n\n"
        for match in matches:
            response += f"🎓 Партнер\n"
            response += f"📍 Страна: {match.location}\n"
            response += f"🗣️ Язык: {match.language}\n"
            response += f"📅 Возраст: {match.age}\n"
            response += f"📚 Предметы: {', '.join(match.subjects)}\n"

            if match.username:
                response += f"Профиль: @{match.username}\n"
            else:
                response += f"Telegram ID: {match.telegram_id}\n"

            response += "\n"

        await message.answer(response)