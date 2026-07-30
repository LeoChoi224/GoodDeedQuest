"""
GoodDeedQuest 데모 데이터 시드 파일

실행 위치: 프로젝트 루트(GoodDeedQuest)
실행 명령: python -m backend.seed_demo_data

권장 저장 위치:
    backend/seed_demo_data.py

생성 데이터:
- 서울/경기 지역
- 환경/봉사/생활실천 카테고리
- 로그인 가능한 데모 사용자 10명(관리자 겸 팀장 1명 포함)
- 개인/팀 퀘스트
- 승인된 퀘스트 인증 기록
- 커뮤니티 게시글, 좋아요, 댓글
- 관심 없음 기록, 신고, 최근 7일 접속 기록
- 공개/비공개 챌린지 팀과 팀원
- 대기/거절 상태의 팀 초대
- 팀 초대 AI 추천에 필요한 사용자 관심사, 난이도, 활동 시간대,
  위치, 임베딩, 레벨, 연속 활동, 최근 30일 승인 기록

주의:
- 기존 데이터를 삭제하지 않습니다.
- seed.*@example.com 계정과 [SEED] 표시 데이터가 이미 있으면 최신 값으로 갱신합니다.
- --delete 옵션은 현재/이전 Seed 계정(example.com, gdq.local)과 연결된 Seed 데이터만 삭제합니다.
- DB 마이그레이션이 완료된 상태에서 실행해야 합니다.
"""

from __future__ import annotations

import argparse

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import MetaData, Table, and_, delete, func, insert, select, text, update
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

from backend.app.common.database import engine


SEED_PASSWORD = "Seed1234!"
SEED_EMAIL_DOMAIN = "example.com"
LEGACY_SEED_EMAIL_DOMAIN = "gdq.local"
NOW = datetime.now(timezone.utc)


def _password_hash(password: str) -> str:
    """프로젝트 비밀번호 유틸을 우선 사용하고, 없으면 안전한 fallback을 사용합니다."""
    import importlib

    candidates = (
        ("backend.app.common.auth", "hash_password"),
        ("backend.app.common.auth", "get_password_hash"),
        ("backend.app.auth.service", "hash_password"),
        ("backend.app.auth.service", "get_password_hash"),
    )
    for module_name, function_name in candidates:
        try:
            function = getattr(importlib.import_module(module_name), function_name)
            return str(function(password))
        except (ImportError, AttributeError, TypeError):
            continue

    try:
        from passlib.context import CryptContext

        return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)
    except Exception as exc:  # pragma: no cover - 실행 환경별 fallback
        raise RuntimeError(
            "비밀번호 해시 함수를 찾지 못했습니다. "
            "backend.app.common.auth의 hash_password/get_password_hash 또는 passlib을 확인해 주세요."
        ) from exc


def _reflect(engine_: Engine) -> dict[str, Table]:
    metadata = MetaData()
    metadata.reflect(bind=engine_)
    return dict(metadata.tables)


def _require_tables(tables: dict[str, Table], names: Iterable[str]) -> None:
    missing = [name for name in names if name not in tables]
    if missing:
        raise RuntimeError(
            "필수 테이블이 없습니다: " + ", ".join(missing) + "\n"
            "먼저 python -m alembic --config backend/alembic.ini upgrade head 를 실행해 주세요."
        )


def _available_columns(table: Table, values: dict[str, Any]) -> dict[str, Any]:
    """현재 DB 테이블에 실제로 존재하는 컬럼만 INSERT에 사용합니다."""
    return {key: value for key, value in values.items() if key in table.c}


def _enum_value(table: Table, column_name: str, *preferred: str) -> str:
    """PostgreSQL/SQLite enum 표현 차이를 흡수해 실제 허용값을 선택합니다."""
    column = table.c[column_name]
    enum_values = list(getattr(column.type, "enums", []) or [])

    if not enum_values:
        return preferred[0]

    normalized = {str(value).upper().replace(" ", "_"): str(value) for value in enum_values}
    for candidate in preferred:
        key = candidate.upper().replace(" ", "_")
        if key in normalized:
            return normalized[key]

    raise RuntimeError(
        f"{table.name}.{column_name} enum에서 {preferred!r} 값을 찾지 못했습니다. "
        f"현재 허용값: {enum_values}"
    )


def _next_id(connection: Connection, table: Table, pk_name: str) -> int:
    current = connection.execute(select(func.max(table.c[pk_name]))).scalar_one_or_none()
    return int(current or 0) + 1


def _find_one_id(
    connection: Connection,
    table: Table,
    id_column: str,
    **conditions: Any,
) -> int | None:
    clauses = [table.c[key] == value for key, value in conditions.items()]
    row = connection.execute(select(table.c[id_column]).where(and_(*clauses))).first()
    return int(row[0]) if row else None


