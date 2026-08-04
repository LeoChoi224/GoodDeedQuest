"""backend의 VolunteerCenter 테이블을 읽기/ai_category 갱신 용도로만 사용하는 미러 모델.
분류 배치 작업 전용이라 필요한 컬럼만 매핑함 (ai 서비스는 backend와 다른 SQLAlchemy Base를 쓰기 때문에
같은 테이블이라도 모델을 새로 정의해야 함)."""
from typing import Optional
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from ai.app.common.database import Base


class VolunteerCenterMirror(Base):
    __tablename__ = "volunteer_center"

    center_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vol_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vol_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    vol_act: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    ai_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)