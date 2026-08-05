import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from backend.app.common.config import get_setting  # AWS_REGION, S3_BUCKET_NAME 등 환경설정

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

# ---------------------------------------------------------------------------
# S3 클라이언트 & Presigned URL
#
# Presigned URL: S3 접근 권한을 임시로 부여하는 서명된 URL.
# 서버가 파일을 직접 주고받지 않고, 클라이언트(RN 앱)가 이 URL로 S3에
# 직접 업로드/다운로드하게 해서 서버 부하를 줄이는 방식.
# ---------------------------------------------------------------------------

# boto3 S3 클라이언트는 모듈 로드 시 한 번만 생성해서 재사용 (매 요청마다 새로 만들지 않음)
_s3_client = boto3.client(
    "s3",
    region_name=get_setting().AWS_REGION,
    aws_access_key_id=get_setting().AWS_ACCESS_KEY_ID.get_secret_value(),
    aws_secret_access_key=get_setting().AWS_SECRET_ACCESS_KEY.get_secret_value(),
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"})
)

PRESIGNED_UPLOAD_EXPIRE_SECONDS = 300      # 5분 - 업로드용은 짧게 (클라이언트가 바로 씀)
PRESIGNED_DOWNLOAD_EXPIRE_SECONDS = 3600   # 1시간 - 조회용은 폴링/재생 도중 만료되지 않도록 여유
COMMUNITY_VIDEO_TRANSCODE_TIMEOUT_SECONDS = 120


class CommunityVideoTranscodeTimeoutError(RuntimeError):
    """커뮤니티 동영상 변환 제한 시간을 초과했을 때 발생합니다."""


def generate_upload_presigned_url(s3_key: str, content_type: str) -> str:
    """
    클라이언트가 직접 S3에 파일을 업로드할 수 있도록 presigned PUT URL 발급.
    (배경음악 업로드, 최종 영상 업로드 등에 사용)

    Args:
        s3_key: 업로드될 S3 객체 키 (예: "shortform/{shortform_id}/output.mp4")
        content_type: 업로드할 파일의 MIME 타입 (예: "video/mp4")
    """
    return _s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": get_setting().S3_BUCKET_NAME,
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=PRESIGNED_UPLOAD_EXPIRE_SECONDS,
    )


def upload_bytes(s3_key: str, data: bytes, content_type: str) -> None:
    """
    서버가 직접 바이트를 S3에 업로드한다 (시드/데모 데이터용 - 평소 앱 흐름은
    presigned PUT URL로 클라이언트가 직접 업로드하므로 이 함수를 쓰지 않는다).
    """
    _s3_client.put_object(
        Bucket=get_setting().S3_BUCKET_NAME,
        Key=s3_key,
        Body=data,
        ContentType=content_type,
    )

def copy_s3_object(source_key: str, destination_key: str) -> None:
    """같은 버킷 안에서 S3 객체를 별도의 key로 실제 복사합니다."""

    bucket_name = get_setting().S3_BUCKET_NAME

    _s3_client.copy_object(
        Bucket=bucket_name,
        CopySource={
            "Bucket": bucket_name,
            "Key": source_key,
        },
        Key=destination_key,
        MetadataDirective="COPY",
    )
"""                         민재 추가
submission/1/10/원본.jpg
         ↓ 실제 S3 복사
community/1/100/새UUID.jpg
URL 문자열만 복사하는 것이 아니라 S3 객체 자체를 복사하는 코드
"""

