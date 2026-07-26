import logging

import boto3
from botocore.config import Config

from .config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# S3 클라이언트
#
# AI 서버는 S3 객체를 직접 로컬 파일로 다운로드해서(FFmpeg 입력으로 사용) 처리한다.
# backend와 달리 presigned URL은 발급하지 않는다.
# ---------------------------------------------------------------------------

# boto3 S3 클라이언트는 모듈 로드 시 한 번만 생성해서 재사용 (매 요청마다 새로 만들지 않음)
_s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)


def download_file_from_s3(s3_key: str, local_path: str) -> None:
    """
    S3 객체를 local_path 경로의 로컬 파일로 다운로드한다.
    (FFmpeg 렌더링 입력으로 사용할 이미지/BGM 파일 등)

    Args:
        s3_key: 다운로드할 S3 객체 키
        local_path: 저장할 로컬 파일 경로
    """
    try:
        _s3_client.download_file(settings.S3_BUCKET_NAME, s3_key, local_path)
        logger.info(f"[S3Client] 다운로드 성공: s3_key={s3_key} -> local_path={local_path}")
    except Exception:
        logger.exception(f"[S3Client] 다운로드 실패: s3_key={s3_key}")
        raise