def _get_or_insert(
    connection: Connection,
    table: Table,
    id_column: str,
    lookup: dict[str, Any],
    values: dict[str, Any],
    *,
    update_existing: bool = False,
) -> int:
    existing_id = _find_one_id(connection, table, id_column, **lookup)
    if existing_id is not None:
        if update_existing:
            update_values = _available_columns(table, values)
            update_values.pop(id_column, None)
            if update_values:
                connection.execute(
                    update(table)
                    .where(table.c[id_column] == existing_id)
                    .values(**update_values)
                )
        return existing_id

    payload = _available_columns(table, {**lookup, **values})
    if id_column not in payload:
        payload[id_column] = _next_id(connection, table, id_column)

    connection.execute(insert(table).values(**payload))
    return int(payload[id_column])


def _insert_ignore(connection: Connection, table: Table, values: dict[str, Any]) -> None:
    """복합 UNIQUE 데이터는 중복 시 건너뜁니다."""
    try:
        with connection.begin_nested():
            connection.execute(insert(table).values(**_available_columns(table, values)))
    except IntegrityError:
        pass


def _sync_postgresql_sequence(
    connection: Connection,
    table: Table,
    pk_name: str,
) -> None:
    """수동 PK 입력 뒤 PostgreSQL 시퀀스를 현재 최댓값에 맞춥니다."""
    if connection.dialect.name != "postgresql" or pk_name not in table.c:
        return

    sequence_name = connection.execute(
        text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
        {
            "table_name": table.name,
            "column_name": pk_name,
        },
    ).scalar_one_or_none()

    if not sequence_name:
        return

    max_value = int(
        connection.execute(
            select(func.max(table.c[pk_name]))
        ).scalar_one_or_none()
        or 0
    )

    connection.execute(
        text(
            "SELECT setval("
            "CAST(:sequence_name AS regclass), "
            ":sequence_value, "
            ":is_called"
            ")"
        ),
        {
            "sequence_name": sequence_name,
            "sequence_value": max(max_value, 1),
            "is_called": max_value > 0,
        },
    )


