"""
City / Region 테이블 시드 스크립트

데이터 출처: 국가데이터처(통계청) SGIS "행정구역 통계 및 경계" ZIP 안의
  3. 코드집/1. 행정구역 코드(adm_code).xlsx  -> '2025년 6월' 시트
에서 시도/시군구만 추출해 만든 city_seed.csv, region_seed.csv 를 그대로 읽어서 저장함.
(원본 xlsx는 읍면동 단위까지 있는데, 지금 City/Region 모델은 시도/시군구 단위라 그 두 레벨만 뽑음)

PK를 SGIS 행정표준코드 그대로 사용:
- city_id   = 시도코드 (예: 서울특별시 = 11)
- region_id = 시도코드*1000 + 시군구코드 (예: 창원시 진해구 = 38115)
  -> 나중에 RGIS 경계 파일이나 다른 공공데이터랑 연계할 때도 같은 코드 체계라 매칭이 쉬움

주의:
- 창원시/고양시/수원시 등 "일반구가 있는 시"는 SGIS에 시 단위 행이 따로 없고
  "창원시 진해구" 처럼 구 단위로만 존재함 (region_seed.csv에 그대로 반영되어 있음).
  이 때문에 vms_crawler.py의 resolve_region_id()는 봉사지역 텍스트에 구 이름이
  없으면 여러 구가 동시에 매칭되고, 이 경우 봉사장소/제목 텍스트로 추가 매칭을 시도함.
- 이미 존재하는 city_id/region_id는 건드리지 않고(재실행해도 안전) 없는 것만 추가함.

실행 (프로젝트 루트에서):
    python -m backend.app.map.seed.seed_city_region
"""
import csv
import os

CSV_DIR = os.path.dirname(os.path.abspath(__file__))


def load_csv(filename: str) -> list[dict]:
    path = os.path.join(CSV_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed_cities(db) -> None:
    from backend.app.map.models import City

    rows = load_csv("city_seed.csv")
    created = 0
    for row in rows:
        city_id = int(row["city_id"])
        if db.get(City, city_id) is None:
            db.add(City(city_id=city_id, city_name=row["city_name"]))
            created += 1
    db.commit()
    print(f"City: {created}개 생성 (파일 기준 총 {len(rows)}개)")


def seed_regions(db) -> None:
    from backend.app.map.models import Region

    rows = load_csv("region_seed.csv")
    created = 0
    for row in rows:
        region_id = int(row["region_id"])
        if db.get(Region, region_id) is None:
            db.add(Region(
                region_id=region_id,
                city_id=int(row["city_id"]),
                region_name=row["region_name"],
            ))
            created += 1
    db.commit()
    print(f"Region: {created}개 생성 (파일 기준 총 {len(rows)}개)")


if __name__ == "__main__":
    # NOTE: SessionLocal 이름/경로는 실제 backend/app/common/database.py 구조에 맞춰 확인 필요
    from backend.app.common.database import SessionLocal

    db = SessionLocal()
    try:
        seed_cities(db)   # City가 Region의 FK라 순서 반드시 먼저
        seed_regions(db)
    finally:
        db.close()