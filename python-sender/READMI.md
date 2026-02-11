
Sistem ini digunakan untuk menangkap area layar (ROI), membaginya 
ke dalam grid, dan mengirimkan data pixel RGB ke panel LED 
melalui protokol UDP.

------------------------------------------------------------
1. PANDUAN INSTALASI PYTHON 3.6.1
------------------------------------------------------------

A. WINDOWS:
   1. Download: Buka python.org, cari versi 3.6.1.
   2. Pilih: "Windows x86-64 executable installer".
   3. PENTING: Saat instalasi, centang "Add Python 3.6 to PATH".
   4. Cek: Buka Command Prompt, ketik: python --version

B. LINUX UBUNTU (18.04/20.04+):
   1. Jalankan perintah berikut di terminal:
      sudo add-apt-repository ppa:deadsnakes/ppa
      sudo apt update
      sudo apt install python3.6 python3.6-venv python3.6-dev
   2. Instal PIP:
      curl https://bootstrap.pypa.io/pip/3.6/get-pip.py -o get-pip.py
      python3.6 get-pip.py

------------------------------------------------------------
2. INSTALASI DEPENDENSI (LIBRARY)
------------------------------------------------------------

Buka Terminal/CMD di folder project, lalu jalankan:

pip install opencv-python==4.3.0.38 numpy mss Pillow pygetwindow

(Khusus Linux jika ada error OpenCV, jalankan: 
sudo apt install libgl1-mesa-glx libglib2.0-0)

------------------------------------------------------------
3. CARA MENJALANKAN SISTEM
------------------------------------------------------------

Pastikan file-file berikut berada dalam satu folder:

A. MASTER CONTROLLER (capture.py):
   Jalankan: python capture.py
   - Pilih jendela target di dropdown.
   - Atur layout (H x V).
   - Masukkan IP dan Port tujuan.
   - Klik "Start Preview", atur kotak merah (ROI).
   - Nyalakan tombol "ON" pada panel yang diinginkan.

B. GRID WORKER (grid_worker.py):
   Script ini akan dijalankan otomatis oleh Master. 
   Jangan jalankan secara manual.

C. RECEIVER SIMULATOR (grid_receiver_sim.py):
   Gunakan untuk tes tanpa hardware:
   Jalankan: python grid_receiver_sim.py --port 8888 --size 64

------------------------------------------------------------
4. STRUKTUR FILE PROYEK
------------------------------------------------------------
- main_app.py           (Aplikasi Utama/GUI)
- grid_worker.py        (Pengirim Data)
- grid_receiver_sim.py  (Simulator Penampil)
- DOKUMENTASI.txt       (File ini)

------------------------------------------------------------
5. TIPS TROUBLESHOOTING
------------------------------------------------------------
- Jika gambar di receiver tidak muncul, cek apakah IP & Port 
  sudah sesuai antara Master dan Receiver.
- Pastikan Firewall tidak memblokir koneksi UDP.
- Gunakan IP 127.0.0.1 jika menjalankan semuanya di satu PC.
============================================================
