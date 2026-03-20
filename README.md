# Batch-Google-Docs-OCR
A multi-threaded GUI application for batch OCR using the Google Drive API. It processes image sequences from single or multiple folders, extracts text, and generates synchronized .srt subtitle files. Features include real-time progress logging, support for nested folder structures, and an automatic text-cleaning function to improve output quality.

### Based on Requirements

[Batch_VideoSubFinder](https://github.com/MrGamesKingPro/Batch_VideoSubFinder)


##Main Tool interface##

<img width="819" height="854" alt="Screenshot_2026-03-20_18-43-11" src="https://github.com/user-attachments/assets/a016ab08-dc62-4544-9541-c0de16bf08b5" />


### Key Features
*   **Zero-Config Setup:** No need to manually install libraries; the script handles dependencies on the first run.
*   **Built-in Credentials:** No `credentials.json` file is required (Client ID and Secret are integrated).
*   **Multi-Threaded:** Process up to 20+ images simultaneously for maximum speed.
*   **Smart Folder Management:** Supports single folders or complex multi-video directory structures.
*   **Auto-Cleaning:** Automatically deletes temporary files from Google Drive after processing.

---

### Requirements

1.  **Python 3.7+** installed on your system.
2.  **Internet Connection** (Required for Google Drive API and initial library installation).
3.  **Filenames with Timestamps:** For the SRT generation to work correctly, your images must follow this naming convention:  
    `HH_MM_SS_MS__HH_MM_SS_MS.png`  
    *(Example: `00_01_10_500__00_01_12_000.jpg`)*

---

### How to Use

#### 1. Initial Launch
1.  Place the script in a dedicated folder.
2.  Run the script via terminal or command prompt:
    ```sh
    python "Batch-Google-Docs-OCR.py"
    ```
3.  **Automatic Installation:** On the first run, the script will detect missing libraries (`customtkinter`, `google-api-python-client`, etc.) and install them automatically. Wait for the "All libraries installed successfully!" message.

#### 2. Google Authentication
1.  When you click **"Start Processing"** for the first time, your default web browser will open.
2.  Log in with your Google Account.
3.  You may see a "Google hasn't verified this app" warning (because the Client ID is for personal use). Click **"Advanced"** and then **"Go to Python OCR (unsafe)"** to proceed.
4.  Grant the requested permissions.
5.  A `token.json` file will be created in your folder. You won't need to log in again unless you delete this file.

#### 3. Configuring the GUI

*   **Mode Selection:**
    *   **Single Folder:** Use this if all your images are inside one folder.
    *   **Multi-Folder:** Use this if you have a main directory containing several subfolders (e.g., Video1, Video2), and you want a separate SRT for each.
*   **Subfolder Structure:**
    *   If your images are inside a specific sub-directory (like `RGBImages`), select that option from the dropdown menu.
*   **Paths:**
    *   **Source Folder:** Where your images are located.
    *   **Output Folder:** Where the final `.srt` files will be saved.
*   **Drive Folder ID (Highly Recommended):** 
    *   To keep your Google Drive clean, create an empty folder on Google Drive, copy its ID from the URL (the long string of letters and numbers), and paste it into the **Drive Folder ID** field.
*   **Threads:** 
    *   Default is **20**. If you have a very fast internet connection, you can increase this; if the app crashes or hits rate limits, decrease it.

#### 4. Execution
1.  Click **Start Processing**.
2.  The **Log Box** will show real-time updates for every image being uploaded, converted, and downloaded.
3.  Once finished, your SRT files will be ready in the Output Folder, and two local folders (`raw_texts` and `texts`) will contain the OCR transcriptions for your reference.

---

### Troubleshooting
*   **500 Internal Error:** The script has built-in retry logic. It will automatically attempt to re-process an image if Google’s server fails momentarily.
