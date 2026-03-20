import sys
import subprocess
import os
import time # Import time globally for retries

# --- Dependency Manager ---
def install_dependencies():
    """
    Checks if dependencies are installed. 
    If not, installs them and creates a flag file to skip future checks.
    """
    required_packages = [
        "customtkinter",
        "httplib2",
        "google-api-python-client",
        "oauth2client"
    ]
    
    flag_file = ".dependencies_installed"

    if not os.path.exists(flag_file):
        print("First run detected. Installing required libraries... Please wait.")
        try:
            for package in required_packages:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            
            # Create a flag file
            with open(flag_file, "w") as f:
                f.write("Installation completed on: " + time.ctime())
            
            print("All libraries installed successfully!")
        except Exception as e:
            print(f"Error during installation: {e}")
            sys.exit(1)

# Run installer
if __name__ == '__main__':
    install_dependencies()

# --- GUI and Logic Imports ---
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import io
import json
from pathlib import Path
import re

# Google API Imports
import httplib2
from apiclient import discovery
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
from oauth2client import client
from oauth2client.file import Storage
from oauth2client import tools

# --- Developer Credentials ---
CLIENT_ID = "651071974405-o20dbl7j39mjq0fbn14gukeq1lm3ppfs.apps.googleusercontent.com"
CLIENT_SECRET = "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"

SCOPES = 'https://www.googleapis.com/auth/drive'
TOKEN_FILE = 'token.json'
SETTINGS_FILE = 'settings.json'
APPLICATION_NAME = 'Python OCR with Drive API'

class OcrApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Batch Google Docs OCR V 1.0 By (MrGamesKingPro)")
        self.geometry("800x800") 
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.credentials = None
        self.processing_thread = None
        self.is_stopping = False 

        self.create_widgets()
        self.display_welcome_guide()
        self.load_settings()

    def display_welcome_guide(self):
        guide_text = (
            "Welcome to the Advanced OCR Processor\n"
            "Developed by: MrGamesKingPro\n"
            "----------------------------------------------------------\n"
            "NOTE: Manual library installation is NOT required. \n"
            "All dependencies are installed automatically on the first run.\n"
            "----------------------------------------------------------\n\n"
            "--- HOW TO USE ---\n"
            "1. Select Mode: Choose 'Single Folder' or 'Multi-Folder'.\n"
            "2. Subfolder Structure: Specify where images are located.\n"
            "3. Folders: Select Source (images) and Output (SRT) paths.\n"
            "4. Drive Folder ID (Optional):\n"
            "   - Enter an ID to keep files organized in your Drive.\n"
            "   - If unchecked, files are uploaded to your Drive root.\n"
            "5. Threads: Adjust based on your connection (Default: 20).\n"
            "6. Start: Click 'Start Processing'.\n"
            "7. Auth: Log in via browser when prompted. Processing starts automatically.\n\n"
            "--- EXAMPLES ---\n"
            "▶ Single Folder Mode:\n"
            "   - Source: C:/Videos/Frames/ -> Result: C:/Subtitles/Frames.srt\n\n"
            "▶ Multi-Folder Mode (Direct):\n"
            "   - Source: C:/Videos/ (Contains Video1/, Video2/)\n"
            "   - Result: C:/Subtitles/Video1.srt, Video2.srt\n\n"
            "▶ Multi-Folder (With Subfolders):\n"
            "   - Source: C:/Videos/ (Contains Video1/RGBImages/)\n"
            "   - Result: C:/Subtitles/Video1.srt\n"
            "----------------------------------------------------------\n"
            "System Ready. No credentials.json file required.\n"
        )
        self.log(guide_text)
        self.after(100, lambda: self.log_box.see("1.0"))

    def create_widgets(self):
        # Settings Frame
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(settings_frame, text="Source Folder:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.source_entry = ctk.CTkEntry(settings_frame)
        self.source_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(settings_frame, text="Browse", width=100, command=self.browse_source).grid(row=0, column=2, padx=10, pady=5)

        ctk.CTkLabel(settings_frame, text="Output Folder:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.output_entry = ctk.CTkEntry(settings_frame)
        self.output_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(settings_frame, text="Browse", width=100, command=self.browse_output).grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkLabel(settings_frame, text="Drive Folder ID:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.folder_id_entry = ctk.CTkEntry(settings_frame, placeholder_text="Optional ID")
        self.folder_id_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.use_id_var = ctk.StringVar(value="on")
        ctk.CTkCheckBox(settings_frame, text="Use ID", variable=self.use_id_var, onvalue="on", offvalue="off").grid(row=2, column=2, padx=10, pady=5)

        ctk.CTkLabel(settings_frame, text="Threads:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.threads_entry = ctk.CTkEntry(settings_frame)
        self.threads_entry.insert(0, "20")
        self.threads_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        # Mode Selection
        mode_frame = ctk.CTkFrame(self)
        mode_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        mode_frame.grid_columnconfigure((0,1,2), weight=1)
        self.mode_var = ctk.StringVar(value="Single") 
        ctk.CTkRadioButton(mode_frame, text="Single Folder", variable=self.mode_var, value="Single").grid(row=0, column=0, pady=10)
        ctk.CTkRadioButton(mode_frame, text="Multi-Folder", variable=self.mode_var, value="Multi-Folder").grid(row=0, column=1, pady=10)
        self.nested_var = ctk.StringVar(value="None (Directly inside)")
        ctk.CTkOptionMenu(mode_frame, values=["RGBImages", "TXTImages", "None (Directly inside)"], variable=self.nested_var).grid(row=0, column=2, padx=5, pady=10)

        # Execution
        exec_frame = ctk.CTkFrame(self)
        exec_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        exec_frame.grid_columnconfigure((0, 1), weight=1)
        self.start_btn = ctk.CTkButton(exec_frame, text="Start Processing", command=self.start_processing_thread)
        self.start_btn.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        self.stop_btn = ctk.CTkButton(exec_frame, text="Stop", fg_color="#922B21", state="disabled", command=self.stop_processing)
        self.stop_btn.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.status_lbl = ctk.CTkLabel(exec_frame, text="") 
        self.status_lbl.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        self.progress = ctk.CTkProgressBar(exec_frame)
        self.progress.set(0)
        self.progress.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Log
        self.log_box = ctk.CTkTextbox(self, state="disabled", text_color="#A9A9A9", font=("Consolas", 12))
        self.log_box.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

    def save_settings(self):
        data = {"src": self.source_entry.get(), "out": self.output_entry.get(), "id": self.folder_id_entry.get(), "use": self.use_id_var.get(), "th": self.threads_entry.get(), "mode": self.mode_var.get(), "nest": self.nested_var.get()}
        with open(SETTINGS_FILE, "w") as f: json.dump(data, f)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                d = json.load(f)
                self.source_entry.insert(0, d.get("src", "")); self.output_entry.insert(0, d.get("out", ""))
                self.folder_id_entry.insert(0, d.get("id", "")); self.use_id_var.set(d.get("use", "on"))
                self.threads_entry.delete(0, "end"); self.threads_entry.insert(0, d.get("th", "20"))
                self.mode_var.set(d.get("mode", "Single")); self.nested_var.set(d.get("nest", "None (Directly inside)"))

    def browse_source(self):
        p = filedialog.askdirectory()
        if p: self.source_entry.delete(0, "end"); self.source_entry.insert(0, p)
    def browse_output(self):
        p = filedialog.askdirectory()
        if p: self.output_entry.delete(0, "end"); self.output_entry.insert(0, p)
    def log(self, m):
        self.after(0, lambda: (self.log_box.configure(state="normal"), self.log_box.insert("end", f"{m}\n"), self.log_box.configure(state="disabled"), self.log_box.see("end")))
    def update_ui(self, t, v):
        self.after(0, lambda: (self.status_lbl.configure(text=t), self.progress.set(v)))
    def stop_processing(self):
        self.is_stopping = True
        self.stop_btn.configure(state="disabled")

    def get_creds(self):
        try:
            store = Storage(TOKEN_FILE)
            creds = store.get()
            if not creds or creds.invalid:
                flow = client.OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, SCOPES, user_agent=APPLICATION_NAME)
                creds = tools.run_flow(flow, store)
            self.credentials = creds
            return True
        except Exception as e:
            messagebox.showerror("Auth Error", str(e)); return False

    def start_processing_thread(self):
        self.save_settings(); self.is_stopping = False
        self.processing_thread = threading.Thread(target=self.run_ocr, daemon=True)
        self.processing_thread.start()
        self.start_btn.configure(state="disabled"); self.stop_btn.configure(state="normal")
        
    def run_ocr(self):
        try:
            if not self.get_creds(): return
            src, out = Path(self.source_entry.get()), Path(self.output_entry.get())
            if not src.is_dir() or not out.is_dir(): return
            if self.mode_var.get() == "Single":
                self.process_dir(src, out)
            else:
                for base in [d for d in src.iterdir() if d.is_dir()]:
                    if self.is_stopping: break
                    target = base if self.nested_var.get() == "None (Directly inside)" else base / self.nested_var.get()
                    if target.is_dir(): self.process_dir(target, out, srt_name=base.name)
            self.log("\n--- SESSION COMPLETED ---"); self.update_ui("", 0)
        except Exception as e: self.log(f"Critical Error: {e}")
        finally: self.start_btn.configure(state="normal"); self.stop_btn.configure(state="disabled")

    def process_dir(self, img_dir, out_dir, srt_name=None):
        out_file = out_dir / f'{srt_name or img_dir.name}.srt'
        raw_dir = Path.cwd() / 'raw_texts' / img_dir.name
        txt_dir = Path.cwd() / 'texts' / img_dir.name
        raw_dir.mkdir(parents=True, exist_ok=True); txt_dir.mkdir(parents=True, exist_ok=True)
        imgs = sorted(list(img_dir.glob('*.*')))
        if not imgs: return
        threads, results = [], {}
        max_th = int(self.threads_entry.get())
        for i, path in enumerate(imgs):
            if self.is_stopping: break
            t = threading.Thread(target=self.ocr_single, args=[path, i+1, raw_dir, txt_dir, results])
            threads.append(t); t.start()
            while sum(1 for th in threads if th.is_alive()) >= max_th:
                if self.is_stopping: break
                time.sleep(0.5)
            self.update_ui(f"Progress '{img_dir.name}': {i+1}/{len(imgs)}", (i+1)/len(imgs))
        for t in threads: t.join()
        if not self.is_stopping and results:
            with open(out_file, 'w', encoding='utf-8') as f:
                for ln in sorted(results.keys()): f.writelines(results[ln])

    def clean_text(self, t):
        lines = []
        for l in t.split('\n'):
            l = l.replace('\ufeff','').strip()
            if not l or re.fullmatch(r'[_\-—]+', l): continue
            lines.append(l)
        return '\n'.join(lines)

    def ocr_single(self, img_path, line, raw_dir, txt_dir, results):
        """Modified with Retry Logic for 500 Internal Errors"""
        if self.is_stopping: return
        max_retries = 3
        for attempt in range(max_retries):
            file_id = None
            try:
                http = self.credentials.authorize(httplib2.Http())
                service = discovery.build('drive', 'v3', http=http)
                raw_f, txt_f = raw_dir / f'{img_path.stem}.txt', txt_dir / f'{img_path.stem}.txt'
                
                # 1. Upload
                meta = {"name": img_path.name, "mimeType": 'application/vnd.google-apps.document'}
                if self.use_id_var.get() == "on" and self.folder_id_entry.get():
                    meta["parents"] = [self.folder_id_entry.get()]
                media = MediaFileUpload(str(img_path), mimetype='application/vnd.google-apps.document', resumable=True)
                res = service.files().create(body=meta, media_body=media).execute()
                file_id = res.get("id")

                # 2. Small wait for Google to finish OCR processing
                time.sleep(1)

                # 3. Export/Download
                downloader = MediaIoBaseDownload(io.FileIO(str(raw_f), "wb"), service.files().export_media(fileId=file_id, mimeType="text/plain"))
                done = False
                while not done: _, done = downloader.next_chunk()

                # 4. Clean and Save
                with open(raw_f, 'r', encoding='utf-8') as f: cleaned = self.clean_text(f.read())
                with open(txt_f, 'w', encoding='utf-8') as f: f.write(cleaned)
                
                # 5. Timestamp Parsing
                try:
                    parts = img_path.name.split('__')
                    s, e = parts[0].split('_'), parts[1].split('.')[0].split('_')
                    st, et = f"{s[0]}:{s[1]}:{s[2]},{s[3]}", f"{e[0]}:{e[1]}:{e[2]},{e[3]}"
                except: st, et = "00:00:00,000", "00:00:01,000"
                
                results[line] = [f'{line}\n', f'{st} --> {et}\n', f'{cleaned}\n\n']
                self.log(f"Done: {img_path.name} -> {cleaned[:30]}...")
                
                # Always Cleanup
                service.files().delete(fileId=file_id).execute()
                return # Success!

            except Exception as e:
                # If we have a file_id, try to delete it even if it failed
                if file_id:
                    try: service.files().delete(fileId=file_id).execute()
                    except: pass
                
                if attempt < max_retries - 1:
                    time.sleep(2) # Wait 2 seconds before retry
                    continue
                else:
                    self.log(f"Error on {img_path.name}: {e}")

if __name__ == '__main__':
    app = OcrApp()
    app.mainloop()
