import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import math


# 사각형 클래스
class InteractiveRectangle:
    def __init__(self, x, y, width, height):
        self.x = x  # 좌상단 x
        self.y = y  # 좌상단 y
        self.width = width
        self.height = height
        self.control_radius = 30  # 컨트롤 포인트 감지 반경

    def get_corners(self):
        """사각형의 네 모서리 좌표 반환"""
        return {
            'top_left': (self.x, self.y),
            'top_right': (self.x + self.width, self.y),
            'bottom_left': (self.x, self.y + self.height),
            'bottom_right': (self.x + self.width, self.y + self.height)
        }

    def is_near_control_point(self, px, py, corner_name):
        """특정 컨트롤 포인트 근처에 있는지 확인"""
        corners = self.get_corners()
        cx, cy = corners[corner_name]
        distance = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        return distance < self.control_radius

    def resize_from_bottom_left(self, px, py):
        """좌하단에서 크기 조절"""
        # 새로운 좌하단 위치
        new_x = px
        new_bottom = py

        # 우상단은 고정
        right = self.x + self.width
        top = self.y

        # 새로운 크기 계산
        self.width = right - new_x
        self.height = new_bottom - top
        self.x = new_x

        # 최소 크기 유지
        if self.width < 50:
            self.width = 50
            self.x = right - 50
        if self.height < 50:
            self.height = 50

    def resize_from_top_right(self, px, py):
        """우상단에서 크기 조절"""
        # 새로운 우상단 위치
        new_right = px
        new_top = py

        # 좌하단은 고정
        left = self.x
        bottom = self.y + self.height

        # 새로운 크기 계산
        self.width = new_right - left
        self.height = bottom - new_top
        self.y = new_top

        # 최소 크기 유지
        if self.width < 50:
            self.width = 50
        if self.height < 50:
            self.height = 50
            self.y = bottom - 50

    def move_rectangle(self, px, py):
        """우하단을 기준으로 사각형 이동"""
        # 우하단이 (px, py)가 되도록 이동
        self.x = px - self.width
        self.y = py - self.height

    def draw(self, image):
        """사각형과 컨트롤 포인트 그리기"""
        corners = self.get_corners()

        # 사각형 그리기
        cv2.rectangle(image,
                      (int(self.x), int(self.y)),
                      (int(self.x + self.width), int(self.y + self.height)),
                      (0, 255, 0), 3)

        # 컨트롤 포인트 그리기
        # 좌하단 (파란색 - 크기조절)
        cv2.circle(image, (int(corners['bottom_left'][0]), int(corners['bottom_left'][1])),
                   15, (255, 0, 0), -1)
        cv2.putText(image, "Size", (int(corners['bottom_left'][0]) - 20, int(corners['bottom_left'][1]) + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # 우상단 (빨간색 - 크기조절)
        cv2.circle(image, (int(corners['top_right'][0]), int(corners['top_right'][1])),
                   15, (0, 0, 255), -1)
        cv2.putText(image, "Size", (int(corners['top_right'][0]) - 20, int(corners['top_right'][1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # 우하단 (노란색 - 이동)
        cv2.circle(image, (int(corners['bottom_right'][0]), int(corners['bottom_right'][1])),
                   15, (0, 255, 255), -1)
        cv2.putText(image, "Move", (int(corners['bottom_right'][0]) - 25, int(corners['bottom_right'][1]) + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)


def calculate_distance(point1, point2):
    """두 점 사이의 거리 계산"""
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def is_pinching(hand_landmarks, image_width, image_height):
    """엄지와 검지가 가까운지 확인 (핀치 제스처)"""
    # 엄지 끝 (landmark 4)
    thumb_tip = hand_landmarks[4]
    # 검지 끝 (landmark 8)
    index_tip = hand_landmarks[8]

    # 픽셀 좌표로 변환
    thumb_pos = (thumb_tip.x * image_width, thumb_tip.y * image_height)
    index_pos = (index_tip.x * image_width, index_tip.y * image_height)

    distance = calculate_distance(thumb_pos, index_pos)

    # 거리가 40 픽셀 이하면 핀치로 간주
    return distance < 40, index_pos


# 손 랜드마크 연결선 정의
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),  # 엄지
    (0, 5), (5, 6), (6, 7), (7, 8),  # 검지
    (0, 9), (9, 10), (10, 11), (11, 12),  # 중지
    (0, 13), (13, 14), (14, 15), (15, 16),  # 약지
    (0, 17), (17, 18), (18, 19), (19, 20),  # 새끼
    (5, 9), (9, 13), (13, 17)  # 손바닥
]


# 1. 랜드마크 그리기 함수
def draw_landmarks_on_image(rgb_image, detection_result):
    hand_landmarks_list = detection_result.hand_landmarks
    annotated_image = np.copy(rgb_image)

    image_height, image_width = annotated_image.shape[:2]

    # 각 손에 대해 랜드마크 그리기
    for hand_landmarks in hand_landmarks_list:
        # 연결선 그리기
        for connection in HAND_CONNECTIONS:
            start_idx, end_idx = connection
            start_landmark = hand_landmarks[start_idx]
            end_landmark = hand_landmarks[end_idx]

            start_point = (int(start_landmark.x * image_width),
                           int(start_landmark.y * image_height))
            end_point = (int(end_landmark.x * image_width),
                         int(end_landmark.y * image_height))

            cv2.line(annotated_image, start_point, end_point, (0, 255, 0), 2)

        # 랜드마크 점 그리기
        for landmark in hand_landmarks:
            point = (int(landmark.x * image_width),
                     int(landmark.y * image_height))
            cv2.circle(annotated_image, point, 5, (0, 0, 255), -1)

    return annotated_image


# 2. 웹캠 캡처 초기화
cap = cv2.VideoCapture(0)

# 화면 크기 가져오기
ret, frame = cap.read()
if ret:
    image_height, image_width = frame.shape[:2]
else:
    image_width, image_height = 640, 480

# 사각형 초기화 (화면 중앙에 200x200 크기)
rect = InteractiveRectangle(
    x=image_width // 2 - 100,
    y=image_height // 2 - 100,
    width=200,
    height=200
)

# 인터랙션 상태
interaction_mode = None  # 'resize_bl', 'resize_tr', 'move', None

# 3. 손 인식 옵션 설정
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
    running_mode=vision.RunningMode.VIDEO)

# 4. 손 인식 객체 생성
with vision.HandLandmarker.create_from_options(options) as landmarker:
    frame_timestamp_ms = 0

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        # [수정됨] 이미지를 좌우 반전 (1: 좌우 반전, 0: 상하 반전)
        image = cv2.flip(image, 1)

        image_height, image_width = image.shape[:2]

        # 5. BGR을 RGB로 변환
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # MediaPipe Image 객체 생성
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # 6. 손 인식 수행
        detection_result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)
        frame_timestamp_ms += 33  # ~30 FPS

        # 7. 결과 그리기
        annotated_image = draw_landmarks_on_image(rgb_image, detection_result)

        # 8. 손 제스처로 사각형 조작
        if detection_result.hand_landmarks:
            # 첫 번째 손만 사용
            hand_landmarks = detection_result.hand_landmarks[0]

            # 핀치 제스처 확인
            pinching, finger_pos = is_pinching(hand_landmarks, image_width, image_height)

            if pinching:
                fx, fy = finger_pos

                # 컨트롤 포인트 근처에 있는지 확인하고 모드 설정
                if rect.is_near_control_point(fx, fy, 'bottom_left'):
                    interaction_mode = 'resize_bl'
                    rect.resize_from_bottom_left(fx, fy)
                    cv2.putText(annotated_image, "Resizing (Bottom-Left)", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                elif rect.is_near_control_point(fx, fy, 'top_right'):
                    interaction_mode = 'resize_tr'
                    rect.resize_from_top_right(fx, fy)
                    cv2.putText(annotated_image, "Resizing (Top-Right)", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                elif rect.is_near_control_point(fx, fy, 'bottom_right'):
                    interaction_mode = 'move'
                    rect.move_rectangle(fx, fy)
                    cv2.putText(annotated_image, "Moving", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                # 핀치 위치에 원 표시
                cv2.circle(annotated_image, (int(fx), int(fy)), 10, (255, 255, 0), -1)
            else:
                interaction_mode = None

        # 9. 사각형 그리기
        rect.draw(annotated_image)

        # RGB를 다시 BGR로 변환하여 출력
        bgr_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

        # 10. 화면 출력
        cv2.imshow('Hand Tracking - Interactive Rectangle', bgr_image)

        # ESC 키를 누르면 종료
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()