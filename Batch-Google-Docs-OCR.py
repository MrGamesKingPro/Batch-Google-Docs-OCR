import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import io
import time
from pathlib import Path
import re # Added for text cleaning

# --- Google API & Authentication Imports ---
import httplib2
from apiclient import discovery
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
from oauth2client import client
from oauth2client.file import Storage
from oauth2client import tools

# --- Constants ---
# If modifying these scopes, delete your previously saved token.json.
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
APPLICATION_NAME = 'Python OCR with Drive API'


class OcrApp(ctk.CTk):
    """
    An advanced GUI application for performing OCR on image sequences using Google Drive API.
    It supports multiple folder structures and provides real-time feedback.
    """

    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("Batch Google Docs OCR By (MrGamesKingPro)")
        self.geometry("800x750")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Instance Variables ---
        self.credentials = None
        self.processing_thread = None

        # --- UI WIDGETS ---
        self.create_widgets()
        self.log("Welcome to the Advanced OCR Processor.\n")

        # --- Added Section: How to get credentials.json ---
        self.log("--- IMPORTANT: How to get 'credentials.json' ---")
        self.log("To use this application, you need API credentials from Google.")
        self.log("1. Go to the Google Cloud Console and create a new project.")
        self.log("2. Enable the 'Google Drive API' for your project.")
        self.log("3. Create credentials for an 'OAuth 2.0 Client ID' and select 'Desktop app'.")
        self.log("4. Download the client secret JSON file after creation.")
        self.log("5. Rename the downloaded file to 'credentials.json' and place it in the same folder as this application.\n")
        
        self.log("How to use:")
        self.log("1. Select your processing mode (Single or Multi-Folder).")
        self.log("2. If Multi-Folder, select the subfolder structure (RGBImages, TXTImages, or Directly inside).")
        self.log("3. Choose the source folder containing your images.")
        self.log("4. Choose the destination folder for the .srt subtitle files.")
        self.log("5. Optionally, provide a Google Drive Folder ID to upload temporary files to a specific folder.")
        self.log("6. Adjust thread count for performance.")
        self.log("7. Click 'Start Processing'.\n")
        self.log("Example - Single Folder Mode:")
        self.log("  - Source: C:/Videos/MyVideo_Frames/")
        self.log("  - Output: C:/Subtitles/")
        self.log("  - Result: C:/Subtitles/MyVideo_Frames.srt\n")
        self.log("Example - Multi-Folder Mode:")
        self.log("  - Source: C:/Videos/All_Videos_Frames/")
        self.log("  - All_Videos_Frames contains: Video1_Frames/, Video2_Frames/")
        self.log("  - Output: C:/Subtitles/")
        self.log("  - Result: C:/Subtitles/Video1_Frames.srt, C:/Subtitles/Video2_Frames.srt\n")
        self.log("Example - Multi-Folder with 'RGBImages' subfolder:")
        self.log("  - Source: C:/Videos/All_Videos_Frames/")
        self.log("  - All_Videos_Frames contains: Video1/, Video2/")
        self.log("  - Video1 contains: RGBImages/, Video2 contains: RGBImages/")
        self.log("  - Output: C:/Subtitles/")
        self.log("  - Result: C:/Subtitles/Video1.srt, C:/Subtitles/Video2.srt\n")

        # Scroll the log box to the top after the initial messages are displayed
        self.after(10, lambda: self.log_box.see("1.0"))


    def create_widgets(self):
        """Create and arrange all the GUI widgets."""
        # --- Settings Frame ---
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(settings_frame, text="Source Folder:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.source_entry = ctk.CTkEntry(settings_frame, placeholder_text="Path to image folder(s)")
        self.source_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(settings_frame, text="Browse...", command=self.browse_source).grid(row=0, column=2, padx=10, pady=5)

        ctk.CTkLabel(settings_frame, text="Output Folder:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.output_entry = ctk.CTkEntry(settings_frame, placeholder_text="Path to save .srt files")
        self.output_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(settings_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkLabel(settings_frame, text="Google Drive Folder ID:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.folder_id_entry = ctk.CTkEntry(settings_frame, placeholder_text="Optional: ID of a folder in your Google Drive")
        self.folder_id_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.use_folder_id_var = ctk.StringVar(value="on")
        self.use_folder_id_check = ctk.CTkCheckBox(settings_frame, text="Use ID", variable=self.use_folder_id_var, onvalue="on", offvalue="off")
        self.use_folder_id_check.grid(row=2, column=2, padx=10, pady=5)

        ctk.CTkLabel(settings_frame, text="Threads:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.threads_entry = ctk.CTkEntry(settings_frame)
        self.threads_entry.insert(0, "20")
        self.threads_entry.grid(row=3, column=1, padx=(10,0), pady=5, sticky="w")

        # --- Mode Selection Frame ---
        mode_frame = ctk.CTkFrame(self)
        mode_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        mode_frame.grid_columnconfigure((0,1,2), weight=1) # Adjusted column configure

        self.mode_var = ctk.StringVar(value="Multi-Folder")
        ctk.CTkRadioButton(mode_frame, text="Single Folder", variable=self.mode_var, value="Single").grid(row=0, column=0, padx=5, pady=10)
        ctk.CTkRadioButton(mode_frame, text="Multi-Folder", variable=self.mode_var, value="Multi-Folder").grid(row=0, column=1, padx=5, pady=10)
        
        # Nested menu now applies to Multi-Folder mode specifically, but is always visible
        self.nested_option_var = ctk.StringVar(value="None (Directly inside)") # Changed default value
        self.nested_menu = ctk.CTkOptionMenu(mode_frame, values=["RGBImages", "TXTImages", "None (Directly inside)"], variable=self.nested_option_var)
        self.nested_menu.grid(row=0, column=2, padx=5, pady=10) # Grid position adjusted

        # --- Execution Frame ---
        exec_frame = ctk.CTkFrame(self)
        exec_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        exec_frame.grid_columnconfigure(0, weight=1)

        self.start_button = ctk.CTkButton(exec_frame, text="Start Processing", command=self.start_processing_thread)
        self.start_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.status_label = ctk.CTkLabel(exec_frame, text="Status: Idle")
        self.status_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.progress_bar = ctk.CTkProgressBar(exec_frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # --- Log Frame ---
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_box = ctk.CTkTextbox(log_frame, state="disabled", text_color="#A9A9A9")
        self.log_box.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    # --- UI Callbacks ---
    def browse_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_entry.delete(0, "end")
            self.source_entry.insert(0, path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, path)

    def log(self, message):
        """Appends a message to the log box in a thread-safe way."""
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"{message}\n")
            self.log_box.configure(state="disabled")
            self.log_box.see("end")
        self.after(0, _append)

    def update_status(self, text, value):
        """Updates the status label and progress bar in a thread-safe way."""
        def _update():
            self.status_label.configure(text=f"Status: {text}")
            self.progress_bar.set(value)
        self.after(0, _update)

    def show_error(self, title, message):
        """Shows an error messagebox in a thread-safe way."""
        self.after(0, lambda: messagebox.showerror(title, message))

    # --- Core Logic ---
    def check_prerequisites(self):
        """Checks for necessary files and authentications before starting."""
        if not os.path.exists(CLIENT_SECRET_FILE):
            self.show_error("Missing File", f"Error: The credentials file '{CLIENT_SECRET_FILE}' was not found.")
            return False
        if not os.path.exists(TOKEN_FILE):
             self.show_error("Missing File", f"The token file '{TOKEN_FILE}' was not found. The application will attempt to create it by opening a browser window for authentication.")
        return True

    def get_gdrive_credentials(self):
        """
        Gets valid user credentials from storage or completes the OAuth2 flow.
        """
        try:
            store = Storage(TOKEN_FILE)
            credentials = store.get()
            if not credentials or credentials.invalid:
                self.log("Credentials not found or invalid, starting authentication flow...")
                flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
                flow.user_agent = APPLICATION_NAME
                # Use a console-based flow for initial authentication
                credentials = tools.run_flow(flow, store)
                self.log(f"Credentials stored to {TOKEN_FILE}")
            self.credentials = credentials
            return True
        except Exception as e:
            self.log(f"Authentication Error: {e}")
            self.show_error("Authentication Error", f"Could not get Google Drive credentials. Please ensure '{CLIENT_SECRET_FILE}' is correct. Error: {e}")
            return False

    def start_processing_thread(self):
        """Starts the OCR process in a background thread to keep the GUI responsive."""
        if self.processing_thread and self.processing_thread.is_alive():
            self.show_error("In Progress", "A process is already running.")
            return

        if not self.check_prerequisites():
            return
        
        self.processing_thread = threading.Thread(target=self.run_ocr_process, daemon=True)
        self.processing_thread.start()
        self.start_button.configure(state="disabled", text="Processing...")
        
    def run_ocr_process(self):
        """The main OCR logic that runs in the background."""
        try:
            if self.credentials is None:
                if not self.get_gdrive_credentials():
                    self.start_button.configure(state="normal", text="Start Processing") # Enable button on auth failure
                    return # Stop if authentication fails

            source_dir = Path(self.source_entry.get())
            output_dir = Path(self.output_entry.get())
            mode = self.mode_var.get()
            nested_subfolder_choice = self.nested_option_var.get()

            if not source_dir.is_dir() or not output_dir.is_dir():
                self.show_error("Invalid Path", "Source and Output paths must be valid directories.")
                return

            if mode == "Single":
                self.log(f"\n--- Starting Single Folder Process for '{source_dir.name}' ---")
                self.process_single_directory(source_dir, output_dir)
            elif mode == "Multi-Folder":
                self.log("\n--- Starting Multi-Folder Process ---")
                
                base_folders = [d for d in source_dir.iterdir() if d.is_dir()]
                if not base_folders:
                    self.log(f"No subfolders found in source directory '{source_dir}'. Please check your input or switch to Single Folder mode if processing '{source_dir}' directly.")
                    self.update_status("Idle", 0)
                    return

                for i, base_folder in enumerate(base_folders):
                    target_folder = None
                    srt_output_name = base_folder.name # SRT file name based on base folder

                    if nested_subfolder_choice == "None (Directly inside)":
                        target_folder = base_folder
                    else: # RGBImages or TXTImages
                        target_folder = base_folder / nested_subfolder_choice
                    
                    if target_folder and target_folder.is_dir():
                        self.log(f"\n--- Processing folder {i+1}/{len(base_folders)}: '{target_folder.name}' (SRT name: {srt_output_name}.srt) ---")
                        self.process_single_directory(target_folder, output_dir, srt_name=srt_output_name)
                    else:
                        self.log(f"Warning: Target folder '{target_folder}' not found within '{base_folder}'. Skipping.")

            self.log("\n--- All Processes Complete! ---")
            self.update_status("Idle", 0)

        except Exception as e:
            self.log(f"An unexpected error occurred: {e}")
            self.show_error("Error", f"An unexpected error occurred: {e}")
        finally:
            self.start_button.configure(state="normal", text="Start Processing")

    def process_single_directory(self, images_dir, output_srt_dir, srt_name=None):
        """Handles OCR for all images within a single directory."""
        self.update_status(f"Processing '{images_dir.name}'...", 0)
        
        srt_file_name = f'{srt_name or images_dir.name}.srt'
        output_file = output_srt_dir / srt_file_name

        # --- Create temporary directories without a parent 'temp_ocr_files' folder ---
        base_dir = Path.cwd()
        raw_texts_dir = base_dir / 'raw_texts' / images_dir.name
        texts_dir = base_dir / 'texts' / images_dir.name
        raw_texts_dir.mkdir(parents=True, exist_ok=True)
        texts_dir.mkdir(parents=True, exist_ok=True)

        images = sorted(list(images_dir.glob('*.*')))
        if not images:
            self.log(f"No images found in '{images_dir}'. Skipping.")
            return

        threads = []
        srt_file_list = {} # Local dictionary to prevent race conditions
        max_threads = int(self.threads_entry.get())
        
        for idx, image_path in enumerate(images):
            line_num = idx + 1
            t = threading.Thread(
                target=self.ocr_single_image,
                args=[image_path, line_num, raw_texts_dir, texts_dir, srt_file_list]
            )
            threads.append(t)
            t.start()
            
            # Throttle thread creation and wait for some to finish
            time.sleep(0.1) # Small delay to avoid overwhelming the API
            while sum(1 for th in threads if th.is_alive()) >= max_threads:
                time.sleep(0.5)

        # Wait for all threads for this folder to complete
        total_images = len(images)
        while True:
            alive_threads = sum(1 for t in threads if t.is_alive())
            completed_threads = total_images - alive_threads
            progress = completed_threads / total_images if total_images > 0 else 1
            self.update_status(f"Processing '{images_dir.name}': {completed_threads}/{total_images}", progress)
            if alive_threads == 0:
                break
            time.sleep(1)

        # Write the final SRT file
        if srt_file_list:
            with open(output_file, 'w', encoding='utf-8') as out:
                for line_number in sorted(srt_file_list.keys()):
                    out.writelines(srt_file_list[line_number])
            self.log(f"Successfully created subtitle file: {output_file}")
        else:
            self.log(f"Warning: No text was extracted for '{images_dir.name}'. SRT file not created.")

    def clean_ocr_text(self, text_content):
        """
        Cleans the OCR extracted text by removing common artifacts and empty lines.
        Specifically targets patterns like '﻿________________' and purely non-alphanumeric lines.
        """
        cleaned_lines = []
        lines = text_content.split('\n')

        for line in lines:
            # Remove Zero Width No-Break Space (U+FEFF)
            line = line.replace('\ufeff', '')
            
            stripped_line = line.strip()

            # Skip empty lines
            if not stripped_line:
                continue

            # Skip lines that are just sequences of underscores, hyphens, or similar long dashes
            # This regex matches lines that consist solely of 1 or more underscore, hyphen, or em-dash characters.
            if re.fullmatch(r'[_\-—]+', stripped_line):
                continue
            
            # Add more specific cleaning rules if other patterns emerge.

            cleaned_lines.append(stripped_line)
        
        return '\n'.join(cleaned_lines)

    def ocr_single_image(self, image_path, line, raw_texts_dir, texts_dir, srt_file_list):
        """Performs OCR on one image using Google Drive API."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Re-authorize for each thread to ensure thread safety
                http = self.credentials.authorize(httplib2.Http())
                service = discovery.build('drive', 'v3', http=http)

                imgname = image_path.name
                raw_txtfile = raw_texts_dir / f'{image_path.stem}.txt'
                txtfile = texts_dir / f'{image_path.stem}.txt'

                # --- Create API request body ---
                mime = 'application/vnd.google-apps.document'
                file_metadata = {"name": imgname, "mimeType": mime}
                if self.use_folder_id_var.get() == "on" and self.folder_id_entry.get():
                    file_metadata["parents"] = [self.folder_id_entry.get()]

                media = MediaFileUpload(str(image_path), mimetype=mime, resumable=True)
                
                # Upload and convert
                res = service.files().create(body=file_metadata, media_body=media).execute()

                # Download the converted text
                downloader = MediaIoBaseDownload(
                    io.FileIO(str(raw_txtfile), "wb"),
                    service.files().export_media(fileId=res["id"], mimeType="text/plain"),
                )
                done = False
                while not done:
                    _, done = downloader.next_chunk()

                # Delete the temporary file from Google Drive
                service.files().delete(fileId=res["id"]).execute()
            
                # Clean the extracted text and create the SRT entry
                with open(raw_txtfile, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                # Apply the cleaning function
                cleaned_text = self.clean_ocr_text(text_content)

                # --- ADDED: Save the cleaned text to the 'texts' directory as requested ---
                with open(txtfile, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)

                # Parse filename for timestamps (assuming format: HH_MM_SS_mmm__HH_MM_SS_mmm.jpg)
                try:
                    parts = imgname.split('__')
                    start_parts = parts[0].split('_')
                    end_parts = parts[1].split('.')[0].split('_')
                    
                    start_time = f"{start_parts[0]}:{start_parts[1]}:{start_parts[2]},{start_parts[3]}"
                    end_time = f"{end_parts[0]}:{end_parts[1]}:{end_parts[2]},{end_parts[3]}"
                except IndexError:
                    self.log(f"Warning: Could not parse timestamp from '{imgname}'. Using placeholders.")
                    start_time = "00:00:00,000"
                    end_time = "00:00:01,000"

                # Store the result in the shared dictionary (access should be safe due to unique keys)
                srt_file_list[line] = [
                    f'{line}\n',
                    f'{start_time} --> {end_time}\n',
                    f'{cleaned_text}\n\n',
                ]
                
                # self.log(f"'{imgname}' -> Done.")
                return # Success, exit the retry loop

            except Exception as e:
                self.log(f"Error processing '{image_path.name}' (Attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep((attempt + 1) * 2) # Exponential backoff

        self.log(f"Failed to process '{image_path.name}' after {max_retries} attempts.")


if __name__ == '__main__':
    app = OcrApp()
    app.mainloop()
