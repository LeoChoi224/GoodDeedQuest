import uuid
from typing import Generic, TypeVar
from sqlalchemy import BinaryExpression, select
from sqlalchemy.orm import Session
from backend.app.common.database import Base

Model = TypeVar("Model", bound=Base)

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
      def get_by(self, **kwargs) -> Model | None:
            query = select(self.model).filter_by(**kwargs)
            return self.session.scalars(query).first()
