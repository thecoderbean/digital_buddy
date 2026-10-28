import cv2
import numpy as np
import math
import time
import random
import requests
import pyttsx3
import threading
import json
import re
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from flask import Flask, render_template, Response, jsonify, request

app = Flask(__name__)

# Initialize Local Text-to-Speech Engine globally with a threading lock
tts_lock = threading.Lock()
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 165)  # Speed of speech
tts_engine.setProperty('volume', 2.0)

# Select a sci-fi robotic or cleaner voice if available
voices = tts_engine.getProperty('voices')
for voice in voices:
    if "Zira" in voice.name or "David" in voice.name or "English" in voice.name:
        tts_engine.setProperty('voice', voice.id)
        break

def speak_safely(text):
    """Runs TTS in a separate thread safely protected by a threading lock."""
    def run_tts():
        with tts_lock:
            try:
                # Re-initializing a local engine instance inside the thread avoids main-thread loop collisions on Windows
                engine = pyttsx3.init()
                engine.setProperty('rate', 165)
                engine.setProperty('volume', 2.0)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Runtime Notice: {e}")
    
    threading.Thread(target=run_tts, daemon=True).start()

# Initialize MediaPipe Tasks with Ultra-High Precision Thresholds
face_base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
face_options = vision.FaceLandmarkerOptions(
    base_options=face_base_options,
    num_faces=1,
    min_face_detection_confidence=0.75,
    min_face_presence_confidence=0.75,
    min_tracking_confidence=0.75
)
face_detector = vision.FaceLandmarker.create_from_options(face_options)

hand_base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
hand_options = vision.HandLandmarkerOptions(
    base_options=hand_base_options,
    num_hands=2,
    min_hand_detection_confidence=0.75,
    min_hand_presence_confidence=0.75,
    min_tracking_confidence=0.75
)
hand_detector = vision.HandLandmarker.create_from_options(hand_options)

# ==========================================
# 100-STATE AUTONOMOUS CURIOUS KID ROBOT ENGINE
# ==========================================
class CuriousKidRobotEngine:
    def __init__(self):
        self.mood = {
            "joy": 0.5,
            "irritation": 0.0,
            "energy": 0.9,
            "surprise": 0.0,
            "affection": 0.2,
            "curiosity": 0.5,
            "excitement": 0.5
        }
        self.current_expression = "neutral"
        self.active_gesture = "none"
        self.last_user_seen_time = time.time()
        self.user_present = False
        
        self.autonomous_states = [
            "curious", "sleepy", "sad", "shocked", "surprised", "wink", "happy", "giggle", "angry", "love",
            "glitch_jitter", "scan_radar", "deep_boredom", "yawn_idle", "hyper_curious", "confused_tilt", "robot_dance",
            "thoughtful_nod", "pouty_lip", "sneaky_peek", "optic_blink_fast", "system_reboot", "power_saving", "eco_mode"
        ]
        self.current_random_state_index = 0
        self.state_timer = time.time()

        self.smoothed_hand_x = 0.5
        self.smoothed_hand_y = 0.5
        self.hand_velocity_x = 0.0
        self.hand_velocity_y = 0.0
        self.alpha = 0.3

    def update_behavior(self, raw_emotion, raw_gesture, user_detected):
        current_time = time.time()
        self.user_present = user_detected
        self.active_gesture = raw_gesture

        if user_detected:
            self.last_user_seen_time = current_time
            self.mood["excitement"] = min(1.0, self.mood["excitement"] + 0.04)
            self.mood["energy"] = min(1.0, self.mood["energy"] + 0.02)
            
            if raw_gesture == "pinch":
                return "giggle"
            elif raw_gesture == "fist":
                return "angry"
            elif raw_gesture == "victory":
                return "happy"
            elif raw_gesture == "pointing":
                return "curious"
            elif raw_gesture == "open_palm":
                return "surprised"

            if raw_emotion != "neutral":
                return raw_emotion
            return "happy" if self.mood["excitement"] > 0.7 else "neutral"
        else:
            self.mood["excitement"] = max(0.0, self.mood["excitement"] - 0.03)
            if current_time - self.state_timer > 3.5:
                self.state_timer = current_time
                self.current_random_state_index = random.randint(0, len(self.autonomous_states) - 1)
            
            rand_state = self.autonomous_states[self.current_random_state_index]
            if "sleep" in rand_state or "power" in rand_state:
                return "sleepy"
            elif "sad" in rand_state:
                return "sad"
            elif "shock" in rand_state:
                return "shocked"
            elif "wink" in rand_state:
                return "wink"
            elif "curious" in rand_state:
                return "curious"
            elif "angry" in rand_state:
                return "angry"
            elif "love" in rand_state:
                return "love"
            else:
                return "curious"

engine = CuriousKidRobotEngine()

def calculate_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (getattr(p1, 'z', 0) - getattr(p2, 'z', 0))**2)

def calculate_ear(eye_landmarks):
    v1 = calculate_distance(eye_landmarks[1], eye_landmarks[5])
    v2 = calculate_distance(eye_landmarks[2], eye_landmarks[4])
    h = calculate_distance(eye_landmarks[0], eye_landmarks[3])
    return (v1 + v2) / (2.0 * (h + 1e-6))

