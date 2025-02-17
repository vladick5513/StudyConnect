from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.bot.crud import UserRepository
from app.database import async_session_factory
from app.utils.validation import VALID_COUNTRIES, VALID_LANGUAGES, VALID_SUBJECTS, MIN_AGE, MAX_AGE

router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_location = State()
    waiting_for_language = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_subjects = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = """
👋 Привет! Я бот для поиска партнёров по обучению.

Что я умею:
• Помогаю найти людей для совместного изучения предметов
• Подбираю партнёров по возрасту, стране проживания или интересующим предметам
• Помогаю установить контакт с потенциальными учебными партнёрами

Доступные команды:
/register - Зарегистрироваться
/search - Искать партнёров по обучению

Для начала работы пройдите регистрацию с помощью команды /register 📝
"""
    await message.answer(welcome_text)


@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext):
    async with async_session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_user_by_telegram_id(message.from_user.id)

        if user:
            await message.answer("Вы уже зарегистрированы! Вы можете искать партнёров с помощью /search.")
            return

        await message.answer("Отлично! Давайте создадим ваш профиль. В какой стране вы живете?")
        await state.set_state(RegistrationStates.waiting_for_location)


@router.message(StateFilter(RegistrationStates.waiting_for_location))
async def process_location(message: Message, state: FSMContext):
    location = message.text.strip().capitalize()
    if location not in VALID_COUNTRIES:
        await message.answer("Пожалуйста, введите корректное название страны.")
        return

    await state.update_data(location=location)
    await message.answer("На каком языке вы предпочитаете общаться?")
    await state.set_state(RegistrationStates.waiting_for_language)


@router.message(StateFilter(RegistrationStates.waiting_for_language))
async def process_language(message: Message, state: FSMContext):
    language = message.text.strip().lower()
    if language not in VALID_LANGUAGES:
        await message.answer("Пожалуйста, введите корректное название страны.")
        return

    await state.update_data(language=language)

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Мужской", callback_data="gender_male"))
    builder.add(InlineKeyboardButton(text="Женский", callback_data="gender_female"))

    await message.answer("Укажите ваш пол:", reply_markup=builder.as_markup())
    await state.set_state(RegistrationStates.waiting_for_gender)


@router.callback_query(StateFilter(RegistrationStates.waiting_for_gender))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = "male" if callback.data == "gender_male" else "female"
    await state.update_data(gender=gender)
    await callback.message.answer("Укажите ваш возраст (число):")
    await state.set_state(RegistrationStates.waiting_for_age)
    await callback.answer()


@router.message(StateFilter(RegistrationStates.waiting_for_age))
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return

    age = int(message.text)
    if age < MIN_AGE or age > MAX_AGE:
        await message.answer(f"Пожалуйста, введите корректный возраст (от {MIN_AGE} до {MAX_AGE}).")
        return

    await state.update_data(age=age)
    await message.answer("🎓 Какие предметы вы хотите изучать? Перечислите их через запятую.")
    await state.set_state(RegistrationStates.waiting_for_subjects)


@router.message(StateFilter(RegistrationStates.waiting_for_subjects))
async def process_subjects(message: Message, state: FSMContext):
    user_data = await state.get_data()
    subjects = [s.strip().lower() for s in message.text.split(",")]

    invalid_subjects = [s for s in subjects if s not in VALID_SUBJECTS]
    if invalid_subjects:
        await message.answer(
            "Некоторые предметы введены некорректно. Пожалуйста, введите корректные предметы, например (математика, биология)")
        return

    async with async_session_factory() as session:
        repo = UserRepository(session)
        await repo.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            location=user_data['location'],
            language=user_data['language'],
            gender=user_data['gender'],
            age=user_data['age'],
            subjects=subjects
        )

    await message.answer("✅ Профиль успешно создан! Теперь вы можете искать партнёров с помощью команды /search.")
    await state.clear()