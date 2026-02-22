import cv2
import mediapipe as mp

# 1. MediaPipe 유틸리티 설정
mp_drawing = mp.solutions.drawing_utils # 랜드마크를 그리기 위한 도구
mp_hands = mp.solutions.hands # 손 인식 모델

# 2. 웹캠 캡처 초기화
cap = cv2.VideoCapture(0)

# 3. 손 인식 모델 로드 (설정 옵션 지정)
# min_detection_confidence: 감지 신뢰도 (이 값 이상일 때만 손으로 인정)
# min_tracking_confidence: 추적 신뢰도
with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as hands:

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        # 4. 성능 향상을 위해 이미지 쓰기 불가로 설정 후 색상 변환
        # OpenCV는 BGR을 쓰지만, MediaPipe는 RGB를 사용합니다.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 5. MediaPipe로 이미지 분석 (핵심 단계)
        results = hands.process(image)

        # 6. 결과를 그리기 위해 다시 이미지 쓰기 가능 및 BGR 변환
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # 7. 손이 검출되었다면 랜드마크 그리기
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 손가락 마디마디에 선과 점을 그립니다
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS)

        # 8. 화면 출력
        cv2.imshow('MediaPipe Hands', image)

        # ESC 키를 누르면 종료
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()