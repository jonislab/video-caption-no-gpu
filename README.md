# video-caption-no-gpu
Create a video caption and import in Davinci Resolve
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### Step 3: Install and Configure FFmpeg
This script relies on FFmpeg for media handling.
1. Download FFmpeg for Windows from [Gyan.dev FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/).
2. Extract the ZIP file.
3. Locate the **`bin`** folder (containing `ffmpeg.exe`) and copy its path.
4. Add it to your Windows System PATH:
   * Open Windows Search and type: **“Edit the system environment variables”**.
   * Click **Environment Variables**, select `Path` under System variables, and click **Edit**.
   * Click **New**, paste your FFmpeg `bin` path, and click **OK** to save.

---

## Usage

1. Open the script (`main.py` or your script file) and update the `file_path` and video filename in the `if __name__ == "__main__":` block:
   ```python
   if __name__ == "__main__":
       file_path = r"C:\path\to\your\videos\"
       generate_fcpxml_from_whisper(
           video_path=file_path + "your_video.mp4",
           output_xml=file_path + "captions.fcpxml",
           output_txt=file_path + "captions.txt",
           template_name="JX3DCaption",
           fps=30,
           width=1080,
           height=1920,
           lines_per_caption=2,
           words_per_line=4,
           max_chars_per_line=24,
       )
   ```
2. Run the script:
   ```bash
   python main.py
   ```
3. Import the generated `.fcpxml` file into **DaVinci Resolve** to populate your timeline with perfectly timed captions!

---

## License
This project is licensed under the [MIT License](LICENSE).
