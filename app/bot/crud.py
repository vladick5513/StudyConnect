from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self,
                          telegram_id: int,
                          username: str | None,
                          location: str,
                          language: str,
                          gender: str,
                          age: int,
                          subjects: list[str]) -> User:
        normalized_subjects = [subject.strip().lower() for subject in subjects]

        user = User(
            telegram_id=telegram_id,
            username=username,
            location=location,
            language=language,
            gender=gender,
            age=age,
            subjects=normalized_subjects
        )
        self.session.add(user)
        await self.session.commit()
        return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def find_matches_by_age_param(self, telegram_id: int, target_age: int, range: int = 3) -> list[User]:
        query = select(User).where(
            (User.age.between(target_age - range, target_age + range)) &
            (User.telegram_id != telegram_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def find_matches_by_location_param(self, telegram_id: int, location: str) -> list[User]:
        normalized_location = location.strip().lower()
        query = select(User).where(
            (User.location.ilike(f"%{normalized_location}%")) &
            (User.telegram_id != telegram_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def find_matches_by_subjects_param(self, telegram_id: int, subjects: list[str]) -> list[User]:
        normalized_subjects = [subject.strip().lower() for subject in subjects]
        query = select(User).where(
            and_(
                User.telegram_id != telegram_id,
                User.subjects.op('&&')(normalized_subjects)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_user_field(self, telegram_id: int, field: str, value: any) -> None:
        if field == "subjects":
            value = [subject.strip().lower() for subject in value]

        query = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(**{field: value})
        )
        await self.session.execute(query)
        await self.session.commit()