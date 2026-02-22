from rembg import remove
from PIL import Image
import os
import time

def remove_background(input_path):
    # 1. 파일 경로 확인
    if not os.path.exists(input_path):
        print(f"\n[오류] 파일을 찾을 수 없습니다: {input_path}")
        return

    # 2. 결과 파일 경로 생성 (예: image.jpg -> image_no_bg.png)
    # 배경이 투명해지려면 반드시 png 형식이어야 합니다.
    file_root, _ = os.path.splitext(input_path)
    output_path = f"{file_root}_no_bg.png"

    print("\n작업을 시작합니다... (첫 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다)")
    start_time = time.time()

    try:
        # 3. 이미지 열기
        input_image = Image.open(input_path)

        # 4. 배경 제거 수행
        output_image = remove(input_image)

        # 5. 이미지 저장
        output_image.save(output_path)

        end_time = time.time()
        print(f"\n[완료] 배경이 제거된 이미지가 저장되었습니다.")
        print(f"저장 위치: {output_path}")
        print(f"소요 시간: {end_time - start_time:.2f}초")

    except Exception as e:
        print(f"\n[오류] 작업 중 문제가 발생했습니다: {e}")

if __name__ == "__main__":
    print("--- 이미지 배경 제거 프로그램 ---")
    # 사용자로부터 경로 입력 받기 (따옴표 제거 처리)
    user_input = input("이미지 파일 경로를 입력하세요: ").strip().replace('"', '').replace("'", "")

    remove_background(user_input)

#"C:\Users\82107\OneDrive\사진\스크린샷\사인.png"