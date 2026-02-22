

import os
import subprocess
import math


def get_video_duration(video_path):
    """ffprobe를 사용하여 동영상의 총 길이(초)를 가져옵니다."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def get_file_size_mb(file_path):
    """파일 크기를 MB 단위로 반환합니다."""
    return os.path.getsize(file_path) / (1024 * 1024)


def split_video(input_file, num_parts=3, output_prefix="part", max_size_mb=400):
    """
    동영상을 지정된 개수로 분할합니다.

    Args:
        input_file: 입력 동영상 파일 경로
        num_parts: 분할할 개수 (2 또는 3)
        output_prefix: 출력 파일 접두사 (기본값: "part")
        max_size_mb: 각 파일의 최대 크기(MB) (기본값: 400)
    """

    # 입력 파일 확인
    if not os.path.exists(input_file):
        print(f"오류: '{input_file}' 파일을 찾을 수 없습니다.")
        return

    print(f"동영상 분석 중: {input_file}")

    # 동영상 총 길이 가져오기
    try:
        total_duration = get_video_duration(input_file)
        print(f"총 길이: {total_duration:.2f}초 ({total_duration / 60:.2f}분)")
    except Exception as e:
        print(f"동영상 정보를 가져오는 중 오류 발생: {e}")
        return

    # 분할 길이 계산
    segment_duration = total_duration / num_parts

    # 출력 파일명 생성
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.dirname(input_file) or '.'

    print(f"\n동영상을 {num_parts}개로 분할합니다 (각 {segment_duration:.2f}초)...")

    # 지정된 개수만큼 분할
    for i in range(num_parts):
        start_time = i * segment_duration
        output_file = os.path.join(output_dir, f"{base_name}-{i + 1}.mp4")

        print(f"\n[{i + 1}/{num_parts}] 파트 생성 중...")
        print(f"  시작 시간: {start_time:.2f}초")
        print(f"  길이: {segment_duration:.2f}초")

        # ffmpeg 명령어 (빠른 복사 모드 - 재인코딩 없음)
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-ss', str(start_time),
            '-t', str(segment_duration),
            '-c', 'copy',  # 재인코딩 없이 복사 (빠름)
            '-avoid_negative_ts', '1',
            '-y',  # 덮어쓰기
            output_file
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            file_size = get_file_size_mb(output_file)
            print(f"  ✓ 생성 완료: {output_file}")
            print(f"  파일 크기: {file_size:.2f}MB")

            # 500MB 초과 확인
            if file_size > max_size_mb:
                print(f"  ⚠ 경고: 파일이 {max_size_mb}MB를 초과했습니다!")
                print(f"  재인코딩을 시도합니다...")

                # 재인코딩 (품질 낮춤)
                temp_file = output_file.replace('.mp4', '_temp.mp4')
                os.rename(output_file, temp_file)

                # 비트레이트 계산 (500MB 목표)
                target_bitrate = int((max_size_mb * 8 * 1024) / segment_duration * 0.9)  # 90%로 여유

                cmd_reencode = [
                    'ffmpeg',
                    '-i', temp_file,
                    '-b:v', f'{target_bitrate}k',
                    '-maxrate', f'{target_bitrate}k',
                    '-bufsize', f'{target_bitrate * 2}k',
                    '-y',
                    output_file
                ]

                subprocess.run(cmd_reencode, check=True, capture_output=True)
                os.remove(temp_file)

                new_size = get_file_size_mb(output_file)
                print(f"  ✓ 재인코딩 완료: {new_size:.2f}MB")

        except subprocess.CalledProcessError as e:
            print(f"  ✗ 오류 발생: {e}")
            continue

    print("\n" + "=" * 50)
    print("분할 완료!")
    print("=" * 50)


def main():
    """메인 함수"""
    print("=" * 50)
    print("동영상 분할 프로그램")
    print("(각 파일 최대 400MB)")
    print("=" * 50 + "\n")

    # 분할 개수 선택
    while True:
        choice = input("분할 개수를 선택하세요 (2 또는 3): ").strip()
        if choice in ['2', '3']:
            num_parts = int(choice)
            break
        else:
            print("⚠ 2 또는 3을 입력해주세요.\n")

    # 사용자 입력
    input_file = input("\n분할할 동영상 파일 경로를 입력하세요: ").strip()

    # 따옴표 제거 (드래그 앤 드롭 시)
    input_file = input_file.strip('"').strip("'")

    # 출력 접두사 입력 (선택사항)
    output_prefix = input("출력 파일 접두사 (기본값: part): ").strip() or "part"

    # 분할 실행
    split_video(input_file, num_parts=num_parts, output_prefix=output_prefix, max_size_mb=400)


if __name__ == "__main__":
    main()