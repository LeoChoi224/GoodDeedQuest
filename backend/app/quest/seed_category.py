"""
확정 카테고리 6종 시드.

새 DB에는 category가 비어 있어, 시드 없이 추천을 돌리면 Quest INSERT가
외래키 위반으로 실패한다. alembic upgrade head 다음에 반드시 실행한다.

실행: python -m backend.app.quest.seed_category
"""
import logging
from typing import Final

from sqlalchemy import text

from backend.app.common.database import SessionLocal
from backend.app.quest.models import Category


logger: Final = logging.getLogger(__name__)

# code는 소문자(프론트 CATEGORY_ICONS 키), name은 대문자 영어(AI가 뱉는 category_name)
CATEGORIES: Final = [
    {"category_id": 1, "code": "volunteer",   "name": "VOLUNTEER",   "icon_url": "https://example.com/icons/volunteer.png"},
    {"category_id": 2, "code": "environment", "name": "ENVIRONMENT", "icon_url": "https://example.com/icons/environment.png"},
    {"category_id": 3, "code": "sharing",     "name": "SHARING",     "icon_url": "https://example.com/icons/sharing.png"},
    {"category_id": 4, "code": "animal",      "name": "ANIMAL",      "icon_url": "https://example.com/icons/animal.png"},
    {"category_id": 5, "code": "community",   "name": "COMMUNITY",   "icon_url": "https://example.com/icons/community.png"},
    {"category_id": 6, "code": "other",       "name": "OTHER",       "icon_url": "https://example.com/icons/other.png"},
]


def seed_categories() -> None:
    """
    확정 카테고리 6종을 적재합니다.
    code와 name에 유니크 제약이 없어 단순 INSERT로 짜면 실행할 때마다 6줄씩 늘어나므로,
    category_id 기준으로 있으면 덮어쓰고 없으면 만드는 방식으로 멱등하게 처리합니다.
    """
    with SessionLocal() as db:
        try:
            for row in CATEGORIES:
                # 1. 이미 있으면 값만 갱신 (code 기본값 'other'로 잘못 들어간 행을 교정)
                category = db.query(Category).filter_by(category_id=row["category_id"]).first()
                if category:
                    category.code = row["code"]
                    category.name = row["name"]
                    category.icon_url = row["icon_url"]
                    category.is_active = True
                    continue

                # 2. 없으면 신규 생성
                db.add(Category(
                    category_id=row["category_id"],
                    code=row["code"],
                    name=row["name"],
                    icon_url=row["icon_url"],
                    is_active=True,
                ))

            db.commit()

            # 3. category_id를 명시해서 넣으면 시퀀스가 따라오지 않는다.
            #    보정하지 않으면 이후 자동 증가 INSERT가 id=1을 다시 쓰려다 중복 키 오류가 난다.
            db.execute(
                text("SELECT setval('category_category_id_seq', :last_id)"),
                {"last_id": CATEGORIES[-1]["category_id"]},
            )
            db.commit()

            logger.info(f"카테고리 시드 완료. 총 {len(CATEGORIES)}종")

        except Exception as e:
            db.rollback()
            logger.error(f"카테고리 시드 중 예외 발생. 에러: {str(e)}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_categories()