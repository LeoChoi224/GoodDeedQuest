# ============================================================
# Good Deed Quest 단일 이미지
#
# backend와 ai가 서로를 파이썬 모듈로 import 하기 때문에
#   ai/app/quest_recommend/nodes/volunteer_agent.py:5,11 → backend
#   backend/app/quest_verification/challenge.py:7,8      → ai
# 이미지를 나눌 수 없다. 하나만 만들고 실행 명령만 다르게 준다.
# ============================================================
FROM python:3.12-slim

# ffmpeg: ai(숏폼 렌더링)와 backend(영상 480p 변환, 프레임 추출) 양쪽이 호출한다
#   - ai/app/short_form/agents/render_agent.py:142
#   - backend/app/common/s3_client.py:109
#   - backend/app/quest_verification/media.py:44
# fonts-nanum: ffmpeg drawtext 자막에 쓸 한글 폰트
#   설치 후 경로: /usr/share/fonts/truetype/nanum/NanumGothic.ttf
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성을 소스보다 먼저 복사한다.
# 이렇게 하면 소스만 고쳤을 때 pip install 레이어가 캐시에서 재사용된다.
# (반대로 하면 코드 한 줄 고칠 때마다 131개 패키지를 다시 깐다)
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt

# backend와 ai를 둘 다 넣는다. 하나만 넣으면 ModuleNotFoundError 로 부팅 실패.
COPY backend ./backend
COPY ai ./ai

# ai/app/common/config.py 의 FONT_PATH 기본값이 Windows 경로라 리눅스 경로로 덮어쓴다.
# 이게 없으면 숏폼 렌더링이 죽는다.
ENV FONT_PATH=/usr/share/fonts/truetype/nanum/NanumGothic.ttf

# /app 을 파이썬 최상위 경로로 인식시킨다 (backend.main / ai.main 임포트용)
ENV PYTHONPATH=/app

# 파이썬 출력 버퍼링을 끈다. 안 끄면 docker logs 에 로그가 늦게 나와 디버깅이 괴롭다.
ENV PYTHONUNBUFFERED=1

EXPOSE 8000 8001

# 기본 명령. docker-compose에서 서비스마다 덮어쓴다.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]