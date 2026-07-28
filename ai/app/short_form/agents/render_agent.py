"""
FFmpeg Render Agent

입력: state["media_keys"], state["generated_captions"], state["bgm_match"]
출력: state["rendered_video_key"] (렌더링된 최종 영상의 S3 key)

처리 순서:
1. media_keys, BGM(s3_key는 bgm_id로 DB 재조회) 파일을 로컬 임시 디렉토리로 다운로드
2. FFmpeg으로 이미지(씬)마다 자막을 drawtext로 오버레이하고, concat으로 이어붙인 뒤
   BGM을 -shortest로 붙여 결과 mp4를 로컬에 생성
3. 결과 mp4를 S3에 업로드하고 그 key를 state["rendered_video_key"]에 반영,
   status를 "COMPLETED"로 설정 (#94)
4. 성공/실패 여부와 무관하게 로컬 임시 작업 디렉토리는 항상 삭제

TTS/나레이션 음성 트랙 없음 -- 오디오 트랙은 BGM만 사용.

⭐ 수정: FONT_PATH는 common/config.py의 settings.FONT_PATH를 참조한다.
   기본값은 로컬 Windows 경로(C:\\Windows\\Fonts\\malgun.ttf)이며, Docker(Linux) 배포
   시에는 FONT_PATH 환경변수로 /usr/share/fonts/truetype/nanum/NanumGothic.ttf를
   주입한다 (ai/Dockerfile에 fonts-nanum 설치되어 있음).
"""
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy import select

from ..models import BackgroundMusic
from ...common.config import settings  # ⭐ 수정: FONT_PATH를 settings에서 가져오기 위해 추가
from ...common.database import SessionLocal
from ...common.s3_client import download_file_from_s3, upload_file_to_s3
from ..state import ShortFormState

logger = logging.getLogger(__name__)

SCENE_DURATION_SECONDS = 3
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920


def render_agent(state: ShortFormState) -> ShortFormState:
    if state["status"] == "FAILED":
        print("[RenderAgent] 이전 단계 실패로 렌더링 스킵")
        return state

    shorts_id = state["shorts_id"]
    media_keys = state["media_keys"]
    captions = state["generated_captions"]
    bgm_id = state["bgm_match"]["bgm_id"]

    logger.info(
        f"[RenderAgent] media_keys={media_keys}, captions={captions}, bgm_id={bgm_id}"
    )

    work_dir = tempfile.mkdtemp(prefix=f"shortform_{shorts_id}_")

    try:
        image_paths = _download_scene_images(media_keys, work_dir)
        bgm_local_path = _download_bgm(bgm_id, work_dir)

        output_path = os.path.join(work_dir, "render_result.mp4")
        cmd = _build_ffmpeg_command(image_paths, captions, bgm_local_path, output_path)

        logger.info(f"[RenderAgent] FFmpeg 실행: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"[RenderAgent] 로컬 렌더링 완료: {output_path}")

        video_s3_key = f"shortform/{shorts_id}/render_result.mp4"
        upload_file_to_s3(output_path, video_s3_key)

        state["rendered_video_key"] = video_s3_key
        state["status"] = "COMPLETED"

    except subprocess.CalledProcessError as e:
        error_message = f"FFmpeg 렌더링 실패 (returncode={e.returncode}): {e.stderr}"
        logger.error(f"[RenderAgent] {error_message}")
        state["status"] = "FAILED"
        state["error_message"] = error_message

    except Exception as e:
        error_message = f"렌더링/업로드 중 오류 발생: {e}"
        logger.exception(f"[RenderAgent] {error_message}")
        state["status"] = "FAILED"
        state["error_message"] = error_message

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return state


def _download_scene_images(media_keys: list[str], work_dir: str) -> list[str]:
    """media_keys를 순서대로 work_dir에 다운로드하고 로컬 경로 리스트를 반환."""
    image_paths = []
    for idx, media_key in enumerate(media_keys):
        suffix = Path(media_key).suffix or ".jpg"
        local_path = os.path.join(work_dir, f"scene_{idx}{suffix}")
        download_file_from_s3(media_key, local_path)
        image_paths.append(local_path)
    return image_paths


def _download_bgm(bgm_id: int, work_dir: str) -> str:
    """bgm_id로 BackgroundMusic을 재조회해 s3_key를 얻고, work_dir에 다운로드."""
    with SessionLocal() as session:
        bgm = session.scalars(
            select(BackgroundMusic).where(BackgroundMusic.bgm_id == bgm_id)
        ).first()

    if bgm is None:
        raise RuntimeError(f"BackgroundMusic(bgm_id={bgm_id})를 찾을 수 없습니다.")

    suffix = Path(bgm.s3_key).suffix or ".mp3"
    local_path = os.path.join(work_dir, f"bgm{suffix}")
    download_file_from_s3(bgm.s3_key, local_path)
    return local_path


def _build_ffmpeg_command(
    image_paths: list[str],
    captions: list[str],
    bgm_local_path: str,
    output_path: str,
) -> list[str]:
    """씬(이미지) + 자막 오버레이 + BGM 합성을 위한 FFmpeg 명령어를 구성한다."""
    scene_count = len(image_paths)
    font_path_escaped = _escape_ffmpeg_path(settings.FONT_PATH)  # ⭐ 수정: OS별 경로를 settings에서 주입받음

    cmd = ["ffmpeg", "-y"]
    for image_path in image_paths:
        cmd += ["-loop", "1", "-t", str(SCENE_DURATION_SECONDS), "-i", image_path]
    cmd += ["-i", bgm_local_path]

    scene_filters = []
    for idx in range(scene_count):
        # 방어 코드: captions 개수가 media_keys보다 적을 경우 빈 자막으로 처리
        caption = captions[idx] if idx < len(captions) else ""
        caption_escaped = _escape_drawtext_text(caption)

        scene_filters.append(
            f"[{idx}:v]scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,"
            f"drawtext=fontfile='{font_path_escaped}':text='{caption_escaped}':"
            f"fontsize=48:fontcolor=white:borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y=h-th-120[v{idx}]"
        )

    concat_inputs = "".join(f"[v{idx}]" for idx in range(scene_count))
    concat_filter = f"{concat_inputs}concat=n={scene_count}:v=1:a=0[outv]"

    filter_complex = ";".join(scene_filters + [concat_filter])

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{scene_count}:a",
        "-shortest",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    return cmd


def _escape_drawtext_text(text: str) -> str:
    """FFmpeg drawtext 필터의 text='...' 안에 들어갈 텍스트 이스케이프.
    백슬래시 -> 콜론 -> 작은따옴표 순서로 처리해야 함 (순서 바뀌면 이중 이스케이프됨)."""
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("'", "\\'")
    return text


def _escape_ffmpeg_path(path: str) -> str:
    """fontfile= 등 filter 인자로 들어가는 경로 이스케이프.
    Windows 경로(C:\\...)의 드라이브 콜론과 역슬래시가 filtergraph 문법과 충돌하므로
    슬래시로 통일하고 콜론을 이스케이프한다."""
    path = path.replace("\\", "/")
    path = path.replace(":", "\\:")
    return path
