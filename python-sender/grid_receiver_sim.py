import socket
import numpy as np
import cv2
import argparse

def run_receiver(ip, port, matrix_size):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        sock.bind((ip, port))
        sock.settimeout(0.01) # Agar loop tidak tertahan
    except Exception as e:
        print(f"[!] Gagal binding: {e}")
        return

    expected_size = matrix_size * matrix_size * 3
    print(f"[*] Port: {port} | Matrix Size: {matrix_size}x{matrix_size}")
    print("[*] Menunggu data... (Pastikan worker mengirim ke port ini)")

    # Buat jendela dengan flag WINDOW_AUTOSIZE agar ukurannya mengikuti frame
    window_name = "Simulasi LED Matrix"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    try:
        while True:
            try:
                data, addr = sock.recvfrom(65535)
                
                if len(data) == expected_size:
                    # Konversi bytes ke array (H, W, C)
                    frame = np.frombuffer(data, dtype=np.uint8).reshape((matrix_size, matrix_size, 3))
                    
                    # Konversi RGB ke BGR untuk OpenCV
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Tampilkan ukuran asli (tanpa resize)
                    cv2.imshow(window_name, frame_bgr)
                else:
                    print(f"[!] Ukuran data tidak cocok: {len(data)} bytes")

            except socket.timeout:
                pass

            # Cek tombol 'q' untuk keluar
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[*] Keluar...")
                break
                
    except KeyboardInterrupt:
        print("\n[*] Dihentikan dari terminal.")
    finally:
        sock.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=8888, type=int, help="Port UDP")
    parser.add_argument("--size", default=64, type=int, help="Ukuran matrix (misal: 64)")
    args = parser.parse_args()
    
    run_receiver("0.0.0.0", args.port, args.size)
