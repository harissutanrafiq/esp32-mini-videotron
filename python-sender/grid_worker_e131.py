import cv2
import mss
import numpy as np
import argparse
import time
import sacn  # Pastikan sudah pip install sacn

def run_worker(ip, top, left, width, height, target_size=64, start_universe=1,port=5568):
    print(f"[*] Worker E1.31 (Library Mode) Started")
    print(f"[*] Target IP: {ip} (Port Default: 5568)")
    print(f"[*] ROI: {width}x{height} -> Grid: {target_size}x{target_size}")
    
    # 1. Inisialisasi Sender sACN
    sender = sacn.sACNsender(source_name="PyMatrixWorker")
    sender.start() 
    
    # 64x64 pixel * 3 warna = 12.288 channel
    # 1 Universe muat 510 channel (agar genap dibagi 3)
    channels_per_universe = 510 
    
    # Hitung jumlah universe yang dibutuhkan
    max_universes_needed = int((target_size * target_size * 3) / channels_per_universe) + 1
    
    active_universes = []
    
    # Daftarkan Universe
    for i in range(max_universes_needed):
        univ_id = start_universe + i
        sender.activate_output(univ_id)
        
        # PENTING: Library sacn tidak punya 'destination_port'.
        # Port otomatis 5568. Kita hanya set IP (Unicast).
        sender[univ_id].destination = ip 
        sender[univ_id].multicast = False 
        sender[i+1].destinationPort = port 
        
        active_universes.append(univ_id)
        
    print(f"[*] Active Universes: {active_universes[0]} - {active_universes[-1]}")

    monitor = {"top": int(top), "left": int(left), "width": int(width), "height": int(height)}

    try:
        with mss.mss() as sct:
            while True:
                # 2. Capture & Process
                frame = np.array(sct.grab(monitor))
                
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                resized = cv2.resize(frame_bgr, (target_size, target_size), interpolation=cv2.INTER_NEAREST)
                rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                
                # Flatten data
                flat_data = rgb_frame.flatten().tolist()
                total_data = len(flat_data)
                
                # 3. Kirim per Universe
                for i, univ_id in enumerate(active_universes):
                    start_idx = i * channels_per_universe
                    end_idx = start_idx + channels_per_universe
                    
                    if start_idx < total_data:
                        chunk = flat_data[start_idx : end_idx]
                        sender[univ_id].dmx_data = chunk
                    else:
                        break 
                
                time.sleep(0.03) # ~30 FPS
                
    except KeyboardInterrupt:
        print("\n[!] Worker stopped.")
    except Exception as e:
        print(f"\n[!] Error: {e}")
    finally:
        sender.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True, help="Target IP Address")
    # Port dihapus dari argumen wajib karena library sacn memaksakan 5568
    parser.add_argument("--port", default=5568, type=int, help="Ignored (Standard E1.31 uses 5568)") 
    parser.add_argument("--top", required=True, type=int)
    parser.add_argument("--left", required=True, type=int)
    parser.add_argument("--width", required=True, type=int)
    parser.add_argument("--height", required=True, type=int)
    parser.add_argument("--size", default=64, type=int)
    parser.add_argument("--universe", default=1, type=int)

    args = parser.parse_args()

    run_worker(args.ip, args.top, args.left, args.width, args.height, args.size, args.universe,args.port)