def transcode_s3_video_for_community(
    source_key: str,
    destination_key: str,
) -> None:
    """
    인증 원본 동영상을 커뮤니티 재생용 480p MP4로 변환합니다.

    원본 submission 객체는 유지하고, 변환 결과만 community 경로에
    저장하므로 AI 인증 원본과 커뮤니티 재생 파일을 분리할 수 있습니다.
    """

    bucket_name = get_setting().S3_BUCKET_NAME

    with tempfile.TemporaryDirectory() as temp_directory:
        temp_path = Path(temp_directory)
        source_path = temp_path / "source.mp4"
        output_path = temp_path / "community.mp4"

        # S3의 인증 원본을 백엔드 임시 폴더로 다운로드합니다.
        _s3_client.download_file(
            bucket_name,
            source_key,
            str(source_path),
        )

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source_path),

            # 세로·가로 비율을 유지하면서 높이를 480p로 축소합니다.
            "-vf",
            "scale=-2:480",

            # 대부분의 모바일 기기에서 안정적으로 재생되는 H.264 사용
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",

            # 낮은 화질·저용량 우선
            "-crf",
            "30",
            "-maxrate",
            "900k",
            "-bufsize",
            "1800k",

            # 다양한 모바일 기기와의 호환성 확보
            "-pix_fmt",
            "yuv420p",

            # 음성도 저용량으로 변환
            "-c:a",
            "aac",
            "-b:a",
            "64k",

            # MP4 재생 정보를 파일 앞부분으로 이동
            "-movflags",
            "+faststart",

            "-y",
            str(output_path),
        ]

        try:
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=COMMUNITY_VIDEO_TRANSCODE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise CommunityVideoTranscodeTimeoutError(
                "커뮤니티 동영상 변환 제한 시간인 "
                f"{COMMUNITY_VIDEO_TRANSCODE_TIMEOUT_SECONDS}초를 "
                "초과했습니다."
            ) from exc
        except FileNotFoundError as exc:
            raise RuntimeError(
                "커뮤니티 동영상 변환에 필요한 FFmpeg를 찾을 수 없습니다."
            ) from exc
        except subprocess.CalledProcessError as exc:
            error_message = (
                exc.stderr.strip()
                if exc.stderr
                else "알 수 없는 FFmpeg 오류"
            )

            raise RuntimeError(
                f"커뮤니티 동영상 변환에 실패했습니다: {error_message}"
            ) from exc

        # 변환된 저용량 MP4를 community 경로에 업로드합니다.
        _s3_client.upload_file(
            str(output_path),
            bucket_name,
            destination_key,
            ExtraArgs={
                "ContentType": "video/mp4",
                "CacheControl": "public, max-age=31536000, immutable",
            },
        )

# ⭐ 추가: 숏폼 사진 선택 화면은 이미지만 다루는데, GOOD_DEED 퀘스트 인증 자료는
# 동영상이다 - 그대로는 소재로 쓸 수 없으니 대표 프레임 1장을 뽑아 이미지로
# 등록해 소재 후보에 포함시킨다. transcode_s3_video_for_community와 같은
# 다운로드 -> ffmpeg -> 업로드 패턴을 재사용한다.
def get_video_thumbnail_key(video_key: str) -> str:
    """
    동영상 S3 key에서 대표 프레임 1장을 뽑아 이미지로 저장하고 그 S3 key를 돌려준다.
    같은 동영상에 대해 이미 뽑아둔 썸네일이 있으면 재추출하지 않고 그대로 재사용한다
    (조회할 때마다 다시 인코딩하면 느리고 매번 조금씩 다른 프레임이 나올 수 있음).
    """
    bucket_name = get_setting().S3_BUCKET_NAME
    base_key, _, _extension = video_key.rpartition(".")
    thumbnail_key = f"{base_key or video_key}_thumb.jpg"

    try:
        _s3_client.head_object(Bucket=bucket_name, Key=thumbnail_key)
        return thumbnail_key
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") not in ("404", "NoSuchKey"):
            raise

    with tempfile.TemporaryDirectory() as temp_directory:
        temp_path = Path(temp_directory)
        source_path = temp_path / "source.mp4"
        output_path = temp_path / "thumbnail.jpg"

        _s3_client.download_file(bucket_name, video_key, str(source_path))

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            "0.5",  # 검은 화면일 확률이 높은 0초 프레임을 피해 0.5초 지점에서 뽑는다
            "-i",
            str(source_path),
            "-frames:v",
            "1",
            # ⭐ 추가: 원본 동영상 해상도 그대로 프레임을 뽑으면(스케일 없음) 파일 크기가
            # 커서, 사진 선택 화면 그리드에서 이 썸네일만 로드가 오래 걸리거나 다른
            # 사진들보다 먼저/늦게 뜨는 등 로딩 속도가 들쭉날쭉해 보였다. 그리드 셀
            # 표시 용도로는 큰 해상도가 필요 없으므로 긴 변 기준 480px로 축소한다
            # (get_photo_preview_key와 동일한 상한을 둬서 사진/동영상 썸네일 로딩
            # 속도를 비슷하게 맞춘다).
            "-vf",
            "scale=480:480:force_original_aspect_ratio=decrease",
            "-q:v",
            "3",
            str(output_path),
        ]

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "동영상 썸네일 추출에 필요한 FFmpeg를 찾을 수 없습니다."
            ) from exc
        except subprocess.CalledProcessError as exc:
            error_message = exc.stderr.strip() if exc.stderr else "알 수 없는 FFmpeg 오류"
            raise RuntimeError(
                f"동영상 썸네일 추출에 실패했습니다: {error_message}"
            ) from exc

        _s3_client.upload_file(
            str(output_path),
            bucket_name,
            thumbnail_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )

    return thumbnail_key


