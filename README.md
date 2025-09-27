# Batch-Google-Docs-OCR
A multi-threaded GUI application for batch OCR using the Google Drive API. It processes image sequences from single or multiple folders, extracts text, and generates synchronized .srt subtitle files. Features include real-time progress logging, support for nested folder structures, and an automatic text-cleaning function to improve output quality.

### Based on Requirements

[Batch_VideoSubFinder](https://github.com/MrGamesKingPro/Batch_VideoSubFinder)

### Requirements

1.  **Python 3.7+**
2.  **Google Cloud Project** with the Google Drive API enabled.
3.  The following Python libraries, which can be installed via pip:

```sh
pip install customtkinter
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install oauth2client
```

### How to Use

#### 1. Google API Setup (Crucial First Step)

This application requires API credentials to communicate with your Google Drive.

1.  **Create a Project:** Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2.  **Enable Drive API:** In your project's dashboard, go to "APIs & Services" -> "Library", search for "Google Drive API", and enable it.
3.  **Create Credentials:**
    *   Go to "APIs & Services" -> "Credentials".
    *   Click "Create Credentials" and select "OAuth 2.0 Client ID".
    *   If prompted, configure the "OAuth consent screen". Select "External" and provide a name for the app (e.g., "Python OCR App"). Fill in the user support email and developer contact information. You can skip the rest of the optional scopes and test user sections.
    *   For the "Application type", select **"Desktop app"**.
    *   Give the client ID a name and click "Create".
4.  **Download Credentials:** A popup will appear showing your Client ID and Secret. Click **"DOWNLOAD JSON"**.
5.  **Rename the File:** Rename the downloaded file to **`credentials.json`** and place it in the **exact same directory** as the Python script.

#### 2. Running the Application

1.  **Install Libraries:** Open a terminal or command prompt and run:
    ```sh
pip install customtkinter
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install oauth2client
    ```
2.  **Launch the Script:** Run the Python script from your terminal:
    ```sh
    python Batch-Google-Docs-OCR.py
    ```
3.  **First-Time Authentication:** On the first run, a browser window will open asking you to authorize the application to access your Google Drive. Grant the necessary permissions. This will create a `token.json` file in the same directory, which stores your authorization for future use.

#### 3. Using the GUI

1.  **Processing Mode:**
    *   **Single Folder:** Choose this if you want to process all images located directly inside the selected "Source Folder".
    *   **Multi-Folder:** Choose this if the "Source Folder" contains multiple subfolders, each representing a separate image sequence.

2.  **Subfolder Structure (for Multi-Folder Mode):**
    *   `None (Directly inside)`: Select this if the images are directly inside each subfolder (e.g., `Source/Video1_Frames/`, `Source/Video2_Frames/`).
    *   `RGBImages` or `TXTImages`: Select this if the images are nested one level deeper (e.g., `Source/Video1/RGBImages/`, `Source/Video2/RGBImages/`).

3.  **Choose Folders:**
    *   **Source Folder:** Click "Browse..." to select the folder containing your images or subfolders of images.
    *   **Output Folder:** Click "Browse..." to select the destination folder where the final `.srt` subtitle files will be saved.

4.  **Configure Settings:**
    *   **Google Drive Folder ID (Optional):** You can provide a specific Google Drive folder ID. This will cause all temporary OCR files to be uploaded to that folder instead of your Drive's root directory, keeping it clean.
    *   **Threads:** Adjust the number of concurrent threads. A higher number can improve performance but may be limited by your internet connection and API rate limits. The default is 20.

5.  **Start Processing:** Click the **"Start Processing"** button. The application will begin processing, and you can monitor its progress in the log window and with the progress bar.
