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

# s3_key가 실제 오브젝트 키이자 자연 유니크 키 역할을 하므로 이를 기준으로 upsert한다.
BACKGROUND_MUSIC_SEED: Final = [
    {"title": "apalonbeats-upbeat-upbeat-music-512926", "mood_tag": "신나는", "s3_key": "bgm/신나는-01.mp3"},
    {"title": "bombinsound-upbeat-rock-version-3-544113", "mood_tag": "신나는", "s3_key": "bgm/신나는-02.mp3"},
    {"title": "cinematic-soul-free-stock-music-for-videos-corporate-glow-511441", "mood_tag": "신나는", "s3_key": "bgm/신나는-03.mp3"},
    {"title": "cinematic-soul-motivational-upbeat-music-winning-spirit-511443", "mood_tag": "신나는", "s3_key": "bgm/신나는-04.mp3"},
    {"title": "jonasblakewood-upbeat-rock_60s-573487", "mood_tag": "신나는", "s3_key": "bgm/신나는-05.mp3"},
    {"title": "joyinsound-upbeat-waves-of-ocean-495981", "mood_tag": "신나는", "s3_key": "bgm/신나는-06.mp3"},
    {"title": "musicforpeople-hip-hop-upbeat-491996", "mood_tag": "신나는", "s3_key": "bgm/신나는-07.mp3"},
    {"title": "prettyjohn1-upbeat-exciting-background-music-free-523621", "mood_tag": "신나는", "s3_key": "bgm/신나는-08.mp3"},
    {"title": "the_mountain-upbeat-rock-492814", "mood_tag": "신나는", "s3_key": "bgm/신나는-09.mp3"},
    {"title": "verclub_music-upbeat-exciting-background-music-free-571032", "mood_tag": "신나는", "s3_key": "bgm/신나는-10.mp3"},
    {"title": "gr0za-fun-fun-party-music-569750", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-01.mp3"},
    {"title": "ikoliks_aj-fun-pop-background-music-419356", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-02.mp3"},
    {"title": "kaazoom-queen-of-the-couch-a-fun-song-for-cat-lovers-386495", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-03.mp3"},
    {"title": "kaazoom-sunshine-and-sandcastles-summer-childrenx27s-song-ukulele-385936", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-04.mp3"},
    {"title": "letzgowilhelm-john-smash-karts-theme-song-567427", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-05.mp3"},
    {"title": "moonpetalmedia-goodbye-retro-soul-pop-female-vocals-breakup-song-503503", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-06.mp3"},
    {"title": "mosesharrisjr-smooth-soul-217868", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-07.mp3"},
    {"title": "soulstream77-birds-flying-free-232344", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-08.mp3"},
    {"title": "sounovamusic-khao-khao-khao-thai-groove-for-fun-amp-dance-415247", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-09.mp3"},
    {"title": "universfield-emotional-acoustic-guitar-background-15s-232402", "mood_tag": "발랄한", "s3_key": "bgm/발랄한-10.mp3"},
    {"title": "apalonbeats-instrumental-song-549432", "mood_tag": "차분한", "s3_key": "bgm/차분한-01.mp3"},
    {"title": "clavier-music-relaxing-piano-for-sleeping-312507", "mood_tag": "차분한", "s3_key": "bgm/차분한-02.mp3"},
    {"title": "clavier-music-soft-memories-relaxing-piano-music-351872", "mood_tag": "차분한", "s3_key": "bgm/차분한-03.mp3"},
    {"title": "gensanmaier-gentle-instrumental-1-322812", "mood_tag": "차분한", "s3_key": "bgm/차분한-04.mp3"},
    {"title": "music_for_creators-peaceful-background-333476", "mood_tag": "차분한", "s3_key": "bgm/차분한-05.mp3"},
    {"title": "onetent-morning-relaxing-144011", "mood_tag": "차분한", "s3_key": "bgm/차분한-06.mp3"},
    {"title": "openmindaudio-simple-gospel-worship-song-a-simple-song-543995", "mood_tag": "차분한", "s3_key": "bgm/차분한-07.mp3"},
    {"title": "sigmamusicart-emotional-piano-music-256262", "mood_tag": "차분한", "s3_key": "bgm/차분한-08.mp3"},
    {"title": "soundgallerybydmitrytaras-winter-song-442061", "mood_tag": "차분한", "s3_key": "bgm/차분한-09.mp3"},
    {"title": "surprising_media-romantic-guitar-song-309094", "mood_tag": "차분한", "s3_key": "bgm/차분한-10.mp3"},
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