# ⭐ 추가: 사진 선택 화면 그리드는 원본 사진(카메라 촬영본, 보통 수 MB)을 그대로
# 내려받아 표시하고 있었다 - 동영상 대표 프레임(get_video_thumbnail_key, 480px로 축소)보다
# 파일이 훨씬 커서, 그리드에 진입했을 때 동영상 썸네일은 금방 뜨는데 사진들은 원본 용량
# 그대로라 하나씩 늦게 뜨는 것처럼 보였다. 원본은 media_s3_key로 그대로 남겨(렌더링 시
# 화질 유지) 그리드 표시(media_url)에만 쓸 축소 미리보기를 별도로 만들어 캐싱한다.
def get_photo_preview_key(photo_key: str) -> str:
    """
    사진 S3 key에서 그리드 표시용 축소 미리보기(긴 변 기준 480px)를 만들어 저장하고
    그 S3 key를 돌려준다. 이미 만들어둔 미리보기가 있으면 재생성하지 않고 재사용한다.
    """
    bucket_name = get_setting().S3_BUCKET_NAME
    base_key, _, _extension = photo_key.rpartition(".")
    preview_key = f"{base_key or photo_key}_preview.jpg"

    try:
        _s3_client.head_object(Bucket=bucket_name, Key=preview_key)
        return preview_key
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") not in ("404", "NoSuchKey"):
            raise

    with tempfile.TemporaryDirectory() as temp_directory:
        temp_path = Path(temp_directory)
        source_path = temp_path / "source"
        output_path = temp_path / "preview.jpg"

        _s3_client.download_file(bucket_name, photo_key, str(source_path))

        with Image.open(source_path) as image:
            image = image.convert("RGB")  # PNG 등 알파 채널이 있으면 JPEG 저장 시 에러 방지
            image.thumbnail((480, 480))   # 원본 비율 유지한 채 긴 변 기준 480px 이하로 축소
            image.save(output_path, "JPEG", quality=75)

        _s3_client.upload_file(
            str(output_path),
            bucket_name,
            preview_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )

    return preview_key

def generate_download_presigned_url(s3_key: str) -> str:
    """
    저장된 s3_key를 실제 조회 가능한 presigned GET URL로 변환.
    ShortForm.final_video_s3_key, BackgroundMusic.s3_key 등 DB에는 key만 저장되어 있으므로,
    API 응답(schemas의 video_url, preview_url)으로 내려주기 직전에 이 함수로 변환한다.
    """
    return _s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": get_setting().S3_BUCKET_NAME,
            "Key": s3_key,
        },
        ExpiresIn=PRESIGNED_DOWNLOAD_EXPIRE_SECONDS,
    )