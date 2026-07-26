"""동영상 처리 유틸 — ffprobe/ffmpeg로 메타데이터를 읽고 프레임을 뽑는다.

그래프(graph.py)는 판정 흐름만 다루고, 영상을 실제로 뜯는 일은 여기서 한다.
"""
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Optional

import httpx


def probe_duration(path: str) -> float:
    """영상 길이(초). 읽지 못하면 0.0."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, check=True,
        )
        return float(out.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0.0


def probe_creation_time(path: str) -> Optional[datetime]:
    """영상에 적힌 촬영 시각. 없거나 읽지 못하면 None."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format_tags=creation_time",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, check=True,
        )
        raw = out.stdout.strip()
        if not raw:
            return None
        # 예: "2026-07-20T05:12:33.000000Z" — Z는 파이썬이 못 읽어서 +00:00으로 바꾼다
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        # 시간대가 없으면 UTC로 간주한다 (섞이면 뺄셈에서 TypeError가 난다)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (subprocess.CalledProcessError, ValueError):
        return None


def extract_frames(video_url: str, count: int = 8) -> tuple[list[bytes], Optional[datetime]]:
    """영상을 받아 시간축을 균등하게 나눠 프레임을 뽑고, 촬영 시각도 함께 돌려준다."""
    data = httpx.get(video_url, timeout=60.0).content
    frames: list[bytes] = []
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "input.mp4")
        with open(path, "wb") as f:
            f.write(data)

        duration = probe_duration(path)
        created_at = probe_creation_time(path)

        # 각 구간의 '중앙'을 찍어 앞뒤 검은 화면을 피한다. 길이를 모르면 맨 앞 1장만.
        timestamps = (
            [duration * (i + 0.5) / count for i in range(count)]
            if duration > 0 else [0.0]
        )
        for i, ts in enumerate(timestamps):
            out = os.path.join(tmp, f"frame_{i}.jpg")
            try:
                subprocess.run(
                    ["ffmpeg", "-ss", str(ts), "-i", path,
                     "-frames:v", "1", "-q:v", "3", "-y", out],
                    capture_output=True, check=True,
                )
                with open(out, "rb") as fr:
                    frames.append(fr.read())
            except subprocess.CalledProcessError:
                continue
    return frames, created_at
