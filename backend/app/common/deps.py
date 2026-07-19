from collections.abc import Callable
from fastapi import Depends
from sqlalchemy.orm import Session
from common.database import Base
from backend.app.common.database import get_db
from backend.app.common.repository import DatabaseRepository

def get_repository(
  model: type[Base],
) -> Callable[[Session], DatabaseRepository]:
  def func(session: Session = Depends[get_db]):
    return DatabaseRepository(model, session)
  return func