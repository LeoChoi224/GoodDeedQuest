"""제출 미디어 검사 유틸 — 파일 해시와 지각 해시(pHash) 계산·비교.

라우터는 HTTP 흐름만 다루고, 이미지·동영상을 실제로 뜯어보는 일은 여기서 한다.
"""
import hashlib
import os
import subprocess
import tempfile
from io import BytesIO
from typing import Optional

import imagehash
from PIL import Image

from backend.app.quest_verification.models import QuestSubmission

# pHash 거리 기준. 0이면 완전 동일이고, 값이 클수록 느슨하게 잡는다.
# 5 이하면 "같은 자료를 살짝 편집한 것"으로 본다.
PHASH_DISTANCE_THRESHOLD = 5


def compute_sha256(media_bytes: bytes) -> str:
    return hashlib.sha256(media_bytes).hexdigest()


def compute_phash(image_bytes: bytes) -> Optional[str]:
    try:
        image = Image.open(BytesIO(image_bytes))
        return str(imagehash.phash(image))
    except Exception:
        return None


def extract_frame(video_bytes: bytes) -> Optional[bytes]:
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "input.mp4")
        out = os.path.join(tmp, "frame.jpg")
        with open(src, "wb") as f:
            f.write(video_bytes)
        for seek in ("1", "0"):
            try:
                subprocess.run(
                    ["ffmpeg", "-ss", seek, "-i", src, "-frames:v", "1", "-q:v", "3", "-y", out],
                    capture_output=True, check=True,
                )
                if os.path.exists(out) and os.path.getsize(out) > 0:
                    with open(out, "rb") as fr:
                        return fr.read()
            except subprocess.CalledProcessError:
                continue
    return None


def compute_media_phash(media_bytes: bytes, is_video: bool) -> Optional[str]:
    source = extract_frame(media_bytes) if is_video else media_bytes
    return compute_phash(source) if source else None


def find_nearest_submission(repository, phash: str) -> tuple[Optional[QuestSubmission], Optional[int]]:

    target = imagehash.hex_to_hash(phash)
    nearest: Optional[QuestSubmission] = None
    nearest_distance: Optional[int] = None
    
    for past in repository.filter():
        for value in past.media_embedding or []:
            
            if not isinstance(value, str):
                continue
            try:
                distance = target - imagehash.hex_to_hash(value) 
            except (ValueError, TypeError):
                continue
            if nearest_distance is None or distance < nearest_distance:
                nearest, nearest_distance = past, distance
    
    return nearest, nearest_distance

def is_duplicate(distance: Optional[int]) -> bool:
    return distance is not None and distance <= PHASH_DISTANCE_THRESHOLD
