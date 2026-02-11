import sacn
import numpy as np
import cv2
import argparse
import time

def run_receiver_lib(size, start_universe, port):
    # 1. Hitung Buffer
    total_pixels = size * size
    total_channels = total_pixels * 3 # RGB
    frame_buffer = np.zeros(total_channels, dtype=np.uint8)
    
    # 510 adalah standar payload sACN untuk RGB (170 pixel x 3)
    channels_per_universe = 510 
    
    # Hitung berapa universe yang perlu kita dengarkan untuk memenuhi 1 matrix
    total_universes_needed = int(total_channels / channels_per_universe) + 1
    
    print(f"[*] Starting sACN Receiver (Library Mode)")
    print(f"[*] Port: {port}")
    print(f"[*] Matrix: {size}x{size} | Total Universes: {total_universes_needed}")
    print(f"[*] Listening Universe range: {start_universe} -> {start_universe + total_universes_needed - 1}")

    # 2. Inisialisasi Receiver dengan Custom Port
    # bind_port ditambahkan di sini untuk mengganti default 5568
    receiver = sacn.sACNreceiver(bind_address="0.0.0.0", bind_port=port)
    receiver.start()

    # 3. Definisi Fungsi Callback
    def packet_callback(packet):
        # Hitung posisi data ini harus ditaruh di buffer mana
        uni_offset = packet.universe - start_universe
        
        if uni_offset >= 0:
            buffer_index = uni_offset * channels_per_universe
            data = packet.dmxData
            data_len = len(data)
            
            # Safety check agar tidak array index out of bound
            if buffer_index + data_len <= total_channels:
                # Salin data ke buffer utama
                frame_buffer[buffer_index : buffer_index + data_len] = data

    # 4. Daftarkan Callback
    for i in range(total_universes_needed):
        univ_id = start_universe + i
        receiver.register_listener("universe", packet_callback, universe=univ_id)
        # Gabung multicast (opsional, tapi aman dinyalakan)
        receiver.join_multicast(univ_id)

    print("[*] Receiver running... Press 'q' to exit.")
    
    window_name = f"sACN Receiver (Port {port})"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    try:
        while True:
            # 5. Loop Display
            frame_2d = frame_buffer.reshape((size, size, 3))
            frame_bgr = cv2.cvtColor(frame_2d, cv2.COLOR_RGB2BGR)
            cv2.imshow(window_name, frame_bgr)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n[*] Stopping...")
    finally:
        receiver.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Menambahkan argumen Port
    parser.add_argument("--port", default=5568, type=int, help="Custom UDP Port (default: 5568)")
    parser.add_argument("--size", default=64, type=int, help="Matrix Size (default: 64)")
    parser.add_argument("--universe", default=1, type=int, help="Start Universe ID (default: 1)")
    
    args = parser.parse_args()
    
    run_receiver_lib(args.size, args.universe, args.port)