def seed_demo_data() -> None:
    tables = _reflect(engine)
    _require_tables(
        tables,
        (
            "city",
            "region",
            "category",
            "user",
            "quest",
            "quest_submission",
            "community_post",
            "post_like",
            "comment",
            "team",
            "team_member",
        ),
    )

    city = tables["city"]
    region = tables["region"]
    category = tables["category"]
    user = tables["user"]
    quest = tables["quest"]
    submission = tables["quest_submission"]
    post = tables["community_post"]
    post_like = tables["post_like"]
    comment = tables["comment"]
    team = tables["team"]
    team_member = tables["team_member"]
    feed_hidden = tables.get("feed_hidden_preference")
    report = tables.get("report")
    team_invite = tables.get("team_invite")
    activity_log = tables.get("user_activity_log")

    password_hash = _password_hash(SEED_PASSWORD)

    with engine.begin() as connection:
        # 1. 지역 데이터
        seoul_city_id = _get_or_insert(
            connection,
            city,
            "city_id",
            {"city_name": "서울특별시"},
            {"created_at": NOW, "updated_at": NOW},
        )
        gyeonggi_city_id = _get_or_insert(
            connection,
            city,
            "city_id",
            {"city_name": "경기도"},
            {"created_at": NOW, "updated_at": NOW},
        )

        region_specs = [
            ("마포구", seoul_city_id),
            ("성동구", seoul_city_id),
            ("강남구", seoul_city_id),
            ("수원시", gyeonggi_city_id),
        ]
        region_ids: dict[str, int] = {}
        for region_name, city_id in region_specs:
            region_ids[region_name] = _get_or_insert(
                connection,
                region,
                "region_id",
                {"region_name": region_name},
                {"city_id": city_id, "created_at": NOW, "updated_at": NOW},
            )

        # 2. 카테고리 데이터
        category_ids: dict[str, int] = {}
        for name, code, icon_url in (
            (
                "환경",
                "environment",
                "https://cdn-icons-png.flaticon.com/512/1598/1598196.png",
            ),
            (
                "봉사",
                "volunteer",
                "https://cdn-icons-png.flaticon.com/512/3349/3349234.png",
            ),
            (
                "생활실천",
                "other",
                "https://cdn-icons-png.flaticon.com/512/2917/2917995.png",
            ),
        ):
            category_ids[name] = _get_or_insert(
                connection,
                category,
                "category_id",
                {"name": name},
                {
                    "code": code,
                    "icon_url": icon_url,
                    "is_active": True,
                    "created_at": NOW,
                    "updated_at": NOW,
                },
                update_existing=True,
            )

        difficulty_easy = _enum_value(quest, "difficulty", "EASY", "VERY_EASY", "NORMAL")
        difficulty_normal = _enum_value(quest, "difficulty", "NORMAL", "MEDIUM", "EASY")
        user_role = _enum_value(user, "role", "USER") if "role" in user.c else None
        admin_role = _enum_value(user, "role", "ADMIN") if "role" in user.c else None
        accepted_status = _enum_value(
            submission,
            "final_status",
            "ACCEPTED",
            "APPROVED",
            "SUCCESS",
        )

        # 3. 데모 사용자: 첫 계정은 팀장/커뮤니티 확인용
        user_specs = [
            ("leader", "민재 데모", "마포구", ["환경", "봉사"], [6, 18], difficulty_normal, 8, 12, [0.92, 0.15, 0.31]),
            ("green1", "초록지킴이", "마포구", ["환경"], [6, 18], difficulty_normal, 7, 21, [0.94, 0.12, 0.29]),
            ("green2", "플로깅러", "성동구", ["환경", "생활실천"], [6, 12], difficulty_easy, 6, 15, [0.90, 0.18, 0.35]),
            ("helper1", "따뜻한손", "마포구", ["봉사"], [12, 18], difficulty_normal, 9, 18, [0.25, 0.93, 0.20]),
            ("helper2", "나눔천사", "강남구", ["봉사", "생활실천"], [12, 18], difficulty_easy, 5, 9, [0.28, 0.88, 0.32]),
            ("daily1", "매일한걸음", "마포구", ["생활실천", "환경"], [6, 12], difficulty_easy, 4, 30, [0.81, 0.22, 0.52]),
            ("green3", "에코메이트", "수원시", ["환경"], [18], difficulty_normal, 8, 11, [0.86, 0.19, 0.38]),
            ("helper3", "봉사왕", "성동구", ["봉사"], [6, 12], difficulty_normal, 10, 25, [0.21, 0.96, 0.17]),
            ("daily2", "제로웨이스트", "강남구", ["생활실천", "환경"], [12, 18], difficulty_easy, 6, 14, [0.84, 0.24, 0.48]),
            ("mixed", "선행탐험가", "마포구", ["환경", "봉사", "생활실천"], [6, 12, 18], difficulty_normal, 7, 17, [0.70, 0.68, 0.35]),
        ]

        coordinates = {
            "마포구": (Decimal("37.5663"), Decimal("126.9019")),
            "성동구": (Decimal("37.5634"), Decimal("127.0369")),
            "강남구": (Decimal("37.5172"), Decimal("127.0473")),
            "수원시": (Decimal("37.2636"), Decimal("127.0286")),
        }

        user_ids: dict[str, int] = {}
        for index, (key, nickname, region_name, interests, active_time, preferred, level, streak, embedding) in enumerate(user_specs, 1):
            email = f"seed.{key}@{SEED_EMAIL_DOMAIN}"
            latitude, longitude = coordinates[region_name]
            values: dict[str, Any] = {
                "region_id": region_ids[region_name],
                "provider": None,
                "provider_user_id": None,
                "password_hash": password_hash,
                "nickname": nickname,
                "birthday": date(1990 + index, (index % 12) + 1, (index % 20) + 1),
                "category": interests,
                "active_time": active_time,
                "preferred_difficulty": preferred,
                "profile_embedding": embedding,
                "profile_image_url": f"https://i.pravatar.cc/300?img={index + 10}",
                "trust_score": 70 + index,
                "point_balance": 500 + index * 50,
                "current_xp": 300 + index * 80,
                "current_level": level,
                "daily_streak": streak,
                "is_active": True,
                "current_latitude": latitude,
                "current_longitude": longitude,
                "last_embedded_at": NOW - timedelta(hours=2),
                "created_at": NOW - timedelta(days=60 - index),
                "updated_at": NOW,
            }
            if user_role is not None:
                values["role"] = (
                    admin_role
                    if key == "leader" and admin_role is not None
                    else user_role
                )

            user_ids[key] = _get_or_insert(
                connection,
                user,
                "user_id",
                {"email": email},
                values,
                update_existing=True,
            )

        # 4. 퀘스트 데이터
        quest_target_solo = _enum_value(quest, "quest_target", "SOLO", "INDIVIDUAL")
        quest_target_team = _enum_value(quest, "quest_target", "TEAM", "GROUP")
        quest_type_good = _enum_value(quest, "quest_type", "GOOD_DEED", "VOLUNTEER")
        quest_type_volunteer = _enum_value(quest, "quest_type", "VOLUNTEER", "GOOD_DEED")
        quest_source = _enum_value(quest, "quest_source", "ADMIN", "AI", "USER")
        quest_status = _enum_value(quest, "quest_status", "NOT_STARTED", "ACTIVE", "IN_PROGRESS")

        quest_specs = [
            (
                "[SEED] 한강공원 플로깅",
                "환경",
                quest_target_solo,
                quest_type_good,
                "서울 마포구 한강공원",
                difficulty_easy,
                [6, 18],
                [0.94, 0.12, 0.29],
                "한강공원을 걸으며 쓰레기를 줍고 종류별로 분리배출하는 환경 실천 퀘스트입니다.",
            ),
            (
                "[SEED] 재활용품 올바르게 분리배출",
                "환경",
                quest_target_solo,
                quest_type_good,
                "서울 마포구",
                difficulty_easy,
                [6, 12],
                [0.89, 0.18, 0.35],
                "가정에서 나온 재활용품을 세척하고 올바른 기준에 맞춰 분리배출하는 퀘스트입니다.",
            ),
            (
                "[SEED] 유기동물 보호소 봉사",
                "봉사",
                quest_target_team,
                quest_type_volunteer,
                "서울 성동구",
                difficulty_normal,
                [12, 18],
                [0.22, 0.96, 0.18],
                "보호소 환경 정리와 유기동물 돌봄을 팀원들과 함께 수행하는 봉사 퀘스트입니다.",
            ),
            (
                "[SEED] 어르신 도시락 나눔",
                "봉사",
                quest_target_team,
                quest_type_volunteer,
                "서울 마포구",
                difficulty_normal,
                [6, 12],
                [0.26, 0.91, 0.24],
                "지역 어르신을 위한 도시락 포장과 전달을 함께하는 나눔 봉사 퀘스트입니다.",
            ),
            (
                "[SEED] 일회용품 없는 하루",
                "생활실천",
                quest_target_solo,
                quest_type_good,
                None,
                difficulty_easy,
                [6, 12, 18],
                [0.75, 0.22, 0.58],
                "텀블러와 다회용품을 사용해 하루 동안 일회용품 사용을 줄이는 생활 실천 퀘스트입니다.",
            ),
            (
                "[SEED] 우리 동네 환경정화 팀퀘스트",
                "환경",
                quest_target_team,
                quest_type_good,
                "서울 마포구",
                difficulty_normal,
                [6, 18],
                [0.92, 0.16, 0.31],
                "마포구 골목과 공원을 팀원들과 걸으며 쓰레기를 수거하고 분리배출하는 환경정화 퀘스트입니다.",
            ),
        ]

        quest_ids: list[int] = []
        for index, (
            title,
            category_name,
            target,
            qtype,
            location,
            difficulty,
            active_time,
            quest_embedding,
            description,
        ) in enumerate(quest_specs):
            quest_ids.append(
                _get_or_insert(
                    connection,
                    quest,
                    "quest_id",
                    {"quest_title": title},
                    {
                        "category_id": category_ids[category_name],
                        "creator_id": user_ids["leader"],
                        "quest_description": description,
                        "quest_target": target,
                        "quest_type": qtype,
                        "quest_source": quest_source,
                        "location": location,
                        "reward_point": 100 + index * 20,
                        "reward_exp": 80 + index * 10,
                        "difficulty": difficulty,
                        "estimated_duration": 30 + index * 10,
                        "active_time": active_time,
                        "quest_embedding": quest_embedding,
                        "quest_status": quest_status,
                        "created_at": NOW - timedelta(days=40 - index),
                        "updated_at": NOW,
                    },
                    update_existing=True,
                )
            )

        # 5. 최근 30일 승인 인증과 커뮤니티 게시글
        image_urls = [
            "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=1200",
            "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=1200",
            "https://images.unsplash.com/photo-1559027615-cd4628902d4a?w=1200",
            "https://images.unsplash.com/photo-1593113598332-cd288d649433?w=1200",
            "https://images.unsplash.com/photo-1542810634-71277d95dcbb?w=1200",
            "https://images.unsplash.com/photo-1618477461853-cf6ed80faba5?w=1200",
        ]
        captions = [
            "[SEED] 오늘 한강에서 플로깅 완료! 작은 실천이 모이면 큰 변화가 됩니다.",
            "[SEED] 분리배출 기준을 다시 확인하고 깨끗하게 정리했어요.",
            "[SEED] 보호소 친구들과 의미 있는 시간을 보냈습니다.",
            "[SEED] 도시락 나눔 봉사에 참여했어요. 따뜻한 하루였습니다.",
            "[SEED] 텀블러와 장바구니로 일회용품 없는 하루 성공!",
            "[SEED] 팀원들과 우리 동네 골목을 깨끗하게 정리했습니다.",
            "[SEED] 출근길에 보이는 쓰레기를 주워 작은 플로깅을 실천했어요.",
            "[SEED] 봉사활동은 함께할수록 더 즐겁다는 걸 느꼈습니다.",
            "[SEED] 오늘도 제로웨이스트에 한 걸음 가까워졌어요.",
            "[SEED] 선행 퀘스트 완료! 다음 퀘스트도 기대됩니다.",
            "[SEED] 주말 아침 환경정화로 상쾌하게 시작했습니다.",
            "[SEED] 지역 이웃과 함께해서 더 뜻깊었던 봉사였습니다.",
        ]

        submission_ids: list[int] = []
        post_ids: list[int] = []
        user_keys = list(user_ids)

        for index in range(12):
            owner_key = user_keys[index % len(user_keys)]
            owner_id = user_ids[owner_key]
            quest_id = quest_ids[index % len(quest_ids)]
            submitted_at = NOW - timedelta(days=index % 18, hours=index)
            media_url = image_urls[index % len(image_urls)]
            explain = f"[SEED] 데모 인증 기록 {index + 1}"

            existing_submission = connection.execute(
                select(submission.c.submission_id).where(
                    and_(
                        submission.c.user_id == owner_id,
                        submission.c.quest_id == quest_id,
                        submission.c.quest_explain == explain,
                    )
                )
            ).first()

            if existing_submission:
                submission_id = int(existing_submission[0])
            else:
                submission_id = _next_id(connection, submission, "submission_id")
                submission_values = {
                    "submission_id": submission_id,
                    "user_id": owner_id,
                    "quest_id": quest_id,
                    "reviewed_by": user_ids["leader"],
                    "attempt_number": 1,
                    "quest_explain": explain,
                    "media_url": media_url,
                    "extra_media_urls": [],
                    "media_hash": f"seed-media-{index + 1}",
                    "media_embedding": [0.8, 0.2 + index * 0.01, 0.3],
                    "ai_verdict": {"approved": True, "reason": "데모 승인 데이터"},
                    "ai_generated_suspicion": False,
                    "final_status": accepted_status,
                    "submitted_at": submitted_at,
                    "reviewed_at": submitted_at + timedelta(minutes=2),
                    "updated_at": submitted_at + timedelta(minutes=2),
                }
                if "media_type" in submission.c:
                    submission_values["media_type"] = _enum_value(
                        submission, "media_type", "IMAGE", "PHOTO"
                    )
                connection.execute(insert(submission).values(**_available_columns(submission, submission_values)))

            submission_ids.append(submission_id)

            caption = captions[index]
            existing_post = connection.execute(
                select(post.c.post_id).where(post.c.caption == caption)
            ).first()
            if existing_post:
                post_id = int(existing_post[0])
            else:
                post_id = _next_id(connection, post, "post_id")
                connection.execute(
                    insert(post).values(
                        **_available_columns(
                            post,
                            {
                                "post_id": post_id,
                                "user_id": owner_id,
                                "submission_id": submission_id,
                                "media_url": media_url,
                                "caption": caption,
                                "is_active": True,
                                "created_at": submitted_at + timedelta(minutes=5),
                                "updated_at": submitted_at + timedelta(minutes=5),
                            },
                        )
                    )
                )
            post_ids.append(post_id)

        # 6. 좋아요와 댓글: 게시글별 반응량을 다르게 만들어 알고리즘 정렬을 확인합니다.
        next_comment_id = _next_id(connection, comment, "comment_id")
        comment_texts = [
            "좋은 실천이에요!",
            "저도 다음에 함께하고 싶어요.",
            "꾸준히 실천하는 모습 멋집니다.",
            "우리 동네도 깨끗해졌으면 좋겠어요.",
        ]
        all_user_ids = list(user_ids.values())

        for post_index, post_id in enumerate(post_ids):
            reaction_count = 2 + (post_index % 6)
            for reacting_user_id in all_user_ids[:reaction_count]:
                _insert_ignore(
                    connection,
                    post_like,
                    {
                        "post_id": post_id,
                        "user_id": reacting_user_id,
                        "created_at": NOW - timedelta(hours=post_index),
                        "updated_at": NOW - timedelta(hours=post_index),
                    },
                )

            for comment_index in range(1 + post_index % 3):
                marker = f"[SEED-{post_index + 1}-{comment_index + 1}]"
                content = f"{marker} {comment_texts[(post_index + comment_index) % len(comment_texts)]}"
                exists = connection.execute(
                    select(comment.c.comment_id).where(
                        and_(comment.c.post_id == post_id, comment.c.content == content)
                    )
                ).first()
                if exists:
                    continue
                connection.execute(
                    insert(comment).values(
                        **_available_columns(
                            comment,
                            {
                                "comment_id": next_comment_id,
                                "post_id": post_id,
                                "user_id": all_user_ids[(post_index + comment_index + 1) % len(all_user_ids)],
                                "content": content,
                                "created_at": NOW - timedelta(hours=post_index),
                                "updated_at": NOW - timedelta(hours=post_index),
                            },
                        )
                    )
                )
                next_comment_id += 1

        # 7. 커뮤니티 관심 없음, 관리자 신고, 최근 7일 접속 추이
        if feed_hidden is not None:
            _insert_ignore(
                connection,
                feed_hidden,
                {
                    "user_id": user_ids["leader"],
                    "post_id": post_ids[8],
                    "created_at": NOW - timedelta(hours=3),
                    "updated_at": NOW - timedelta(hours=3),
                },
            )

        if report is not None:
            pending_report_status = _enum_value(
                report,
                "status",
                "PENDING",
            )
            expired_report_status = _enum_value(
                report,
                "status",
                "EXPIRED",
                "REJECTED",
            )
            report_specs = [
                (
                    user_ids["helper1"],
                    post_ids[0],
                    "[SEED] 관리자 신고 승인 흐름 확인용 신고입니다.",
                    pending_report_status,
                    NOW - timedelta(days=1),
                ),
                (
                    user_ids["helper2"],
                    post_ids[1],
                    "[SEED] 관리자 신고 목록과 상세 화면 확인용 신고입니다.",
                    pending_report_status,
                    NOW - timedelta(days=3),
                ),
                (
                    user_ids["daily1"],
                    post_ids[2],
                    "[SEED] 신고 만료 상태 필터 확인용 신고입니다.",
                    expired_report_status,
                    NOW - timedelta(days=35),
                ),
            ]

            for reporter_id, post_id, reason, status_value, created_at in report_specs:
                _insert_ignore(
                    connection,
                    report,
                    {
                        "reporter_id": reporter_id,
                        "reviewed_by": None,
                        "post_id": post_id,
                        "reason": reason,
                        "status": status_value,
                        "created_at": created_at,
                        "reviewed_at": None,
                        "updated_at": created_at,
                    },
                )

        if activity_log is not None:
            for day_offset in range(7):
                access_date = (NOW - timedelta(days=day_offset)).date()
                daily_user_count = max(4, len(all_user_ids) - day_offset)

                for activity_user_id in all_user_ids[:daily_user_count]:
                    _insert_ignore(
                        connection,
                        activity_log,
                        {
                            "user_id": activity_user_id,
                            "access_date": access_date,
                        },
                    )

        # 8. 챌린지 팀과 멤버
        team_status = _enum_value(team, "status", "RECRUITING", "ACTIVE")
        leader_role = _enum_value(team_member, "role_in_team", "LEADER")
        member_role = _enum_value(team_member, "role_in_team", "MEMBER")

        team_specs = [
            ("[SEED] 마포 플로깅 크루", quest_ids[5], "마포구", True, 6),
            ("[SEED] 주말 도시락 나눔팀", quest_ids[3], "마포구", True, 5),
            ("[SEED] 성동 보호소 메이트", quest_ids[2], "성동구", False, 4),
        ]

        team_ids: list[int] = []
        for index, (name, quest_id, region_name, is_public, max_members) in enumerate(team_specs):
            team_ids.append(
                _get_or_insert(
                    connection,
                    team,
                    "team_id",
                    {"name": name},
                    {
                        "leader_id": user_ids["leader"],
                        "quest_id": quest_id,
                        "password_hash": None if is_public else password_hash,
                        "notification": "[SEED] 함께 즐겁게 선행 퀘스트를 완료해요!",
                        "region": region_name,
                        "is_public": is_public,
                        "max_members": max_members,
                        "status": team_status,
                        "expires_at": NOW + timedelta(days=30 + index * 5),
                        "created_at": NOW - timedelta(days=5 - index),
                        "updated_at": NOW,
                    },
                    update_existing=True,
                )
            )

        next_team_member_id = _next_id(connection, team_member, "team_member_id")
        team_memberships = [
            (team_ids[0], user_ids["leader"], leader_role),
            (team_ids[0], user_ids["helper1"], member_role),
            (team_ids[1], user_ids["leader"], leader_role),
            (team_ids[1], user_ids["daily1"], member_role),
            (team_ids[2], user_ids["leader"], leader_role),
            (team_ids[2], user_ids["helper2"], member_role),
        ]
        for team_id, member_user_id, role_value in team_memberships:
            exists = connection.execute(
                select(team_member.c.team_member_id).where(
                    and_(
                        team_member.c.team_id == team_id,
                        team_member.c.user_id == member_user_id,
                    )
                )
            ).first()
            if exists:
                continue
            connection.execute(
                insert(team_member).values(
                    **_available_columns(
                        team_member,
                        {
                            "team_member_id": next_team_member_id,
                            "team_id": team_id,
                            "user_id": member_user_id,
                            "role_in_team": role_value,
                            "joined_at": NOW - timedelta(days=3),
                            "updated_at": NOW,
                        },
                    )
                )
            )
            next_team_member_id += 1

        # 9. 팀 초대 상태: 초대 목록과 재초대 가능 조건을 확인합니다.
        if team_invite is not None:
            invite_user_column = (
                "user_id"
                if "user_id" in team_invite.c
                else "invited_user_id"
            )
            pending_invite_status = _enum_value(
                team_invite,
                "status",
                "PENDING",
            )
            rejected_invite_status = _enum_value(
                team_invite,
                "status",
                "REJECTED",
            )

            _insert_ignore(
                connection,
                team_invite,
                {
                    "team_id": team_ids[1],
                    invite_user_column: user_ids["green3"],
                    "status": pending_invite_status,
                    "expires_at": NOW + timedelta(days=20),
                    "created_at": NOW - timedelta(days=2),
                    "updated_at": NOW - timedelta(days=2),
                },
            )
            _insert_ignore(
                connection,
                team_invite,
                {
                    "team_id": team_ids[0],
                    invite_user_column: user_ids["helper2"],
                    "status": rejected_invite_status,
                    "expires_at": NOW + timedelta(days=10),
                    "created_at": NOW - timedelta(days=12),
                    "updated_at": NOW - timedelta(days=10),
                },
            )

        # 수동으로 입력한 PK 다음에 앱이 새 데이터를 생성해도 충돌하지 않도록 보정합니다.
        for sequence_table, pk_name in (
            (city, "city_id"),
            (region, "region_id"),
            (category, "category_id"),
            (user, "user_id"),
            (quest, "quest_id"),
            (submission, "submission_id"),
            (post, "post_id"),
            (comment, "comment_id"),
            (team, "team_id"),
            (team_member, "team_member_id"),
        ):
            _sync_postgresql_sequence(
                connection,
                sequence_table,
                pk_name,
            )

    print("\n" + "=" * 68)
    print("GoodDeedQuest 데모 데이터 생성 완료")
    print("=" * 68)
    print(f"관리자·팀장 계정 : seed.leader@{SEED_EMAIL_DOMAIN}")
    print(f"공통 비밀번호   : {SEED_PASSWORD}")
    print("비공개 팀 비밀번호도 동일합니다.")
    print(
        "생성 범위        : 사용자 10명 / 퀘스트 6개 / "
        "인증·게시글 12개 / 팀 3개"
    )
    print("추천 확인 팀     : [SEED] 마포 플로깅 크루")
    print("\n이제 Backend와 AI 서버를 실행한 뒤 Swagger 또는 모바일 앱에서 확인하세요.")


