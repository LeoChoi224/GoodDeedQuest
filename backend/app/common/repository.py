import uuid
from typing import Generic, TypeVar
from sqlalchemy import BinaryExpression, select
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

Model = TypeVar("Model", bound=models.Base)

class DatabaseRepository(Generic[Model]):
  def __init__(self, model: type[Model], session: Session) -> None:
        self.model = model
        self.session = session
  def create(self, data: dict) -> Model:
        instance = self.model(**data)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance
  def get(self, pk: uuid.UUID) -> Model | None:
        return self.session.get(self.model, pk)
  def filter(self, *expressions: BinaryExpression) -> list[Model]:
        query = select(self.model)
        if expressions:
            query = query.where(*expressions)
        return list(self.session.scalars(query))
