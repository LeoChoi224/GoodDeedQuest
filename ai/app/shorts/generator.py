import subprocess
import os

class ShortsVideoGenerator:
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def summarize_activity_for_audio(self, user_name: str, quest_title: str) -> str:
        """LLM을 호출하여 숏폼 오디오 나레이션용 대본(Script)을 생성합니다."""
        script = f"안녕하세요! 오늘 {user_name}님이 완수한 선행 퀘스트는 바로 '{quest_title}'입니다. 깨끗해지는 거리를 보며 큰 보람을 느낀 하루였습니다. 우리 모두 작은 선행에 동참해봐요!"
        return script

    def generate_tts_audio(self, script_text: str, output_path: str) -> str:
        """TTS API를 사용하여 스크립트를 음성 파일(mp3/wav)로 합성합니다."""
        # gTTS나 기타 TTS 라이브러리 사용 뼈대
        print(f"Generating TTS Audio for text: {script_text[:20]}...")
        # Mock file creation
        with open(output_path, "wb") as f:
            f.write(b"MOCK AUDIO DATA")
        return output_path

    def render_shorts_video(self, image_path: str, audio_path: str, output_name: str) -> str:
        """FFmpeg을 활용하여 정적 이미지와 TTS 나레이션 음성, 배경음악을 융합하여 숏폼 비디오(MP4)를 렌더링합니다."""
        output_file_path = os.path.join(self.output_dir, output_name)
        
        # FFmpeg subprocess 실행 뼈대 예시 (실제 구동을 위해서는 로컬 환경에 ffmpeg 설치 필요)
        # command = [
        #     "ffmpeg", "-loop", "1", "-i", image_path, "-i", audio_path,
        #     "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac",
        #     "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", output_file_path
        # ]
        # print("Running FFmpeg build command...")
        # subprocess.run(command, check=True)
        
        print(f"Mocking video generation to path: {output_file_path}")
        with open(output_file_path, "wb") as f:
            f.write(b"MOCK VIDEO DATA")
            
        return output_file_path

generator = ShortsVideoGenerator()

def generate_shorts_boilerplate(quest_id: int, user_name: str) -> dict:
    quest_titles = {1: "플로깅(조깅하며 쓰레기 줍기)", 2: "유기동물 보호소 봉사"}
    title = quest_titles.get(quest_id, "선행 퀘스트")
    
    script = generator.summarize_activity_for_audio(user_name, title)
    # 임시 Mocking 경로
    audio_path = "./output/temp_narration.mp3"
    video_path = "./output/render_result.mp4"
    
    return {
        "status": "COMPLETED",
        "script": script,
        "audio_path": audio_path,
        "video_path": video_path
    }
