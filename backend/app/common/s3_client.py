import boto3
from botocore.config import Config
from backend.app.common.config import get_setting  # AWS_REGION, S3_BUCKET_NAME 등 환경설정

import subprocess
import tempfile
from pathlib import Path

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
            )
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