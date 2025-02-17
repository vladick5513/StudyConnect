from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.bot.crud import UserRepository
from app.database import async_session_factory
from app.utils.validation import (
    validate_country, validate_language, validate_subjects,
    MIN_AGE, MAX_AGE
)

router = Router()

class UpdateStates(StatesGroup):
    selecting_field = State()
    updating_location = State()
    updating_language = State()
    updating_age = State()
    updating_subjects = State()

@router.message(Command("update"))
async def cmd_update(message: Message, state: FSMContext):
    async with async_session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_user_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer("❌ Вы не зарегистрированы! Пожалуйста, сначала используйте команду /register.")
            return

        profile_text = f"""
📋 Ваш текущий профиль:
📍 Страна: {user.location}
🗣️ Язык: {user.language}
📅 Возраст: {user.age}
📚 Предметы: {', '.join(user.subjects)}

Выберите, что хотите изменить:
"""

        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="Страна", callback_data="update_location"))
        builder.add(InlineKeyboardButton(text="Язык", callback_data="update_language"))
        builder.add(InlineKeyboardButton(text="Возраст", callback_data="update_age"))
        builder.add(InlineKeyboardButton(text="Предметы", callback_data="update_subjects"))

        await message.answer(profile_text, reply_markup=builder.as_markup())
        await state.set_state(UpdateStates.selecting_field)

@router.callback_query(StateFilter(UpdateStates.selecting_field))
async def process_update_selection(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[1]

    if field == "location":
        await callback.message.answer("Введите новую страну проживания:")
        await state.set_state(UpdateStates.updating_location)

    elif field == "language":
        await callback.message.answer("Введите новый язык общения:")
        await state.set_state(UpdateStates.updating_language)

    elif field == "age":
        await callback.message.answer(f"Введите ваш новый возраст (число от {MIN_AGE} до {MAX_AGE}):")
        await state.set_state(UpdateStates.updating_age)

    elif field == "subjects":
        await callback.message.answer("Введите новый список предметов через запятую:")
        await state.set_state(UpdateStates.updating_subjects)

    await callback.answer()

@router.message(StateFilter(UpdateStates.updating_location))
async def process_location_update(message: Message, state: FSMContext):
    country = validate_country(message.text)
    if not country:
        await message.answer("❌ Указанная страна не найдена. Пожалуйста, проверьте правильность написания.")
        return

    async with async_session_factory() as session:
        repo = UserRepository(session)
        await repo.update_user_field(message.from_user.id, "location", country)

    await message.answer("✅ Страна проживания успешно обновлена!")
    await state.clear()

@router.message(StateFilter(UpdateStates.updating_language))
async def process_language_update(message: Message, state: FSMContext):
    language = validate_language(message.text)
    if not language:
        await message.answer("❌ Указанный язык не поддерживается. Пожалуйста, проверьте правильность написания.")
        return

    async with async_session_factory() as session:
        repo = UserRepository(session)
        await repo.update_user_field(message.from_user.id, "language", language)

    await message.answer("✅ Язык общения успешно обновлен!")
    await state.clear()

@router.message(StateFilter(UpdateStates.updating_age))
async def process_age_update(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (MIN_AGE <= int(message.text) <= MAX_AGE):
        await message.answer(f"❌ Пожалуйста, введите корректный возраст (число от {MIN_AGE} до {MAX_AGE}).")
        return

    async with async_session_factory() as session:
        repo = UserRepository(session)
        await repo.update_user_field(message.from_user.id, "age", int(message.text))

    await message.answer("✅ Возраст успешно обновлен!")
    await state.clear()

@router.message(StateFilter(UpdateStates.updating_subjects))
async def process_subjects_update(message: Message, state: FSMContext):
    subjects = [s.strip() for s in message.text.split(",")]

    if not validate_subjects(subjects):
        await message.answer("❌ Один или несколько предметов не найдены. Пожалуйста, проверьте правильность написания.")
        return

    async with async_session_factory() as session:
        repo = UserRepository(session)
        await repo.update_user_field(message.from_user.id, "subjects", subjects)

    await message.answer("✅ Список предметов успешно обновлен!")
    await state.clear()