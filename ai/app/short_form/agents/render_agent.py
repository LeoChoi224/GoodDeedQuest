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
import textwrap  # ⭐ 수정: 자막 줄바꿈(#213)을 위해 추가
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy import select

from ..models import BackgroundMusic
from ...common.config import settings  # ⭐ 수정: FONT_PATH를 settings에서 가져오기 위해 추가
from ...common.database import SessionLocal
from ...common.s3_client import download_file_from_s3, object_exists_in_s3, upload_file_to_s3
from ..state import ShortFormState

logger = logging.getLogger(__name__)

SCENE_DURATION_SECONDS = 3
# ⭐ 추가: 씬 전환이 칼같이 끊기던 문제 - 씬 사이를 짧게 크로스페이드한다.
FADE_DURATION_SECONDS = 0.5
# ⭐ 수정: 렌더링 시간 단축 요청 대응 - 기존 1080x1920(풀HD)은 scale/pad/drawtext
# 필터와 x264 인코딩 전부 픽셀 수에 비례해 느려진다. 9:16 비율은 그대로 유지한 채
# 720x1280(약 2배 적은 픽셀)으로 낮춰서 화질은 살짝 떨어지되 렌더링은 훨씬 빨라지게 한다.
OUTPUT_WIDTH = 720
OUTPUT_HEIGHT = 1280
# ⭐ 추가: 다운로드(S3)와 FFmpeg 인코딩 둘 다 병렬화해서 전체 렌더링 시간을 줄인다.
MAX_CONCURRENT_DOWNLOADS = 4

# ⭐ 수정(#213): 자막이 프레임 밖으로 밀려나던 버그 수정용 상수.
# fontsize 48 기준 malgun.ttf/NanumGothic 한글 글자 폭이 대략 32px이므로,
# 한 줄당 20자면 약 640px로 1080px 폭 안에 넉넉한 여백을 두고 들어간다.
# ⭐ 수정: OUTPUT_WIDTH/HEIGHT를 720x1280으로 낮추면서(기존 1080x1920 대비 2/3배)
# 자막 크기·여백도 같은 비율로 줄여 프레임 대비 상대적인 위치/크기가 그대로 유지되게 한다.
CAPTION_FONT_SIZE = 32
CAPTION_MAX_CHARS_PER_LINE = 20
CAPTION_LINE_SPACING = 14
CAPTION_LINE_HEIGHT = CAPTION_FONT_SIZE + CAPTION_LINE_SPACING  # 줄 간 세로 피치(대략치)
CAPTION_BOTTOM_MARGIN = 120  # 프레임 하단에서 자막까지의 여백(px)


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
        # ⭐ 수정: 렌더링 시간 단축 - 씬 소스(이미지/동영상)와 BGM 다운로드를 전부 동시에
        # 처리해서 S3 왕복 시간을 합산하지 않고 겹치게 한다(Vision Agent 병렬화와 같은 이유).
        with ThreadPoolExecutor(max_workers=min(MAX_CONCURRENT_DOWNLOADS, len(media_keys) + 1)) as executor:
            scene_futures = [
                executor.submit(_download_one_scene_source, idx, media_key, work_dir)
                for idx, media_key in enumerate(media_keys)
            ]
            bgm_future = executor.submit(_download_bgm, bgm_id, work_dir)
            scene_sources = [f.result() for f in scene_futures]
            bgm_local_path = bgm_future.result()

        output_path = os.path.join(work_dir, "render_result.mp4")
        cmd = _build_ffmpeg_command(scene_sources, captions, bgm_local_path, output_path)

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


class SceneSource:
    """씬 하나의 로컬 파일 경로와, 그게 정지 이미지인지 동영상인지를 담는다."""

    __slots__ = ("path", "is_video")

    def __init__(self, path: str, is_video: bool):
        self.path = path
        self.is_video = is_video


_VIDEO_EXTENSIONS = (".mp4", ".mov")


