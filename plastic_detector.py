import cv2 
import requests 
import time 
import os 
import numpy as np 
from datetime import datetime 
from inference_sdk import InferenceHTTPClient 

#  Configuration  
PUSHBULLET_TOKEN = "o.VAk0ncFJBEhvA3DbHJwxwnKQyzDcoZxm"  # Your Pushbullet 
token 
ROBOFLOW_API_KEY = "JULLQT7G8cx3je67zSHV"                # Roboflow key 
MODEL_ID = "plastic-bag-detection-luxxh/2”                          
SNAPSHOTS_DIR = "detection_snapshots" 

# Detection Settings (Optimized for Pi 5) 
# model ID 
# Directory to store snapshots 

MIN_CONFIDENCE = 0.5      # 50% confidence threshold 
INFERENCE_INTERVAL = 2.0  # Slightly longer interval for Pi 
ALERT_COOLDOWN = 300      # 5 minutes between alerts 
RESOLUTION = (320, 240)   # Camera resolution (keep low for Pi) 
JPEG_QUALITY = 70   
      # Lower quality for faster processing 
# ===== Core Functions ===== 
class PlasticDetector: 
def _init_(self): 
self.last_alert_time = 0 
self.detection_count = 0 
self.last_inference_time = 0 
self.client = InferenceHTTPClient( 
api_url="https://detect.roboflow.com", 
api_key=ROBOFLOW_API_KEY 
) 
self.temp_img_path = "/tmp/plastic_temp.jpg" 
self.encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY] 
# Create snapshots directory if it doesn't exist 
if not os.path.exists(SNAPSHOTS_DIR): 
os.makedirs(SNAPSHOTS_DIR) 
def send_alert_with_snapshot(self, confidence, snapshot_path): 
"""Send push notification with snapshot via Pushbullet""" 
try: 
current_time = time.time() 
if current_time - self.last_alert_time > ALERT_COOLDOWN: 
# First upload the file 
with open(snapshot_path, "rb") as f: 
file_data = f.read() 
upload_response = requests.post( 
"https://api.pushbullet.com/v2/upload-request", 
headers={"Access-Token": PUSHBULLET_TOKEN}, 
json={ 
"file_name": os.path.basename(snapshot_path), 
"file_type": "image/jpeg" 
}, 
timeout=5 
) 
if upload_response.status_code == 200: 
upload_data = upload_response.json() 
# Upload the actual file 
with open(snapshot_path, "rb") as f: 
upload_file = requests.post( 
upload_data["upload_url"], 
files={"file": f}, 
data=upload_data["data"], 
timeout=10 
) 
# Send the push notification with file link 
response = requests.post( 
"https://api.pushbullet.com/v2/pushes", 
headers={"Access-Token": PUSHBULLET_TOKEN}, 
json={ 
"type": "file", 
"title": " PLASTIC DETECTED", 
"body": (f"Confidence: {confidence:.0%}\n" 
f"Total Today: {self.detection_count}\n" 
f"Time: {datetime.now().strftime('%H:%M:%S')}"), 
"file_name": upload_data["file_name"], 
"file_type": upload_data["file_type"], 
"file_url": upload_data["file_url"] 
}, 
timeout=5 
) 
self.last_alert_time = current_time 
return response.status_code == 200 
return False 
except Exception as e: 
print(f"Alert error: {e}") 
return False 
def save_snapshot(self, frame): 
"""Save a snapshot of the detection with timestamp""" 
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
snapshot_path = os.path.join(SNAPSHOTS_DIR, f"plastic_{timestamp}.jpg") 
cv2.imwrite(snapshot_path, frame, self.encode_params) 
return snapshot_path 
def process_frame(self, frame): 
"""Run detection on a camera frame""" 
try: 
current_time = time.time() 
if current_time - self.last_inference_time < INFERENCE_INTERVAL: 
return frame, False 
self.last_inference_time = current_time 
# Optimized image saving for Pi 
cv2.imwrite(self.temp_img_path, frame, self.encode_params) 
# Run inference 
result = self.client.infer(self.temp_img_path, model_id=MODEL_ID) 
os.remove(self.temp_img_path) 
# Process results 
plastic_detected = False 
max_confidence = 0.0 
detection_frame = frame.copy() 
for pred in result.get("predictions", []): 
if 
pred['class'].lower() in ['plastic', 'plastic-wrapper'] and pred['confidence'] >= 
MIN_CONFIDENCE: 
plastic_detected = True 
self.detection_count += 1 
max_confidence = max(max_confidence, pred['confidence']) 
# Draw detection markers 
x, y = int(pred["x"]), int(pred["y"]) 
w, h = int(pred["width"]), int(pred["height"]) 
cv2.rectangle(detection_frame, (x-w//2, y-h//2), (x+w//2, y+h//2), (0, 0, 255), 1) 
cv2.putText(detection_frame, f"{pred['confidence']:.0%}",  
(x-w//2, y-h//2-5), cv2.FONT_HERSHEY_SIMPLEX,  
0.4, (0, 0, 255), 1) 
if plastic_detected: 
# Save and send snapshot 
snapshot_path = self.save_snapshot(detection_frame) 
self.send_alert_with_snapshot(max_confidence, snapshot_path) 
return detection_frame, plastic_detected 
except Exception as e: 
print(f"Inference error: {e}") 
return frame, False 
#  Main Loop  
def main(): 
detector = PlasticDetector() 
# Pi-optimized video capture 
cap = cv2.VideoCapture(0) 
cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0]) 
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1]) 
cap.set(cv2.CAP_PROP_FPS, 10)  # Lower FPS for Pi 
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer 
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Better for Pi camera 
# Warm up camera 
for _ in range(5): 
cap.read() 
try: 
while True: 
start_time = time.time() 
# Read frame 
ret, frame = cap.read() 
if not ret: 
time.sleep(0.1) 
continue 
# Process frame 
processed_frame, _ = detector.process_frame(frame) 
# Simple display (no GUI on headless Pi) 
cv2.putText(processed_frame, f"Detects: {detector.detection_count}",  
(10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1) 
# Only display if not running headless 
try: 
cv2.imshow('Plastic Detector', processed_frame) 
if cv2.waitKey(1) & 0xFF == ord('q'): 
break 
except: 
pass  # Running headless 
# Control loop speed 
elapsed = time.time() - start_time 
if elapsed < 0.1: 
time.sleep(0.1 - elapsed) 
finally: 
cap.release() 
try: 
cv2.destroyAllWindows() 
except: 
pass 
print(f"\nSession ended. Total detections: {detector.detection_count}") 
if _name_ == "_main_": 
print("Starting plastic detection system on Raspberry Pi...") 
print(f"• Confidence threshold: {MIN_CONFIDENCE:.0%}") 
print(f"• Alert cooldown: {ALERT_COOLDOWN//60} minutes") 
print(f"• Processing resolution: {RESOLUTION[0]}x{RESOLUTION[1]}") 
print(f"• Snapshots will be saved to: {SNAPSHOTS_DIR}") 
print("Press 'q' to quit (if running with display)\n") 
main()