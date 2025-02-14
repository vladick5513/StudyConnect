from sqlalchemy import select, and_
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
        user = User(
            telegram_id=telegram_id,
            username=username,
            location=location,
            language=language,
            gender=gender,
            age=age,
            subjects=subjects
        )
        self.session.add(user)
        await self.session.commit()
        return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def find_matches_by_location(self, telegram_id: int, location: str) -> list[User]:
        query = select(User).where(
            (User.location == location) &
            (User.telegram_id != telegram_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def find_matches_by_age(self, telegram_id: int, age: int, range: int = 3) -> list[User]:
        query = select(User).where(
            (User.age.between(age - range, age + range)) &
            (User.telegram_id != telegram_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def find_matches_by_subjects(self, telegram_id: int, subjects: list[str]) -> list[User]:
        # Находим пользователей, у которых есть хотя бы один общий предмет
        query = select(User).where(
            and_(
                User.telegram_id != telegram_id,
                User.subjects.op('&&')(subjects)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()