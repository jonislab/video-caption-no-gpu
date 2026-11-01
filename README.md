# Whisper to DaVinci Resolve SRT Subtitle Generator

A Python script that uses OpenAI's **Whisper** model to transcribe video audio with word-level timestamps and automatically formats them into a clean `.srt` subtitle file optimized for DaVinci Resolve.

---

## Prerequisites & Installation

### Step 1: Install Python
Make sure you have Python (version 3.8 or higher) installed on your system. You can download it from [python.org](https://www.python.org/). Verify your installation by running:
```bash
python --version
```

### Step 2: Install Dependencies

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

Clone or download this repository, navigate to the project directory in your terminal, and install the required Python packages (including `openai-whisper`):
```bash
pip install -r requirements.txt
```

### Step 3: Install and Configure FFmpeg
This script relies on FFmpeg for media handling.
1. Download FFmpeg for Windows from [Gyan.dev FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/).
2. Extract the ZIP file.
3. Locate the **`bin`** folder (containing `ffmpeg.exe`) and copy its path.
4. Add it to your Windows System PATH:
  - Open Windows Search and type: **“Edit the system environment variables”**.
  - Click **Environment Variables**, select `Path` under System variables, and click **Edit**.
  - Click **New**, paste your FFmpeg `bin` path, and click **OK** to save.

---

## Usage

1. Open the script (`main.py`) and update the `file_path` and video filename in the `if __name__ == "__main__":` block:
   ```python
   if __name__ == "__main__":
       file_path = r"C:\path\to\your\videos\"
       generate_srt_from_whisper(
           video_path=file_path + "your_video.mp4",
           output_srt=file_path + "captions.srt",
           fps=30,
           lines_per_caption=2,
           words_per_line=4,
           max_chars_per_line=24,
       )
   ```
2. Run the script:
   ```bash
   python main.py
   ```
3. Import the generated `.srt` file into **DaVinci Resolve** via **File > Import > Subtitle...** or by dragging it directly into your Media Pool to populate your timeline's subtitle track!

---

## License
This project is licensed under the [MIT License](LICENSE).
