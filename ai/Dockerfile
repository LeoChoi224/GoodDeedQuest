FROM python:3.12-slim

WORKDIR /app

# ffmpeg: 숏폼 렌더링(FFmpeg Render Agent)에 사용
# fonts-nanum: drawtext 자막 오버레이용 한글 폰트
# (설치 후 컨테이너 내 폰트 경로: /usr/share/fonts/truetype/nanum/NanumGothic.ttf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

COPY ai/requirements.txt ./ai/requirements.txt
RUN pip install --no-cache-dir -r ai/requirements.txt

COPY ai ./ai

EXPOSE 8001

CMD ["uvicorn", "ai.main:app", "--host", "0.0.0.0", "--port", "8001"]
