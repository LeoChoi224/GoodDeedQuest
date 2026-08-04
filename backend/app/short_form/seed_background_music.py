"""
배경음악(BackgroundMusic) 시드.

신나는/발랄한/차분한 3개 무드 태그에 대해 실제 S3(bgm/ 경로)에 업로드된
mp3 10곡씩, 총 30곡을 시드한다. s3_key는 nullable=False이므로 실제
존재하는 오브젝트 키만 등록한다.

실행: python -m backend.app.short_form.seed_background_music
"""
import logging
from typing import Final

from backend import main as _main  # noqa: F401  전체 모델 매퍼 등록(User/UserBadge 등 relationship 해석용)
from backend.app.common.database import SessionLocal
from backend.app.short_form.models import BackgroundMusic


logger: Final = logging.getLogger(__name__)

# ⭐ 수정: title이 원본 스톡 음원 사이트의 파일명 슬러그 그대로 들어가 있어서
# (예: "apalonbeats-upbeat-upbeat-music-512926") 프론트 음악 버튼에 그대로 노출되면
# 보기 안 좋았다 - "{무드}노래{번호}" 형태의 사용자용 표시 이름으로 바꾼다.
# s3_key가 실제 오브젝트 키이자 자연 유니크 키 역할을 하므로 이를 기준으로 upsert한다.
BACKGROUND_MUSIC_SEED: Final = [
    {"title": "신나는노래1", "mood_tag": "신나는", "s3_key": "bgm/신나는-01.mp3"},
    {"title": "신나는노래2", "mood_tag": "신나는", "s3_key": "bgm/신나는-02.mp3"},
    {"title": "신나는노래3", "mood_tag": "신나는", "s3_key": "bgm/신나는-03.mp3"},
    {"title": "신나는노래4", "mood_tag": "신나는", "s3_key": "bgm/신나는-04.mp3"},
    {"title": "신나는노래5", "mood_tag": "신나는", "s3_key": "bgm/신나는-05.mp3"},
    {"title": "신나는노래6", "mood_tag": "신나는", "s3_key": "bgm/신나는-06.mp3"},
    {"title": "신나는노래7", "mood_tag": "신나는", "s3_key": "bgm/신나는-07.mp3"},
    {"title": "신나는노래8", "mood_tag": "신나는", "s3_key": "bgm/신나는-08.mp3"},
    {"title": "신나는노래9", "mood_tag": "신나는", "s3_key": "bgm/신나는-09.mp3"},
    {"title": "신나는노래10", "mood_tag": "신나는", "s3_key": "bgm/신나는-10.mp3"},
    {"title": "발랄한노래1", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-01.mp3"},
    {"title": "발랄한노래2", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-02.mp3"},
    {"title": "발랄한노래3", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-03.mp3"},
    {"title": "발랄한노래4", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-04.mp3"},
    {"title": "발랄한노래5", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-05.mp3"},
    {"title": "발랄한노래6", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-06.mp3"},
    {"title": "발랄한노래7", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-07.mp3"},
    {"title": "발랄한노래8", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-08.mp3"},
    {"title": "발랄한노래9", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-09.mp3"},
    {"title": "발랄한노래10", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-10.mp3"},
    {"title": "차분한노래1", "mood_tag": "차분한", "s3_key": "bgm/차분한-01.mp3"},
    {"title": "차분한노래2", "mood_tag": "차분한", "s3_key": "bgm/차분한-02.mp3"},
    {"title": "차분한노래3", "mood_tag": "차분한", "s3_key": "bgm/차분한-03.mp3"},
    {"title": "차분한노래4", "mood_tag": "차분한", "s3_key": "bgm/차분한-04.mp3"},
    {"title": "차분한노래5", "mood_tag": "차분한", "s3_key": "bgm/차분한-05.mp3"},
    {"title": "차분한노래6", "mood_tag": "차분한", "s3_key": "bgm/차분한-06.mp3"},
    {"title": "차분한노래7", "mood_tag": "차분한", "s3_key": "bgm/차분한-07.mp3"},
    {"title": "차분한노래8", "mood_tag": "차분한", "s3_key": "bgm/차분한-08.mp3"},
    {"title": "차분한노래9", "mood_tag": "차분한", "s3_key": "bgm/차분한-09.mp3"},
    {"title": "차분한노래10", "mood_tag": "차분한", "s3_key": "bgm/차분한-10.mp3"},
]


def seed_background_music() -> None:
    """신나는/발랄한/차분한 BGM 30곡을 s3_key 기준으로 멱등하게 적재한다."""
    with SessionLocal() as db:
        try:
            created_count = 0
            updated_count = 0

            for row in BACKGROUND_MUSIC_SEED:
                bgm = db.query(BackgroundMusic).filter_by(s3_key=row["s3_key"]).first()
                if bgm:
                    bgm.title = row["title"]
                    bgm.mood_tag = row["mood_tag"]
                    updated_count += 1
                    continue

                db.add(BackgroundMusic(
                    title=row["title"],
                    mood_tag=row["mood_tag"],
                    s3_key=row["s3_key"],
                ))
                created_count += 1

            db.commit()
            logger.info(f"BGM 시드 완료. 신규 {created_count}곡 / 기존 {updated_count}곡 갱신")

        except Exception as e:
            db.rollback()
            logger.error(f"BGM 시드 중 예외 발생. 에러: {str(e)}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_background_music()
