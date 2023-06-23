import cv2
import mediapipe as mp
import threading
from pythonosc import osc_message_builder
from pythonosc import udp_client
import tkinter as tk
import ctypes
import subprocess
import time

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

sender = udp_client.SimpleUDPClient('127.0.0.1', 4560)
c = 0



def set_volume(volume):
    volume = max(0, min(100, volume))
    subprocess.run(["amixer", "set", "Master", f"{volume}%"])
    
def on_slider_ch(volume):
    set_volume(int(volume))

def toggle_text():
    if button["text"] == "LOOP\nON":
        button["text"] = "LOOP\nOFF"
    else:
        button["text"] = "LOOP\nON"

def sound(data, runtime):
    global c
    if c - 2 < data < c + 2:
        sender.send_message('/trigger/prophet', [False, data])
        time.sleep(0.3)
        return
    temp = data
    c = temp
    print("data :", data)
    
    if data < 30:
        sender.send_message('/trigger/prophet', [True, 0])
    else:
        sender.send_message('/trigger/prophet', [False, data])
        time.sleep(0.1)

def long(a, b, c, d):
    lwrw = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
    lwla = ((a.x - c.x) ** 2 + (a.y - c.y) ** 2) ** 0.5
    lara = ((d.x - c.x) ** 2 + (d.y - c.y) ** 2) ** 0.5
    rwra = ((b.x - d.x) ** 2 + (b.y - d.y) ** 2) ** 0.5

    solong = int((lwrw + lwla + lara + rwra) * 50)
    
    return solong

def timemer(la, ra):
    lara = ((la.x - ra.x) ** 2 + (la.y - ra.y) ** 2) ** 0.5
    time1 = float("{:.1f}".format(lara * 10))
    return time1

def process_frames():
    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as pose:
        
        while True:
            if cap.isOpened():
                ret, image = cap.read()
                if not ret:
                    break
                    
                image = cv2.resize(image, (640, 480))
                image.flags.writeable = False
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = pose.process(image_rgb)

                if results.pose_landmarks:
                    left_wrist_landmark = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
                    right_wrist_landmark = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
                    left_ankle_landmark = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE]
                    right_ankle_landmark = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]

                    #mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                    
                    data = long(left_wrist_landmark, right_wrist_landmark, left_ankle_landmark, right_ankle_landmark)
                    runtime = timemer(left_ankle_landmark, right_ankle_landmark)
                    sound(data, runtime)
                    
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                cv2.imshow('MediaPipe Pose Detection', cv2.flip(image, 1))

                if cv2.waitKey(1) == ord('q'):
                    break

# Initialize video capture object
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 10)

# Create the tkinter window
win = tk.Tk()
win.geometry('800x480')
win.title('사용자 UI')

# 라디오 버튼 그룹 변수 생성
radio_var = tk.StringVar(value='Option 1')

# 텍스트 추가
text = tk.Label(win, text='사운드 크기', font=('Malgun Gothic', 20))

# Add the loop button
button = tk.Button(win, text='LOOP\nON', font=('Arial', 16), command=toggle_text)
button.config(width=15, height=3)
button.pack()

# 라디오 버튼 생성 및 글자 크기 설정
radio1 = tk.Radiobutton(win, text='Music 1', variable=radio_var, value='Option 1', font = ('Arial', 16))
radio2 = tk.Radiobutton(win, text='Music 2', variable=radio_var, value='Option 2', font = ('Arial', 16))
radio3 = tk.Radiobutton(win, text='Music 3', variable=radio_var, value='Option 3', font = ('Arial', 16))

# Add the volume slider
volume_slider = tk.Scale(win, from_=0, to=100, orient=tk.VERTICAL, command=on_slider_ch, font=('Arial', 8), width=50, length=300)
volume_slider.set(50)
volume_slider.pack(padx=10, pady=10)

# 위젯 배치
radio1.place(x = 150, y = 180)
radio2.place(x = 150, y = 250)
radio3.place(x = 150, y = 320)
volume_slider.place(x = 650, y = 40)
button.place(x = 120, y = 60)
text.place(x = 450, y = 220)

# Start a new thread to process frames
frame_thread = threading.Thread(target=process_frames)
frame_thread.start()

# Start the tkinter event loop
win.mainloop()

# Wait for the frame processing thread to finish
frame_thread.join()

# Release video capture object and destroy all windows
cap.release()
cv2.destroyAllWindows()

