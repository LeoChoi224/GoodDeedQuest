"""DB에 실제로 붙는 테스트를 위한 데이터 헬퍼.

배경:
    일부 테스트가 "DB에 user_id=1 이 있다"고 가정하고 있었다. 그 유저가 지워지자
    전부 외래키 위반으로 실패했고, 팀원 노트북이나 CI 처럼 빈 DB 에서는 처음부터
    돌지 않았다. 테스트가 자기가 쓸 데이터를 스스로 만들게 해서 어느 환경에서든
    같은 결과가 나오도록 한다.

사용법:
    class SomeTest(TestCase):
        def setUp(self):
            self.test_user_id = create_test_user()

        def tearDown(self):
            delete_test_user(self.test_user_id)
"""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import text

import backend.app.models_registry  # noqa: F401  relationship 문자열 참조 해석용
from backend.app.auth.models import User
from backend.app.common.database import SessionLocal


def create_test_user() -> int:
    """테스트 전용 유저를 만들고 user_id 를 반환한다.

    email/nickname 에 임의 접미사를 붙여서 여러 테스트가 동시에 돌아도
    unique 제약에 걸리지 않게 한다.
    """
    suffix = uuid4().hex[:12]

    with SessionLocal() as db:
        user = User(
            email=f"pytest-{suffix}@example.com",
            password_hash="pytest-not-a-real-hash",
            nickname=f"pytest-{suffix}",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.user_id


def _tables_referencing_user(db) -> list[tuple[str, str]]:
    """user 테이블을 외래키로 참조하는 (테이블명, 컬럼명) 목록을 DB에서 읽어온다.

    목록을 코드에 박아두면 나중에 테이블이 늘었을 때 조용히 실패한다.
    스키마에서 직접 읽으면 그럴 일이 없다.
    """
    rows = db.execute(
        text(
            """
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND ccu.table_name = 'user'
            """
        )
    ).fetchall()

    return [(table, column) for table, column in rows]


def delete_test_user(user_id: int) -> None:
    """테스트 유저와 그 유저가 남긴 행들을 지운다.

    자식 테이블끼리도 외래키로 엮여 있어서(예: post_like -> community_post)
    한 번에 지워지지 않는다. 더 이상 지워지는 게 없을 때까지 반복한다.
    끝내 남는 게 있으면 유저를 남겨두고 조용히 넘어간다. 테스트 뒷정리가
    실패했다고 테스트 자체를 실패시킬 이유는 없다.
    """
    with SessionLocal() as db:
        targets = _tables_referencing_user(db)

        # 지워지는 게 있으면 다시 한 바퀴 돈다. 순서를 몰라도 결국 다 지워진다.
        for _ in range(len(targets) + 1):
            deleted_any = False
            remaining: list[tuple[str, str]] = []

            for table, column in targets:
                try:
                    result = db.execute(
                        text(f'DELETE FROM "{table}" WHERE {column} = :uid'),
                        {"uid": user_id},
                    )
                    db.commit()
                    if result.rowcount:
                        deleted_any = True
                except Exception:
                    db.rollback()
                    remaining.append((table, column))

            targets = remaining
            if not targets or not deleted_any:
                break

        try:
            db.execute(
                text('DELETE FROM "user" WHERE user_id = :uid'),
                {"uid": user_id},
            )
            db.commit()
        except Exception:
            db.rollback()
