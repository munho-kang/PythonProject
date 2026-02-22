import cv2
import mediapipe as mp
import numpy as np
import math

# 1. MediaPipe 초기화
mp_hands = mp.solutions.hands


# 2. 물리 엔진 클래스 (줄에 매달린 물체 시뮬레이션)
class StringPhysics:
    def __init__(self, start_pos, label="part"):
        self.pos = np.array(start_pos, dtype=np.float32)  # 현재 물체 위치
        self.velocity = np.array([0, 0], dtype=np.float32)  # 속도
        self.label = label

    def update(self, target_pos, string_length, stiffness=0.1, gravity=0.5):
        """
        target_pos: 손가락 끝 좌표 (줄의 시작점)
        string_length: 줄의 길이
        stiffness: 줄의 탄성 (낮을수록 느슨하고 무거운 느낌)
        gravity: 중력 가속도
        """
        # 목표 위치 설정 (손가락 바로 아래 string_length 만큼 떨어진 곳)
        desired_pos = np.array([target_pos[0], target_pos[1] + string_length], dtype=np.float32)

        # 1. 관성 이동 (현재 위치에서 목표 위치로 부드럽게 이동)
        # 거리에 비례하여 속도 증가 (스프링 효과)
        force = (desired_pos - self.pos) * stiffness

        # 2. 물리 적용
        self.velocity += force
        self.velocity[1] += gravity  # 중력 추가
        self.velocity *= 0.8  # 공기 저항 (감속) -> 없으면 영원히 흔들림

        # 위치 업데이트
        self.pos += self.velocity

        return (int(self.pos[0]), int(self.pos[1]))


# 물리 객체 생성 (머리, 왼손, 오른손)
# 초기값은 화면 중앙 쯤으로 설정
physics_head = StringPhysics([320, 200], "head")
physics_l_hand = StringPhysics([200, 300], "l_hand")
physics_r_hand = StringPhysics([440, 300], "r_hand")

# 다리 흔들림 변수
sway_angle = 0
prev_head_x = 0

cap = cv2.VideoCapture(0)

with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        # 전처리
        image = cv2.flip(image, 1)
        h, w, c = image.shape
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        results = hands.process(image_rgb)

        # [배경] 검은색 캔버스 (홀로그램 모드)
        canvas = np.zeros((h, w, c), dtype=np.uint8)

        # (선택사항) 내 실제 손 위치를 흐릿하게 보고 싶으면 아래 주석 해제
        # canvas = cv2.addWeighted(canvas, 1.0, image, 0.3, 0)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                def get_coord(idx):
                    lm = hand_landmarks.landmark[idx]
                    return np.array([lm.x * w, lm.y * h], dtype=np.float32)


                # --- 1. 컨트롤러(손가락) 좌표 획득 ---
                finger_l = get_coord(8)  # 검지
                finger_head = get_coord(12)  # 중지
                finger_r = get_coord(16)  # 약지

                # --- 2. 물리 엔진 업데이트 (줄에 매달린 효과) ---
                # 줄 길이 설정 (픽셀 단위)
                str_len_head = 80
                str_len_hand = 100

                # 업데이트 실행 (좌표 반환)
                # stiffness 값을 조절하여 무게감을 다르게 줌 (머리는 무겁게 0.05, 손은 가볍게 0.1)
                puppet_head = physics_head.update(finger_head, str_len_head, stiffness=0.08)
                puppet_l_hand = physics_l_hand.update(finger_l, str_len_hand, stiffness=0.15)
                puppet_r_hand = physics_r_hand.update(finger_r, str_len_hand, stiffness=0.15)

                # --- 3. 몸통 및 다리 계산 (머리 따라가기) ---
                # 몸통은 머리 바로 아래 고정 + 약간의 흔들림
                torso_top = (puppet_head[0], puppet_head[1] + 20)
                torso_bottom = (puppet_head[0], puppet_head[1] + 120)

                # 다리 스윙 계산 (이전 코드의 로직 유지)
                velocity_x = puppet_head[0] - prev_head_x
                sway_angle -= velocity_x * 0.03
                sway_angle *= 0.90  # 감속
                prev_head_x = puppet_head[0]

                leg_len = 70
                leg_l = (int(torso_bottom[0] + math.sin(sway_angle - 0.3) * leg_len),
                         int(torso_bottom[1] + math.cos(sway_angle - 0.3) * leg_len))
                leg_r = (int(torso_bottom[0] + math.sin(sway_angle + 0.3) * leg_len),
                         int(torso_bottom[1] + math.cos(sway_angle + 0.3) * leg_len))

                # --- 4. 그리기 (Drawing) ---

                # 색상 팔레트
                c_string = (150, 150, 150)  # 줄 색 (회색)
                c_controller = (0, 255, 255)  # 내 손가락 위치 (노랑)
                c_puppet = (255, 100, 100)  # 인형 관절

                # [Step 1] 줄 그리기 (손가락 -> 인형 파츠)
                # 실제 실처럼 얇게 그림
                cv2.line(canvas, (int(finger_l[0]), int(finger_l[1])), puppet_l_hand, c_string, 1)
                cv2.line(canvas, (int(finger_head[0]), int(finger_head[1])), puppet_head, c_string, 1)
                cv2.line(canvas, (int(finger_r[0]), int(finger_r[1])), puppet_r_hand, c_string, 1)

                # [Step 2] 컨트롤러 위치 표시 (내 손가락 끝)
                cv2.circle(canvas, (int(finger_l[0]), int(finger_l[1])), 5, c_controller, -1)
                cv2.circle(canvas, (int(finger_head[0]), int(finger_head[1])), 5, c_controller, -1)
                cv2.circle(canvas, (int(finger_r[0]), int(finger_r[1])), 5, c_controller, -1)

                # [Step 3] 인형 그리기
                # 어깨
                sh_l = (torso_top[0] - 20, torso_top[1] + 10)
                sh_r = (torso_top[0] + 20, torso_top[1] + 10)

                # 팔 (어깨 -> 손)
                cv2.line(canvas, sh_l, puppet_l_hand, c_puppet, 4)
                cv2.line(canvas, sh_r, puppet_r_hand, c_puppet, 4)

                # 몸통 & 다리
                cv2.line(canvas, torso_top, torso_bottom, (0, 200, 0), 6)  # 척추
                cv2.line(canvas, torso_bottom, leg_l, (0, 200, 0), 4)  # 왼다리
                cv2.line(canvas, torso_bottom, leg_r, (0, 200, 0), 4)  # 오른다리

                # 머리 & 손 관절볼
                cv2.circle(canvas, puppet_head, 25, (50, 50, 255), -1)  # 머리
                cv2.circle(canvas, puppet_l_hand, 10, c_puppet, -1)
                cv2.circle(canvas, puppet_r_hand, 10, c_puppet, -1)

                # 시각적 장치: 십자 막대 (손가락 사이를 잇는 가상의 컨트롤러 막대)
                cv2.line(canvas, (int(finger_l[0]), int(finger_l[1])), (int(finger_head[0]), int(finger_head[1])),
                         c_controller, 1)
                cv2.line(canvas, (int(finger_head[0]), int(finger_head[1])), (int(finger_r[0]), int(finger_r[1])),
                         c_controller, 1)

        cv2.imshow('Real Marionette', canvas)

        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()