def classify_simple_gesture(landmarks):
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    index_extended = index_tip.y < landmarks[6].y
    middle_extended = middle_tip.y < landmarks[10].y
    ring_extended = ring_tip.y < landmarks[14].y
    pinky_extended = pinky_tip.y < landmarks[18].y

    if calculate_distance(thumb_tip, index_tip) < 0.045:
        return "pinch"
    elif index_extended and middle_extended and ring_extended and pinky_extended:
        return "open_palm"
    elif not index_extended and not middle_extended and not ring_extended and not pinky_extended:
        return "fist"
    elif index_extended and middle_extended and not ring_extended and not pinky_extended:
        return "victory"
    elif index_extended and not middle_extended and not ring_extended and not pinky_extended:
        return "pointing"
    return "active"

def draw_facial_landmarks_hud(frame, landmarks, w, h):
    key_indices = [33, 133, 160, 144, 362, 263, 385, 380, 70, 300, 1, 2, 4, 6, 61, 291, 13, 14]
    for idx in key_indices:
        if idx < len(landmarks):
            pt = landmarks[idx]
            px, py = int(pt.x * w), int(pt.y * h)
            cv2.circle(frame, (px, py), 3, (0, 255, 136), -1)

def draw_hologram_hand(frame, hand_landmarks, w, h):
    connections = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
                   (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
                   (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]
    points = []
    for lm in hand_landmarks:
        px, py = int(lm.x * w), int(lm.y * h)
        points.append((px, py))
        cv2.circle(frame, (px, py), 4, (0, 255, 128), -1)
    for conn in connections:
        cv2.line(frame, points[conn[0]], points[conn[1]], (102, 252, 241), 2, cv2.LINE_AA)

def generate_frames():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        return

    while True:
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        raw_emotion = "neutral"
        raw_gesture = "none"
        user_detected = False

        face_result = face_detector.detect(mp_image)
        if face_result.face_landmarks:
            user_detected = True
            lm = face_result.face_landmarks[0]
            draw_facial_landmarks_hud(frame, lm, w, h)

            inter_ocular_dist = calculate_distance(lm[33], lm[263]) + 1e-6
            left_ear = calculate_ear([lm[33], lm[160], lm[158], lm[133], lm[153], lm[144]])
            right_ear = calculate_ear([lm[362], lm[385], lm[387], lm[263], lm[373], lm[380]])
            avg_ear = (left_ear + right_ear) / 2.0

            mouth_height = calculate_distance(lm[13], lm[14]) / inter_ocular_dist
            mouth_width = calculate_distance(lm[61], lm[291]) / inter_ocular_dist
            lip_center_y = (lm[13].y + lm[14].y) / 2.0
            corners_y = (lm[61].y + lm[291].y) / 2.0
            smile_curvature = (lip_center_y - corners_y) / inter_ocular_dist

            if avg_ear < 0.12:
                raw_emotion = "sleepy"
            elif mouth_height > 0.45:
                raw_emotion = "surprised"
            elif smile_curvature > 0.035 and mouth_width > 0.45:
                raw_emotion = "happy"
            else:
                raw_emotion = "neutral"

        hand_result = hand_detector.detect(mp_image)
        if hand_result.hand_landmarks:
            for hand_lms in hand_result.hand_landmarks:
                draw_hologram_hand(frame, hand_lms, w, h)
            wrist = hand_result.hand_landmarks[0][0]
            engine.smoothed_hand_x = engine.alpha * wrist.x + (1 - engine.alpha) * engine.smoothed_hand_x
            engine.smoothed_hand_y = engine.alpha * wrist.y + (1 - engine.alpha) * engine.smoothed_hand_y
            raw_gesture = classify_simple_gesture(hand_result.hand_landmarks[0])
        else:
            raw_gesture = "none"

        engine.current_expression = engine.update_behavior(raw_emotion, raw_gesture, user_detected)

        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    camera.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify({
        'emotion': engine.current_expression,
        'gesture': engine.active_gesture,
        'mood': engine.mood,
        'hand': {
            "detected": engine.smoothed_hand_x != 0.5,
            "norm_x": engine.smoothed_hand_x + (engine.hand_velocity_x * 0.4),
            "norm_y": engine.smoothed_hand_y + (engine.hand_velocity_y * 0.4),
            "gesture": engine.active_gesture
        }
    })

@app.route('/chat', methods=['POST'])
def chat_with_llm():
    data = request.get_json()
    user_message = data.get('message', '')

    system_prompt = (
        "You are an expressive sci-fi robot companion. "
        "You must respond ONLY in valid JSON format with two keys: "
        "'reply' (your 1-2 sentence spoken response) and "
        "'emotion' (must be strictly one of: happy, sad, angry, surprised, curious, shocked, sleepy, love, wink, giggle, neutral). "
        "CRITICAL RULE: Never include the word 'imagi' or any variation of it in your reply. "
        "Do not include markdown code blocks or backticks in your output, just raw JSON."
    )

    try:
        ollama_response = requests.post('http://localhost:11434/api/generate', json={
            "model": "gemma2:2b",
            "prompt": f"{system_prompt}\n\nUser: {user_message}\nJSON Response:",
            "stream": False
        }, timeout=8)
        
        raw_output = ollama_response.json().get('response', '')
        clean_output = re.sub(r'```(?:json)?', '', raw_output).strip()
        
        parsed_data = json.loads(clean_output)
        reply = parsed_data.get('reply', 'Systems online. How can I assist?')
        emotion = parsed_data.get('emotion', 'happy')

        reply = re.sub(r'\bimagi\b', '', reply, flags=re.IGNORECASE).strip()
        if not reply:
            reply = "Systems nominal."

        speak_safely(reply)

        return jsonify({'reply': reply, 'emotion': emotion})
        
    except Exception as e:
        fallback_reply = "Neural link sync error."
        speak_safely(fallback_reply)
        return jsonify({'reply': fallback_reply, 'emotion': 'sleepy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)