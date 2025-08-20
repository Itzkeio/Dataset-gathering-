import cv2
import numpy as np
import datetime
import time
import os
from pathlib import Path
import sys
import threading

class ImageCapture:
    def __init__(self, output_dir='captured_images', interval=2, cameraSource=None):
        if cameraSource is None:
            self.cameraSource = [0]  # Default to the first webcam
        elif isinstance(cameraSource, (int, str)):
            self.cameraSource = [cameraSource]
        else:
            self.cameraSource = cameraSource
        
        self.image_counter = 1
        self.captured_images = []
        self.start_time = None
        self.end_time = None
        self.is_capturing = False
        self.quit_flag = False
        self.is_paused = False
        self.cameras = [] 
        self.capture_interval = interval

        # Ensure output directory exists
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self._initializeCamera()

        self.logFile = self.output_dir / 'capture_log.txt'

    def _initializeCamera(self):
        print(f"Initializing {len(self.cameraSource)} camera(s)...")

        for i, cameraSource in enumerate(self.cameraSource):
            print(f"Connecting to camera {i + 1} at source {cameraSource}...")
            cap = cv2.VideoCapture(cameraSource)

            if isinstance(cameraSource, str):
                # Reduce buffering for network streams (RTSP/HTTP)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                cap.release()
                raise RuntimeError(f"Could not open camera source {cameraSource}")
            
            # Test camera connection
            ret, _ = cap.read()
            if not ret:
                cap.release()
                raise RuntimeError(f"Error: could not read from camera source {cameraSource}")
            
            self.cameras.append({
                'cap': cap,
                'source': cameraSource,
                'id': i+1
            })
            print(f"Camera {i + 1} connected.")

        print("All cameras initialized successfully.")

    def captureImages(self):
        timestamp = time.strftime("%d%m%Y_%H%M%S")
        captured_images = []

        for camera in self.cameras:
            ret, frame = camera['cap'].read()
            if ret:
                # Create a file name with camera ID
                if len(self.cameras) > 1:
                    filename = f"{self.image_counter}_camera{camera['id']}_{timestamp}.jpg"
                else:
                    filename = f"{self.image_counter}_{timestamp}.jpg"

                filepath = self.output_dir / filename
                cv2.imwrite(str(filepath), frame)

                captured_images.append({
                    'filename': filename,
                    'camera_id': camera['id'],
                    'camera_source': camera['source'],
                    'timestamp': datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                })

                print(f"Captured from camera {camera['id']}: {filename}")
            else:
                print(f"Error: Failed to capture from Camera {camera['id']}")
                return False
                
        if captured_images:
            self.captured_images.append({
                'counter': self.image_counter,
                'timestamp': timestamp,
                'files': captured_images
            })
            self.image_counter += 1
            return True
        return False
        
    def generate_filename(self):
        timestamp = time.strftime("%d%m%Y_%H%M%S")
        filename = f"{self.image_counter}_{timestamp}.jpg"
        return filename
        
    def capture_image(self):
        return self.captureImages()
        
    def keyboardListener(self):
        print("Controls")
        print("Press 'P' to pause/resume capture")
        print("Press 'Q' to quit")

        while not self.quit_flag:
            try:
                user_input  = input().upper().strip()
                if user_input == 'Q':
                    print("Quitting Capturing")
                    self.quit_flag = True
                    break
                elif user_input == 'P':
                    if self.is_paused:
                        print("Resuming capture...")
                        self.is_paused = False
                    else:
                        print("Pausing capture...")
                        self.is_paused = True
                else:
                    print("Invalid input. Press 'P' to pause/resume or 'Q' to quit.")
            except (EOFError, KeyboardInterrupt):
                self.quit_flag = True
                break
        
    def create_log_file(self):
        try:
            with open(self.logFile, 'w') as f:
                f.write("Capture Log\n")
                f.write(f"Number of Cameras: {len(self.cameras)}\n")
                for i, source in enumerate(self.cameraSource, 1):
                    f.write(f"Camera {i}: {source}\n")
                f.write(f"Start Time: {self.start_time}\n")
                f.write(f"End Time: {self.end_time}\n")

                if self.start_time and self.end_time:
                    start_dt = datetime.datetime.strptime(self.start_time, "%d-%m-%Y %H:%M:%S")
                    end_dt = datetime.datetime.strptime(self.end_time, "%d-%m-%Y %H:%M:%S")
                    duration = end_dt - start_dt
                    f.write(f"Total Duration: {duration}\n")

                totalFiles = sum(len(session['files']) for session in self.captured_images)
                f.write(f"Total Images Captured: {totalFiles}\n")

                f.write("Captured Images:\n")
                for session in self.captured_images:
                    f.write(f"\n--- Capture Session {session['counter']} at {session['timestamp']} ---\n")
                    for file_info in session['files']:
                        f.write(f"Camera {file_info['camera_id']} : {file_info['filename']}\n")

                f.write("\nEnd of Log\n")
            print(f"Log file created at {self.logFile}")

        except Exception as e:
            print(f"Error creating log file: {e}")

    def start_capture(self):
        print("Starting image capture...")

        self.start_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.is_capturing = True

        keyboard_thread = threading.Thread(target=self.keyboardListener)
        keyboard_thread.daemon = True  # Allow thread to exit when main program exits
        keyboard_thread.start()

        try:
            while not self.quit_flag:
                if self.capture_image():
                    for _ in range(int(self.capture_interval * 10)):
                        if self.quit_flag:
                            break
                        if self.is_paused:
                            print("Press 'P' to resume or 'Q' to quit.")
                            while self.is_paused and not self.quit_flag:
                                time.sleep(0.5)
                            if not self.quit_flag:
                                print("Resuming capture...")
                            break
                        time.sleep(0.1)
                else:
                    break
        
        except KeyboardInterrupt:
            print("Capture interrupted by user.")
            self.quit_flag = True

        self.end_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        self.is_capturing = False

        for camera in self.cameras:
            camera['cap'].release()
        cv2.destroyAllWindows()

        self.create_log_file()

def main():
    print("Image Capture Tool")
    print("-" * 30)

    try:
        #  Replace these with your RTSP camera URLs
        camera_sources = [
            "rtsp://admin:Admin1234@10.209.3.125:554"
            
            
        ]

        output_dir = input("Enter output directory (default: 'captured_images'): ").strip()
        if not output_dir:
            output_dir = 'captured_images'

        interval = input("Enter capture interval in seconds (default: 2): ").strip()
        if not interval:
            capture_interval = 2.0
        else:
            capture_interval = float(interval)
    
    except (ValueError, KeyboardInterrupt):
        print("Using default settings..")
        camera_sources = [
            "rtsp://admin:Admin1234@10.209.3.125:554"
        ]
        output_dir = 'captured_images'
        capture_interval = 2.0

    try:
        capture_tool = ImageCapture(output_dir=Path(output_dir), interval=capture_interval, cameraSource=camera_sources)
        capture_tool.start_capture()
    
    except RuntimeError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()  