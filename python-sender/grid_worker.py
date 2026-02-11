import cv2
import mss
import numpy as np
import socket
import argparse
import time
import sys

def run_worker(ip, port, top, left, width, height, target_size=64):
    print(f"[*] Worker started for {ip}:{port}")
    print(f"[*] Target ROI: {width}x{height} at ({left}, {top})")
    
    # Inisialisasi Socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Area monitor untuk mss
    monitor = {
        "top": int(top),
        "left": int(left),
        "width": int(width),
        "height": int(height)
    }

    try:
        with mss.mss() as sct:
            while True:
                # 1. Capture area spesifik
                sct_img = sct.grab(monitor)
                frame = np.array(sct_img)
                
                # 2. Konversi BGRA ke BGR (OpenCV) lalu ke RGB (LED)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # 3. Resize ke resolusi grid (default 64x64)
                resized = cv2.resize(frame, (target_size, target_size), interpolation=cv2.INTER_NEAREST)
                rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                
                # 4. Kirim data raw bytes via UDP
                data = rgb_frame.flatten().tobytes()
                sock.sendto(data, (ip, int(port)))
                
                # Limit FPS (~25-30 FPS) agar tidak membebani CPU
                time.sleep(0.03)
                
    except KeyboardInterrupt:
        print(f"\n[!] Worker {ip} stopped by user.")
    except Exception as e:
        print(f"\n[!] Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone Grid Capture Worker")
    
    # Parameter wajib
    parser.add_argument("--ip", required=True, help="Target ESP32 IP Address")
    parser.add_argument("--port", default=8888, type=int, help="UDP Port (default: 8888)")
    parser.add_argument("--top", required=True, type=int, help="ROI Top coordinate")
    parser.add_argument("--left", required=True, type=int, help="ROI Left coordinate")
    parser.add_argument("--width", required=True, type=int, help="ROI Width")
    parser.add_argument("--height", required=True, type=int, help="ROI Height")
    parser.add_argument("--size", default=64, type=int, help="Target matrix size (default: 64)")

    args = parser.parse_args()

    run_worker(args.ip, args.port, args.top, args.left, args.width, args.height, args.size)
