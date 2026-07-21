from datetime import date, datetime
import httpx
from fastapi import BackgroundTasks
from backend.app.auth.models import User
from backend.app.common.config import get_setting
from backend.app.common.database import SessionLocal
from backend.app.common.repository import DatabaseRepository

def calculate_age(birthday: date) -> int:
    today = date.today()
    age = today.year - birthday.year
    if (today.month, today.day) < (birthday.month, birthday.day):
        age -= 1
    return age


async def embed_user_profile_task(user_id: int):
    with SessionLocal() as session:
        repository = DatabaseRepository(User, session)
        user = repository.get(user_id)
        if user is None:
          return
        try:
          async with httpx.AsyncClient() as client:
            response = await client.post(
              f"{get_setting().AI_SERVICE_URL}/ai/user/embed",
              json={
                "category": user.category,
                "active_time": user.active_time,
                "preferred_difficulty": user.preferred_difficulty.value if user.preferred_difficulty else None,
                "age": calculate_age(user.birthday) if user.birthday else None
              },
              timeout=10.0,
            )
            if response.status_code == 200:
              user.profile_embedding = response.json()["data"]["embedding"]
              user.last_embedded_at = datetime.now()
              session.commit()
        except Exception:
          pass
        
def trigger_embedding_if_needed(user: User, background_tasks: BackgroundTasks):
  if user.last_embedded_at is None or user.last_embedded_at.date() < date.today():
    background_tasks.add_task(embed_user_profile_task, user.user_id)