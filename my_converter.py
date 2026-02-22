import os
from pdf2image import convert_from_path

# 1. 설정
pdf_path = r"C:\Users\82107\Downloads\강문호.pdf"
# 저장할 폴더 (파일명이 아닙니다)
save_dir = r"C:\Users\82107\Downloads"
# Poppler 경로
poppler_dir = r"C:\Program Files\poppler\poppler-25.12.0\Library\bin"

dpi_setting = 300

try:
    print("변환을 시작합니다...")
    # PDF를 이미지로 변환
    images = convert_from_path(
        pdf_path,
        dpi=dpi_setting,
        poppler_path=poppler_dir
    )

    for i, image in enumerate(images):
        # 파일명 깔끔하게 생성 (강문호_page_1.jpg 등)
        output_filename = os.path.join(save_dir, f"강문호_page_{i + 1}.jpg")

        image.save(output_filename, "JPEG")
        print(f"저장 완료: {output_filename}")

    print("모든 작업이 완료되었습니다.")

except Exception as e:
    print(f"오류가 발생했습니다: {e}")