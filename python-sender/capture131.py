import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import mss
import numpy as np
import pygetwindow as gw
import threading
import time
import subprocess
import sys
import os
from PIL import Image, ImageTk

class GridStreamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Matrix Master Controller - Auto Width Layout")
        self.root.geometry("1400x850")

        # --- STATE ---
        self.is_running_global = False
        self.grid_h = tk.IntVar(value=2)
        self.grid_v = tk.IntVar(value=2)
        self.GRID_PIXELS = 64
        
        self.worker_processes = {} 
        self.receiver_processes = {}
        
        self.roi = [20, 20, 150, 150] 
        self.drag_mode = None
        self.current_scale = 1.0 
        self.current_target_win = None

        self.setup_ui()
        self.refresh_windows()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, pady=10, bg="#2c3e50")
        header.pack(fill="x", side="top")
        
        tk.Label(header, text="Target Window:", bg="#2c3e50", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=(20, 5))
        self.combo = ttk.Combobox(header, width=40, state="readonly")
        self.combo.pack(side="left", padx=5)
        tk.Button(header, text="Refresh", command=self.refresh_windows).pack(side="left", padx=5)
        
        self.btn_main = tk.Button(header, text="START PREVIEW", bg="#27ae60", fg="white", 
                                 font=("Arial", 9, "bold"), command=self.toggle_preview)
        self.btn_main.pack(side="right", padx=20)

        # Body
        self.main_body = tk.Frame(self.root)
        self.main_body.pack(fill="both", expand=True)

        # PANEL KIRI: CONFIG
        # UBAH DISINI: Tidak pakai width fix, tidak pakai pack_propagate(False)
        # Agar lebar panel otomatis mengikuti konten di dalamnya (Fit Content)
        self.left_panel = tk.Frame(self.main_body) 
        self.left_panel.pack(side="left", fill="y", padx=5)
        
        grid_set = tk.LabelFrame(self.left_panel, text=" Layout Settings ", pady=10)
        grid_set.pack(fill="x", side="top", pady=(0, 5))
        tk.Spinbox(grid_set, from_=1, to=10, textvariable=self.grid_h, width=3, command=self.on_layout_change).pack(side="left", padx=5)
        tk.Label(grid_set, text="x").pack(side="left")
        tk.Spinbox(grid_set, from_=1, to=10, textvariable=self.grid_v, width=3, command=self.on_layout_change).pack(side="left", padx=5)

        self.list_container = tk.Frame(self.left_panel)
        self.list_container.pack(fill="both", expand=True)
        
        # Canvas butuh width awal agar tidak terlalu kecil saat start, tapi nanti akan membesar
        self.canvas = tk.Canvas(self.list_container, highlightthickness=0, width=480)
        self.scrollbar = ttk.Scrollbar(self.list_container, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Update scrollregion saat isi berubah
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        # Update lebar window canvas saat canvas berubah
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # PREVIEW PANELS
        self.center_panel = tk.LabelFrame(self.main_body, text=" 1. Source Selector ", bg="#1a1a1a", fg="white")
        self.center_panel.pack(side="left", fill="both", expand=True)
        self.source_label = tk.Label(self.center_panel, bg="black")
        self.source_label.place(relx=0.5, rely=0.5, anchor="center")
        self.source_label.bind("<Button-1>", self.on_source_click)
        self.source_label.bind("<B1-Motion>", self.on_source_drag)
        self.source_label.bind("<ButtonRelease-1>", self.on_source_release)

        self.right_panel = tk.LabelFrame(self.main_body, text=" 2. Grid Preview ", bg="#000", fg="white")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=5)
        self.preview_label = tk.Label(self.right_panel, bg="black")
        self.preview_label.place(relx=0.5, rely=0.5, anchor="center")

        self.render_grid_inputs()

    def on_frame_configure(self, event):
        """Update scrollregion agar scrollbar bekerja"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Update lebar canvas agar pas dengan lebar frame isinya
        self.canvas.config(width=event.width)

    def on_canvas_configure(self, event):
        """Agar frame di dalam canvas melebar mengikuti canvas"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def render_grid_inputs(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.grid_vars = []
        
        for i in range(self.grid_h.get() * self.grid_v.get()):
            # Frame per baris
            row = tk.Frame(self.scrollable_frame, pady=3, padx=2, bd=1, relief="groove")
            row.pack(fill="x", pady=1)
            
            # P1
            tk.Label(row, text=f"P{i+1}", width=3, font=("Arial", 8, "bold")).pack(side="left")
            
            # IP (Lebar 15)
            ip_v = tk.StringVar(value=f"192.168.1.{101+i}")
            tk.Entry(row, textvariable=ip_v, width=15).pack(side="left", padx=1)
            
            # Port
            tk.Label(row, text=":").pack(side="left")
            port_v = tk.StringVar(value="5568")
            tk.Entry(row, textvariable=port_v, width=5).pack(side="left", padx=1)
            
            # Univ (Readonly, Fixed 1)
            tk.Label(row, text="U:", font=("Arial", 8)).pack(side="left", padx=(2,0))
            univ_v = tk.StringVar(value="1") 
            tk.Entry(row, textvariable=univ_v, width=3, state="readonly").pack(side="left", padx=1)
            
            # Tombol SEND
            btn_active = tk.BooleanVar(value=False)
            btn = tk.Button(row, text="SEND", width=6, font=("Arial", 7, "bold"), 
                           command=lambda idx=i: self.toggle_worker_script(idx))
            btn.pack(side="right", padx=1)

            # Tombol TEST RX
            btn_rx_active = tk.BooleanVar(value=False)
            btn_rx = tk.Button(row, text="TEST RECEIVER", width=14, font=("Arial", 7, "bold"), bg="#9b59b6", fg="white",
                           command=lambda idx=i: self.toggle_receiver_script(idx))
            btn_rx.pack(side="right", padx=1)
            
            self.grid_vars.append({
                "ip": ip_v, 
                "port": port_v, 
                "univ": univ_v, 
                "active": btn_active, 
                "btn": btn,
                "rx_active": btn_rx_active,
                "btn_rx": btn_rx
            })

    # ==========================
    # LOGIC SEND (WORKER)
    # ==========================
    def toggle_worker_script(self, idx):
        if not self.grid_vars[idx]["active"].get():
            # START
            if not self.is_running_global:
                messagebox.showwarning("Warning", "Aktifkan 'Start Preview' terlebih dahulu!")
                return

            cfg = self.grid_vars[idx]
            gh, gv = self.grid_h.get(), self.grid_v.get()
            hx, vx = idx % gh, idx // gh
            rx, ry, rw, rh = self.roi
            
            worker_w = rw / gh
            worker_h = rh / gv
            worker_left = self.current_target_win.left + rx + (hx * worker_w)
            worker_top = self.current_target_win.top + ry + (vx * worker_h)

            current_dir = os.path.dirname(os.path.abspath(__file__))
            worker_path = os.path.join(current_dir, "grid_worker_e131.py")
            python_exe = sys.executable

            cmd = [
                python_exe, worker_path,
                "--ip", cfg["ip"].get(),
                "--port", cfg["port"].get(),
                "--universe", cfg["univ"].get(), # Selalu "1"
                "--top", str(int(worker_top)),
                "--left", str(int(worker_left)),
                "--width", str(int(worker_w)),
                "--height", str(int(worker_h)),
                "--size", str(self.GRID_PIXELS)
            ]

            try:
                proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.worker_processes[idx] = proc
                cfg["active"].set(True)
                cfg["btn"].config(text="STOP", bg="#2ecc71", fg="white") 
            except Exception as e:
                messagebox.showerror("Error", f"Worker {idx+1} Gagal: {e}")
        else:
            # STOP
            self.kill_process(self.worker_processes, idx)
            cfg = self.grid_vars[idx]
            cfg["active"].set(False)
            cfg["btn"].config(text="SEND", bg="#f0f0f0", fg="black")

    # ==========================
    # LOGIC TEST RECEIVER
    # ==========================
    def toggle_receiver_script(self, idx):
        cfg = self.grid_vars[idx]
        
        if not cfg["rx_active"].get():
            # START
            current_dir = os.path.dirname(os.path.abspath(__file__))
            receiver_path = os.path.join(current_dir, "grid_receiver_e131.py")
            python_exe = sys.executable
            
            cmd = [
                python_exe, receiver_path,
                "--port", cfg["port"].get(),     
                "--universe", cfg["univ"].get(), 
                "--size", str(self.GRID_PIXELS)
            ]
            
            try:
                proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.receiver_processes[idx] = proc
                
                cfg["rx_active"].set(True)
                cfg["btn_rx"].config(text="STOP TEST", bg="#e74c3c", fg="white") 
                print(f"[*] Receiver {idx+1} Started on Port {cfg['port'].get()}")
            except Exception as e:
                messagebox.showerror("Error", f"Receiver {idx+1} Gagal: {e}\nPastikan file 'grid_receiver_sacn_custom.py' ada.")
        else:
            # STOP
            self.kill_process(self.receiver_processes, idx)
            cfg["rx_active"].set(False)
            cfg["btn_rx"].config(text="TEST RECEIVER", bg="#9b59b6", fg="white") 

    def kill_process(self, process_dict, idx):
        if idx in process_dict:
            proc = process_dict[idx]
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=0.1)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except: pass
            del process_dict[idx]

    def stop_all_streams(self):
        self.is_running_global = False
        
        for idx in list(self.worker_processes.keys()):
            self.kill_process(self.worker_processes, idx)
        for idx in list(self.receiver_processes.keys()):
            self.kill_process(self.receiver_processes, idx)
            
        self.source_label.config(image='')
        self.preview_label.config(image='')
        self.btn_main.config(text="START PREVIEW", bg="#27ae60")
        
        for cfg in self.grid_vars:
            cfg["active"].set(False)
            cfg["btn"].config(text="SEND", bg="#f0f0f0", fg="black")
            cfg["rx_active"].set(False)
            cfg["btn_rx"].config(text="TEST RECEIVER", bg="#9b59b6", fg="white")

    # --- GUI CAPTURE LOOP ---
    def main_loop(self, window_obj):
        self.current_target_win = window_obj
        with mss.mss() as sct:
            while self.is_running_global:
                try:
                    monitor = {"top": window_obj.top, "left": window_obj.left, "width": window_obj.width, "height": window_obj.height}
                    frame = cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_BGRA2BGR)
                    
                    cw_s, ch_s = self.center_panel.winfo_width()-20, self.center_panel.winfo_height()-40
                    fh, fw = frame.shape[:2]
                    self.current_scale = min(cw_s/fw, ch_s/fh)

                    rx, ry, rw, rh = self.roi
                    source_view = frame.copy()
                    cv2.rectangle(source_view, (int(rx), int(ry)), (int(rx+rw), int(ry+rh)), (0, 0, 255), 2)
                    
                    pil_src = Image.fromarray(cv2.cvtColor(source_view, cv2.COLOR_BGR2RGB))
                    pil_src = pil_src.resize((int(fw*self.current_scale), int(fh*self.current_scale)), Image.LANCZOS)

                    gh, gv = self.grid_h.get(), self.grid_v.get()
                    if rw > 0 and rh > 0:
                        cropped = cv2.resize(frame[int(ry):int(ry+rh), int(rx):int(rx+rw)], (gh*64, gv*64))
                        preview_img = cropped.copy()
                        for v in range(gv):
                            for h in range(gh):
                                xp, yp = h*64, v*64
                                cv2.rectangle(preview_img, (xp, yp), (xp+64, yp+64), (0, 255, 255), 1)
                                cv2.putText(preview_img, str(v*gh+h+1), (xp+5, yp+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,255), 1)
                        
                        cw_g, ch_g = self.right_panel.winfo_width()-30, self.right_panel.winfo_height()-50
                        grid_scale = min(cw_g/(gh*64), ch_g/(gv*64))
                        pil_grid = Image.fromarray(cv2.cvtColor(preview_img, cv2.COLOR_BGR2RGB)).resize((int(gh*64*grid_scale), int(gv*64*grid_scale)), Image.NEAREST)
                        
                        img_src_tk = ImageTk.PhotoImage(pil_src)
                        img_grid_tk = ImageTk.PhotoImage(pil_grid)
                        self.root.after(0, self.update_display, img_src_tk, img_grid_tk)
                    time.sleep(0.04)
                except: break

    def update_display(self, src, grid):
        if self.is_running_global:
            self.source_label.config(image=src); self.source_label.image = src
            self.preview_label.config(image=grid); self.preview_label.image = grid

    def toggle_preview(self):
        if not self.is_running_global:
            selection = self.combo.get(); target_win = gw.getWindowsWithTitle(selection)[0]
            self.is_running_global = True; self.btn_main.config(text="STOP PREVIEW", bg="#c0392b")
            threading.Thread(target=self.main_loop, args=(target_win,), daemon=True).start()
        else: self.stop_all_streams()

    def refresh_windows(self):
        titles = gw.getAllTitles(); self.combo['values'] = sorted(list(set([t for t in titles if t.strip()])))
        if self.combo['values']: self.combo.current(0)

    def on_layout_change(self): self.stop_all_streams(); self.render_grid_inputs()
    
    def on_source_click(self, event):
        if self.current_scale == 0: return
        ex, ey = event.x / self.current_scale, event.y / self.current_scale
        rx, ry, rw, rh = self.roi
        if rx < ex < rx + rw and ry < ey < ry + rh: self.drag_mode = 'move'; self.off_x, self.off_y = ex - rx, ey - ry
        else: self.drag_mode = 'resize'; self.ix, self.iy = ex, ey

    def on_source_drag(self, event):
        if not self.drag_mode: return
        ex, ey = event.x / self.current_scale, event.y / self.current_scale
        gh, gv = self.grid_h.get(), self.grid_v.get()
        if self.drag_mode == 'move': self.roi[0] = max(0, ex - self.off_x); self.roi[1] = max(0, ey - self.off_y)
        elif self.drag_mode == 'resize':
            rw = max(10, abs(ex - self.ix)); rh = int(rw / (gh/gv))
            self.roi[2], self.roi[3] = rw, rh; self.roi[0] = self.ix if ex > self.ix else self.ix - rw; self.roi[1] = self.iy if ey > self.iy else self.iy - rh

    def on_source_release(self, event): 
        self.drag_mode = None
        for i, cfg in enumerate(self.grid_vars):
            if cfg["active"].get():
                self.toggle_worker_script(i) 
                self.root.after(200, lambda idx=i: self.toggle_worker_script(idx))

    def on_closing(self): self.stop_all_streams(); self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GridStreamerApp(root)
    root.mainloop()