def _resolve_video_source_key(media_key: str) -> str | None:
    """
    media_key가 backend의 get_video_thumbnail_key()로 만들어진 동영상 대표 프레임
    썸네일(패턴: "{원본 동영상 key, 확장자 제외}_thumb.jpg")이면 원본 동영상 S3 key를
    돌려주고, 아니면 None을 돌려준다.

    ⭐ 추가: 인증 동영상도 숏폼 소재로 고를 수 있게 됐지만, 지금까지는 대표 프레임
    1장만 정지 이미지로 썼다 - 실제 동영상 구간이 최종 숏폼에 전혀 반영되지 않았다.
    백엔드가 썸네일을 만들 때 쓰는 이름 규칙을 거꾸로 풀어서, 이 씬이 원래 동영상이었는지
    판별해 렌더링에는 정지 프레임 대신 실제 동영상 구간을 쓴다.

    주의: get_video_thumbnail_key()는 원본 확장자를 뗀 뒤 "_thumb.jpg"를 붙인다
    (예: ".../xxx.mp4" -> ".../xxx_thumb.jpg", 확장자가 사라짐) - 그래서 "_thumb.jpg"만
    떼어내면 확장자 없는 base_key만 남는다. 원래 확장자를 알 수 없으므로 흔한 동영상
    확장자를 하나씩 붙여보며 실제로 S3에 존재하는지 확인한다.
    """
    suffix = "_thumb.jpg"
    if not media_key.endswith(suffix):
        return None
    base_key = media_key[: -len(suffix)]
    for extension in _VIDEO_EXTENSIONS:
        candidate = base_key + extension
        if object_exists_in_s3(candidate):
            return candidate
    return None


