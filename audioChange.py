import os
from pydub import AudioSegment

# ==========================================
# 1. FFmpeg 실행 파일 경로 직접 지정 (필수 수정)
# ==========================================
# Windows 예시: r"C:\ffmpeg\bin\ffmpeg.exe" (앞에 r을 붙여야 백슬래시 오류가 나지 않습니다)
# macOS/Linux 예시: "/usr/local/bin/ffmpeg"

FFMPEG_PATH = r"C:\Users\82107\Downloads\ffmpeg-2026-02-15-git-33b215d155-essentials_build\ffmpeg-2026-02-15-git-33b215d155-essentials_build\bin\ffmpeg.exe"
FFPROBE_PATH = r"C:\Users\82107\Downloads\ffmpeg-2026-02-15-git-33b215d155-essentials_build\ffmpeg-2026-02-15-git-33b215d155-essentials_build\bin\ffprobe.exe"

# pydub에 경로 적용
AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH


def convert_audio(input_path, target_format):
    """
    오디오 파일을 m4a, mp3, aac, amr, wav 중 하나의 포맷으로 변환합니다.
    """
    # [안전 장치] 지정한 FFmpeg 경로에 실제 파일이 있는지 먼저 검사합니다.
    if not os.path.isfile(FFMPEG_PATH):
        print(f"❌ 설정 오류: 지정하신 경로에 FFmpeg 실행 파일이 없습니다.\n확인된 경로: {FFMPEG_PATH}")
        return

    supported_formats = ['m4a', 'mp3', 'aac', 'amr', 'wav']

    target_format = target_format.lower()
    if target_format.startswith('.'):
        target_format = target_format[1:]

    if target_format not in supported_formats:
        print(f"❌ 지원하지 않는 포맷입니다. ({', '.join(supported_formats)} 중 하나를 선택하세요)")
        return

    if not os.path.exists(input_path):
        print("❌ 입력 파일이 존재하지 않습니다. 경로를 확인해 주세요.")
        return

    filename, _ = os.path.splitext(input_path)
    output_path = f"{filename}.{target_format}"

    format_mapping = {
        'm4a': 'ipod',
        'mp3': 'mp3',
        'aac': 'adts',
        'amr': 'amr',
        'wav': 'wav'
    }

    export_format = format_mapping[target_format]

    try:
        print(f"⏳ '{input_path}' 파일을 읽어오는 중...")
        audio = AudioSegment.from_file(input_path)

        # AMR 포맷을 위한 특별 처리 (8000Hz, 모노)
        if target_format == 'amr':
            audio = audio.set_frame_rate(8000).set_channels(1)

        print(f"🔄 '{output_path}' 파일로 변환 중...")
        audio.export(output_path, format=export_format)
        print("✅ 변환이 완료되었습니다!")

    except Exception as e:
        print(f"❌ 변환 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    # ==========================================
    # 2. 파일 변환 실행 (이 부분을 수정해서 사용하세요)
    # ==========================================

    # 변환할 원본 파일의 경로
    source_file = r"C:\Users\82107\OneDrive\문서\11-2.mp4"

    # 원하는 변환 확장자 ('m4a', 'mp3', 'aac', 'amr', 'wav')
    desired_format = "mp3"

    convert_audio(source_file, desired_format)