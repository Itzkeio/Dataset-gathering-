import cv2
import time
import os

# RTSP URL
rtsp_url = "ff"

# Open stream
cap = cv2.VideoCapture(rtsp_url)

# Check if connected
if not cap.isOpened():
    print("❌ Gagal membuka stream RTSP")
    exit()

# Target FPS for saving screenshots
save_fps = 1   # save 1 image per second
frame_interval = 1 / save_fps  

# Output folder
output_folder = "helmet"
os.makedirs(output_folder, exist_ok=True)

frame_count = 0
last_save_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠ Gagal mengambil frame, mencoba ulang...")
        continue

    # Show live stream
    cv2.imshow("RTSP Live", frame)

    # Save frame only at interval
    current_time = time.time()
    if current_time - last_save_time >= frame_interval:
        filename = os.path.join(output_folder, f"frame_{frame_count:05d}.jpg")
        cv2.imwrite(filename, frame)
        print(f"✅ Screenshot disimpan: {filename}")
        frame_count += 1
        last_save_time = current_time

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
