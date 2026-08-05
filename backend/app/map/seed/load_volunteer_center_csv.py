"""
VolunteerCenter(봉사센터) 테이블을 CSV에서 바로 로드하는 스크립트.

배경:
    vms_crawler.py로 실시간 크롤링하면 시간이 너무 오래 걸려서, 이미 크롤링해둔
    volunteer_center.csv(테이블 덤프 형태, center_id/region_id 등 실제 값 포함)를
    그대로 읽어서 DB에 업서트한다.

CSV 위치:
    이 스크립트와 같은 폴더(backend/app/map/seed/)에 volunteer_center.csv를 놓을 것.
    (seed_city_region.py가 city_seed.csv/region_seed.csv를 읽는 방식과 동일)

CSV 컬럼:
    center_id, region_id, vol_name, vol_address, target, vms_url, vol_qual, vol_act,
    vol_date, latitude, longitude, updated_at, vol_title, ai_category, embedding,
    quest_title, quest_summary
    -> VolunteerCenter 모델 컬럼과 1:1로 대응됨.

전제조건:
    region_id가 실제 Region 테이블에 있어야 하는 FK라서, seed_city_region.py를
    먼저 실행해서 City/Region이 채워져 있어야 한다.

동작:
    - center_id 기준으로 이미 있으면 필드 갱신(update), 없으면 새로 insert.
      (크롤러가 나중에 같은 center_id로 갱신해도 안전하게 재실행 가능)
    - latitude/longitude는 Decimal로, updated_at은 datetime으로, embedding은
      JSON 문자열이면 dict로 파싱해서 넣음. 빈 문자열은 전부 None으로 처리.
    - 다 끝나면 center_id가 explicit하게 들어갔기 때문에, 시퀀스를 현재 최대값으로
      맞춰서 이후 크롤러가 insert할 때 PK 충돌 안 나게 함.

실행 (프로젝트 루트에서):
    python -m backend.app.map.seed.load_volunteer_center_csv
"""
import csv
import json
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

CSV_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILENAME = "volunteer_center.csv"
COMMIT_BATCH_SIZE = 500


def _empty_to_none(value):
    if value is None:
        return None
    value = value.strip()
    return value if value != "" else None


def _parse_decimal(value):
    value = _empty_to_none(value)
    if value is None:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _parse_datetime(value):
    value = _empty_to_none(value)
    if value is None:
        return None
    # "2026-08-04 06:00:48.235503" 또는 마이크로초 없는 "2026-08-04 06:00:48" 둘 다 대응
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _parse_embedding(value):
    value = _empty_to_none(value)
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _row_to_values(row: dict) -> dict:
    return {
        "center_id": int(row["center_id"]),
        "region_id": int(row["region_id"]),
        "vol_name": _empty_to_none(row.get("vol_name")),
        "vol_address": _empty_to_none(row.get("vol_address")),
        "target": _empty_to_none(row.get("target")),
        "vms_url": _empty_to_none(row.get("vms_url")),
        "vol_qual": _empty_to_none(row.get("vol_qual")),
        "vol_act": _empty_to_none(row.get("vol_act")),
        "vol_date": _empty_to_none(row.get("vol_date")),
        "latitude": _parse_decimal(row.get("latitude")),
        "longitude": _parse_decimal(row.get("longitude")),
        "updated_at": _parse_datetime(row.get("updated_at")),
        "vol_title": _empty_to_none(row.get("vol_title")),
        "ai_category": _empty_to_none(row.get("ai_category")),
        "embedding": _parse_embedding(row.get("embedding")),
        "quest_title": _empty_to_none(row.get("quest_title")),
        "quest_summary": _empty_to_none(row.get("quest_summary")),
    }


def load_volunteer_centers(db) -> None:
    from backend.app.map.models import Region, VolunteerCenter

    path = os.path.join(CSV_DIR, CSV_FILENAME)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} 가 없습니다. volunteer_center.csv를 이 스크립트와 같은 폴더에 놓으세요."
        )

    existing_region_ids = {r.region_id for r in db.query(Region.region_id).all()}
    if not existing_region_ids:
        raise RuntimeError(
            "Region 데이터가 없습니다. backend.app.map.seed.seed_city_region 을 먼저 실행하세요."
        )

    created = 0
    updated = 0
    skipped_missing_region = 0
    pending = 0

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            values = _row_to_values(row)

            if values["region_id"] not in existing_region_ids:
                skipped_missing_region += 1
                continue

            existing = db.get(VolunteerCenter, values["center_id"])
            if existing:
                for key, value in values.items():
                    if key == "center_id":
                        continue
                    setattr(existing, key, value)
                updated += 1
            else:
                db.add(VolunteerCenter(**values))
                created += 1

            pending += 1
            if pending >= COMMIT_BATCH_SIZE:
                db.commit()
                pending = 0
                print(f"  진행 중... 신규 {created} / 갱신 {updated}")

    db.commit()

    # center_id를 explicit하게 넣었으니 시퀀스를 최대값으로 맞춰서 이후 크롤러 insert와 충돌 방지
    from sqlalchemy import text

    db.execute(text(
        "SELECT setval(pg_get_serial_sequence('volunteer_center', 'center_id'), "
        "(SELECT COALESCE(MAX(center_id), 1) FROM volunteer_center))"
    ))
    db.commit()

    print(
        f"완료. 신규 {created}개 / 갱신 {updated}개 "
        f"(region_id 없어서 건너뜀 {skipped_missing_region}개)"
    )


if __name__ == "__main__":
    from backend.app.common.database import SessionLocal

    db = SessionLocal()
    try:
        load_volunteer_centers(db)
    finally:
        db.close()