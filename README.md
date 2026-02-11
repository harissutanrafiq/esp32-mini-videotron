# esp32-mini-videotron
Making a simple videotron using ESP32



# Matrix Master Controller - Documentation

This system is designed to capture a specific screen area (ROI), divide it into a grid, and stream raw RGB pixel data to LED panels (ESP32/HUB75) via the UDP protocol using a multi-process architecture.

------------------------------------------------------------
1. PYTHON 3.6.1 INSTALLATION GUIDE
------------------------------------------------------------

A. WINDOWS:
   1. Download: Visit python.org and look for the Python 3.6.1 release.
   2. Installer: Select "Windows x86-64 executable installer".
   3. IMPORTANT: During installation, check the box "Add Python 3.6 to PATH".
   4. Verify: Open Command Prompt and type: python --version

B. LINUX UBUNTU (18.04/20.04+):
   Since Python 3.6 is an older release, use the 'deadsnakes' PPA:
   1. Run the following commands:
      sudo add-apt-repository ppa:deadsnakes/ppa
      sudo apt update
      sudo apt install python3.6 python3.6-venv python3.6-dev
   2. Install PIP for 3.6:
      curl https://bootstrap.pypa.io/pip/3.6/get-pip.py -o get-pip.py
      python3.6 get-pip.py

------------------------------------------------------------
2. DEPENDENCIES & LIBRARY INSTALLATION
------------------------------------------------------------

Open your Terminal or Command Prompt in the project folder and run the following command. Note that specific versions are used to ensure compatibility with Python 3.6.1:

pip install opencv-python==4.3.0.38 numpy==1.19.5 mss Pillow==8.4.0 pygetwindow

(Linux users: if you encounter OpenCV errors, run: 
sudo apt install libgl1-mesa-glx libglib2.0-0)

------------------------------------------------------------
3. HOW TO RUN THE SYSTEM
------------------------------------------------------------

Ensure all script files are located in the same folder:

A. MASTER CONTROLLER (capture.py):
   Run: python capture.py
   - Select the target window from the dropdown menu.
   - Configure Layout Settings (H x V grid).
   - Enter the Destination IP and Port for each panel.
   - Click "Start Preview", then adjust the red box (ROI) on the screen.
   - Toggle the "OFF" button to "ON" for the specific worker to start streaming.

B. GRID WORKER (grid_worker.py):
   This script handles the data transmission. It is called automatically 
   by the Master Controller as a subprocess. DO NOT run it manually.

C. RECEIVER SIMULATOR (grid_receiver_sim.py):
   Use this to test without physical LED hardware:
   Run: python grid_receiver_sim.py --port 8888 --size 64

------------------------------------------------------------
4. PROJECT STRUCTURE
------------------------------------------------------------
- capture.py           (Main Dashboard GUI)
- grid_worker.py        (Data Sender / Worker)
- grid_receiver_sim.py  (Virtual Matrix Simulator)
- README.md             (This documentation file)

------------------------------------------------------------
5. TROUBLESHOOTING TIPS
------------------------------------------------------------
- Firewall: Ensure Windows/Linux Firewall is not blocking UDP traffic on your chosen ports.
- Local Testing: Use IP 127.0.0.1 if running both the Master and Simulator on the same PC.
- UI Focus: When using the Simulator, click on the image window before pressing 'q' to exit.
============================================================
- Gunakan IP 127.0.0.1 jika menjalankan semuanya di satu PC.
============================================================