def _delete_where_in(
    connection: Connection,
    table: Table,
    column_name: str,
    values: Iterable[int],
) -> int:
    """대상 값이 있을 때만 DELETE를 실행하고 삭제 행 수를 반환합니다."""
    value_list = list(values)
    if not value_list or column_name not in table.c:
        return 0
    result = connection.execute(delete(table).where(table.c[column_name].in_(value_list)))
    return int(result.rowcount or 0)


def _set_null_where_in(
    connection: Connection,
    table: Table,
    column_name: str,
    values: Iterable[int],
) -> int:
    """Seed 사용자를 검토자로 참조하는 외부 데이터의 FK를 안전하게 비웁니다."""
    value_list = list(values)
    if not value_list or column_name not in table.c:
        return 0

    result = connection.execute(
        update(table)
        .where(table.c[column_name].in_(value_list))
        .values({column_name: None})
    )
    return int(result.rowcount or 0)


def delete_seed_data() -> None:
    """Seed 계정과 그 계정에 연결된 데모 데이터만 외래키 역순으로 삭제합니다."""
    tables = _reflect(engine)
    _require_tables(
        tables,
        (
            "user",
            "quest",
            "quest_submission",
            "community_post",
            "post_like",
            "comment",
            "team",
            "team_member",
        ),
    )

    user = tables["user"]
    quest = tables["quest"]
    submission = tables["quest_submission"]
    post = tables["community_post"]
    post_like = tables["post_like"]
    comment = tables["comment"]
    team = tables["team"]
    team_member = tables["team_member"]

    deleted: dict[str, int] = {}

    with engine.begin() as connection:
        seed_user_rows = connection.execute(
            select(user.c.user_id).where(
                user.c.email.like(f"seed.%@{SEED_EMAIL_DOMAIN}")
                | user.c.email.like(f"seed.%@{LEGACY_SEED_EMAIL_DOMAIN}")
            )
        ).all()
        seed_user_ids = [int(row[0]) for row in seed_user_rows]

        quest_conditions = [
            quest.c.quest_title.like("[SEED]%"),
        ]
        if "creator_id" in quest.c:
            quest_conditions.append(
                quest.c.creator_id.in_(seed_user_ids or [-1])
            )

        seed_quest_rows = connection.execute(
            select(quest.c.quest_id).where(
                quest_conditions[0]
                if len(quest_conditions) == 1
                else quest_conditions[0] | quest_conditions[1]
            )
        ).all()
        seed_quest_ids = [int(row[0]) for row in seed_quest_rows]

        seed_submission_rows = connection.execute(
            select(submission.c.submission_id).where(
                submission.c.quest_explain.like("[SEED]%")
                | submission.c.user_id.in_(seed_user_ids or [-1])
                | submission.c.quest_id.in_(seed_quest_ids or [-1])
            )
        ).all()
        seed_submission_ids = [int(row[0]) for row in seed_submission_rows]

        seed_post_rows = connection.execute(
            select(post.c.post_id).where(
                post.c.caption.like("[SEED]%")
                | post.c.user_id.in_(seed_user_ids or [-1])
                | post.c.submission_id.in_(seed_submission_ids or [-1])
            )
        ).all()
        seed_post_ids = [int(row[0]) for row in seed_post_rows]

        seed_team_rows = connection.execute(
            select(team.c.team_id).where(
                team.c.name.like("[SEED]%")
                | team.c.leader_id.in_(seed_user_ids or [-1])
                | team.c.quest_id.in_(seed_quest_ids or [-1])
            )
        ).all()
        seed_team_ids = [int(row[0]) for row in seed_team_rows]

        # Seed 관리자가 실제 테스트 데이터의 검토자로 남아 있어도 사용자 삭제가 막히지 않게 합니다.
        deleted["quest_submission.reviewed_by(null)"] = _set_null_where_in(
            connection,
            submission,
            "reviewed_by",
            seed_user_ids,
        )
        report_table = tables.get("report")
        if report_table is not None:
            deleted["report.reviewed_by(null)"] = _set_null_where_in(
                connection,
                report_table,
                "reviewed_by",
                seed_user_ids,
            )

        # Seed 사용자로 앱을 테스트하며 생성된 부가 데이터도 FK 역순으로 정리합니다.
        seed_purchase_ids: list[int] = []
        purchase_table = tables.get("purchase")
        if (
            purchase_table is not None
            and "purchase_id" in purchase_table.c
            and "user_id" in purchase_table.c
        ):
            seed_purchase_ids = [
                int(row[0])
                for row in connection.execute(
                    select(purchase_table.c.purchase_id).where(
                        purchase_table.c.user_id.in_(seed_user_ids or [-1])
                    )
                ).all()
            ]

        seed_ai_log_ids: list[int] = []
        ai_log_table = tables.get("ai_recommendation_log")
        if (
            ai_log_table is not None
            and "ai_log_id" in ai_log_table.c
            and "user_id" in ai_log_table.c
        ):
            seed_ai_log_ids = [
                int(row[0])
                for row in connection.execute(
                    select(ai_log_table.c.ai_log_id).where(
                        ai_log_table.c.user_id.in_(seed_user_ids or [-1])
                    )
                ).all()
            ]

        optional_deletes = (
            ("ai_recommendation", "ai_log_id", seed_ai_log_ids),
            ("ai_recommendation", "quest_id", seed_quest_ids),
            ("point_transaction", "submission_id", seed_submission_ids),
            ("point_transaction", "purchase_id", seed_purchase_ids),
            ("point_transaction", "user_id", seed_user_ids),
            ("competition_contribution", "submission_id", seed_submission_ids),
            ("competition_contribution", "user_id", seed_user_ids),
            ("team_invite", "team_id", seed_team_ids),
            ("team_invite", "user_id", seed_user_ids),
            ("team_invite", "invited_user_id", seed_user_ids),
            ("feed_hidden_preference", "post_id", seed_post_ids),
            ("feed_hidden_preference", "user_id", seed_user_ids),
            ("report", "post_id", seed_post_ids),
            ("report", "reporter_id", seed_user_ids),
            ("user_report", "reported_user_id", seed_user_ids),
            ("user_report", "reporter_id", seed_user_ids),
            ("short_form", "user_id", seed_user_ids),
            ("shortform", "user_id", seed_user_ids),
            ("user_activity_log", "user_id", seed_user_ids),
            ("user_badge", "user_id", seed_user_ids),
        )
        for table_name, column_name, ids in optional_deletes:
            optional_table = tables.get(table_name)
            if optional_table is None:
                continue
            key = f"{table_name}.{column_name}"
            deleted[key] = deleted.get(key, 0) + _delete_where_in(
                connection, optional_table, column_name, ids
            )

        deleted["post_like(post)"] = _delete_where_in(connection, post_like, "post_id", seed_post_ids)
        deleted["post_like(user)"] = _delete_where_in(connection, post_like, "user_id", seed_user_ids)
        deleted["comment(post)"] = _delete_where_in(connection, comment, "post_id", seed_post_ids)
        deleted["comment(user)"] = _delete_where_in(connection, comment, "user_id", seed_user_ids)
        deleted["community_post"] = _delete_where_in(connection, post, "post_id", seed_post_ids)
        deleted["team_member(team)"] = _delete_where_in(connection, team_member, "team_id", seed_team_ids)
        deleted["team_member(user)"] = _delete_where_in(connection, team_member, "user_id", seed_user_ids)
        deleted["team"] = _delete_where_in(connection, team, "team_id", seed_team_ids)
        if purchase_table is not None:
            deleted["purchase"] = _delete_where_in(
                connection,
                purchase_table,
                "purchase_id",
                seed_purchase_ids,
            )
        if ai_log_table is not None:
            deleted["ai_recommendation_log"] = _delete_where_in(
                connection,
                ai_log_table,
                "ai_log_id",
                seed_ai_log_ids,
            )
        deleted["quest_submission"] = _delete_where_in(
            connection, submission, "submission_id", seed_submission_ids
        )
        deleted["quest"] = _delete_where_in(connection, quest, "quest_id", seed_quest_ids)
        deleted["user"] = _delete_where_in(connection, user, "user_id", seed_user_ids)

    print("\n" + "=" * 68)
    print("GoodDeedQuest 데모 데이터 삭제 완료")
    print("=" * 68)
    print(f"삭제한 Seed 사용자 : {deleted.get('user', 0)}명")
    print(f"삭제한 Seed 퀘스트 : {deleted.get('quest', 0)}개")
    print(f"삭제한 Seed 인증    : {deleted.get('quest_submission', 0)}개")
    print(f"삭제한 Seed 게시글  : {deleted.get('community_post', 0)}개")
    print(f"삭제한 Seed 팀      : {deleted.get('team', 0)}개")
    print("공용 지역(city/region)과 카테고리(category)는 삭제하지 않았습니다.")


def main() -> None:
    parser = argparse.ArgumentParser(description="GoodDeedQuest 데모 데이터 관리")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--delete",
        action="store_true",
        help="현재/이전 Seed 계정과 연결된 데모 데이터만 삭제합니다.",
    )
    mode.add_argument(
        "--reset",
        action="store_true",
        help="Seed 데이터만 삭제한 뒤 동일한 데모 계정으로 다시 생성합니다.",
    )
    args = parser.parse_args()

    if args.delete:
        delete_seed_data()
        return

    if args.reset:
        delete_seed_data()
        seed_demo_data()
        return

    seed_demo_data()


if __name__ == "__main__":
    main()