def _download_one_scene_source(idx: int, media_key: str, work_dir: str) -> SceneSource:
    """씬 하나를 다운로드한다 - 동영상에서 뽑은 썸네일이면 원본 동영상을, 아니면 그
    media_key 그대로(사진)를 받아온다."""
    video_key = _resolve_video_source_key(media_key)
    if video_key:
        local_path = os.path.join(work_dir, f"scene_{idx}{Path(video_key).suffix or '.mp4'}")
        download_file_from_s3(video_key, local_path)
        return SceneSource(local_path, is_video=True)

    suffix = Path(media_key).suffix or ".jpg"
    local_path = os.path.join(work_dir, f"scene_{idx}{suffix}")
    download_file_from_s3(media_key, local_path)
    return SceneSource(local_path, is_video=False)


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
    scene_sources: list[SceneSource],
    captions: list[str],
    bgm_local_path: str,
    output_path: str,
) -> list[str]:
    """씬(이미지/동영상) + 자막 오버레이 + 씬 전환 크로스페이드 + BGM 합성을 위한
    FFmpeg 명령어를 구성한다."""
    scene_count = len(scene_sources)
    font_path_escaped = _escape_ffmpeg_path(settings.FONT_PATH)  # ⭐ 수정: OS별 경로를 settings에서 주입받음

    cmd = ["ffmpeg", "-y"]
    for source in scene_sources:
        if source.is_video:
            # ⭐ 추가: 실제 동영상 구간을 소재로 쓴다 - 원본이 SCENE_DURATION_SECONDS보다
            # 짧아도 -stream_loop로 채우고, 길면 -t로 그만큼만 잘라서 항상 같은 길이가
            # 되게 한다(뒤에 나오는 xfade 전환 시간 계산이 씬 길이가 고정이라는 가정에
            # 의존하기 때문).
            cmd += ["-stream_loop", "-1", "-t", str(SCENE_DURATION_SECONDS), "-i", source.path]
        else:
            cmd += ["-loop", "1", "-t", str(SCENE_DURATION_SECONDS), "-i", source.path]
    cmd += ["-i", bgm_local_path]

    scene_filters = [
        _build_scene_filter(idx, captions[idx] if idx < len(captions) else "", font_path_escaped)
        for idx in range(scene_count)
    ]
    transition_filter, final_label = _build_transition_filter(scene_count)

    filters = scene_filters + ([transition_filter] if transition_filter else [])
    filter_complex = ";".join(filters)

    cmd += [
        "-filter_complex", filter_complex,
        "-map", f"[{final_label}]",
        "-map", f"{scene_count}:a",
        "-shortest",
        "-c:v", "libx264",
        # ⭐ 수정: 렌더링 시간 추가 단축 - veryfast보다 더 빠른 ultrafast로 올리고,
        # 인코더가 사용 가능한 CPU 코어를 전부 쓰도록 threads를 명시한다. 화질은
        # 조금 더 낮아지지만 짧은 숏폼 영상 용도로는 충분하다.
        "-preset", "ultrafast",
        "-crf", "26",
        "-threads", "0",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    return cmd


def _build_scene_filter(idx: int, caption: str, font_path_escaped: str) -> str:
    """씬 하나의 필터 체인을 만든다: fps 통일 + 스케일/패딩 -> 자막(줄마다 별도
    drawtext로 각각 가운데 정렬). 최종 출력 라벨은 v{idx}.

    ⭐ 수정: 자막이 2줄일 때 왼쪽으로 치우쳐 보이던 문제 - 기존엔 여러 줄을
    text='줄1\\n줄2' 형태로 drawtext 하나에 다 넣고 x=(w-text_w)/2로 정렬했는데,
    drawtext는 여러 줄 텍스트의 text_w를 "가장 긴 줄" 기준 하나로 계산해서 짧은
    줄은 중앙에 오지 않고 왼쪽 정렬처럼 보였다. 줄마다 별도의 drawtext 필터로
    나눠서 각 줄을 독립적으로 가운데 정렬한다.
    ⭐ 추가: fps=25로 통일 - 정지 이미지(기본 25fps)와 실제 동영상 씬(원본 fps가
    30/60 등으로 제각각)을 섞어도 뒤의 xfade 전환이 프레임레이트 불일치로 깨지지
    않게 한다.
    """
    caption_lines = _wrap_caption(caption)
    n_lines = len(caption_lines)
    top_y = OUTPUT_HEIGHT - CAPTION_BOTTOM_MARGIN - (n_lines * CAPTION_LINE_HEIGHT)

    base_label = f"s{idx}base"
    parts = [
        f"[{idx}:v]fps=25,scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[{base_label}]"
    ]

    current_label = base_label
    for line_idx, line in enumerate(caption_lines):
        line_escaped = _escape_drawtext_text(line)
        y = top_y + line_idx * CAPTION_LINE_HEIGHT
        is_last_line = line_idx == n_lines - 1
        out_label = f"v{idx}" if is_last_line else f"s{idx}l{line_idx}"
        parts.append(
            f"[{current_label}]drawtext=fontfile='{font_path_escaped}':text='{line_escaped}':"
            f"fontsize={CAPTION_FONT_SIZE}:fontcolor=white:borderw=3:bordercolor=black:"
            f"x=(w-text_w)/2:y={y}[{out_label}]"
        )
        current_label = out_label

    return ";".join(parts)


def _build_transition_filter(scene_count: int) -> tuple[str | None, str]:
    """씬들을 이어붙이는 필터를 만든다.

    ⭐ 추가: 기존 concat은 씬 사이가 칼같이 끊겨서, xfade로 짧게(FADE_DURATION_SECONDS)
    크로스페이드하며 이어붙인다. 씬이 1개뿐이면 이어붙일 게 없으니 그대로 둔다.

    반환값: (filter_complex에 이어붙일 필터 문자열 또는 None, 최종 비디오 스트림 라벨)
    """
    if scene_count <= 1:
        return None, "v0"

    parts = []
    current_label = "v0"
    # xfade는 "지금까지 이어붙인 스트림의 길이" 기준으로 offset(전환이 시작되는 시점)을
    # 잡아야 해서, 이전 xfade로 겹쳐진 만큼(FADE_DURATION_SECONDS) 줄어든 누적 길이를
    # 계속 추적한다.
    cumulative_seconds = float(SCENE_DURATION_SECONDS)
    for idx in range(1, scene_count):
        offset = cumulative_seconds - FADE_DURATION_SECONDS
        is_last = idx == scene_count - 1
        out_label = "outv" if is_last else f"vx{idx}"
        parts.append(
            f"[{current_label}][v{idx}]xfade=transition=fade:duration={FADE_DURATION_SECONDS}:"
            f"offset={offset}[{out_label}]"
        )
        current_label = out_label
        cumulative_seconds += SCENE_DURATION_SECONDS - FADE_DURATION_SECONDS

    return ";".join(parts), "outv"


def _wrap_caption(text: str) -> list[str]:  # ⭐ 수정(#213): 자막 줄바꿈
    """자막을 CAPTION_MAX_CHARS_PER_LINE 기준으로 여러 줄로 줄바꿈.

    공백 단위로 먼저 나누고, 한 단어(공백으로 구분되지 않는 덩어리)가 그 자체로
    기준 길이를 넘으면 강제로 잘라서라도 줄바꿈한다(break_long_words=True) -
    그렇지 않으면 긴 단어 하나가 여전히 프레임 폭을 넘어갈 수 있음.
    """
    if not text:
        return [""]
    lines = textwrap.wrap(
        text, width=CAPTION_MAX_CHARS_PER_LINE, break_long_words=True, break_on_hyphens=False
    )
    return lines or [""]


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
