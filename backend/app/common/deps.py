from collections.abc import Callable
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.app.auth import models
from backend.app.admin import models
from backend.app.badge import models
from backend.app.challenge import models
from backend.app.community import models
from backend.app.map import models
from backend.app.quest import models
from backend.app.quest_recommend import models
from backend.app.quest_verification import models
from backend.app.shop import models
from backend.app.short_form import models
from backend.app.common.database import get_db
from backend.app.common.repository import DatabaseRepository

def get_repository(
  model: type[models.Base],
) -> Callable[[Session], DatabaseRepository]:
  def func(session: Session = Depends[get_db]):
    return DatabaseRepository(model, session)
  return func