# DaVinci Resolve AI Caption Automation (No-Render Edition v2)

Automate speech-to-text transcription using **OpenAI Whisper**, generate word-timed subtitle chunks, and assemble styled **Fusion Text+** caption clips directly onto your **DaVinci Resolve timeline**—all without triggering background video rendering.



## ✨ Features

- **🎙️ Automatic Whisper Transcription**: Transcribes video audio streams with word-level timestamps using any OpenAI Whisper model size (`tiny`, `base`, `small`, `medium`, `large`).
- **🧩 Smart Subtitle Chunking**: Custom word-wrapping algorithm enforcing strict parameters:
  - Maximum words per line (`words_per_line`)
  - Maximum characters per line (`max_chars_per_line`)
  - Maximum lines per title card (`lines_per_caption`)
  - Natural sentence breaks on punctuation (`.`, `?`, `!`) and speech silence gaps.
- **🎨 Fusion Template Integration**: Replaces standard flat subtitle tracks with rich animated Fusion Title templates (e.g., `TFx-Caption`) placed on **Video Track 3**. Automatically finds and injects text into the `TextPlus` or `Template` node's `StyledText` parameter.
- **⏱️ Comprehensive Sub-Stage Timers**: Tracks and logs exact runtimes for:
  - Step 1: Whisper Audio Transcription
  - Step 4: Track 3 Placement & Fusion Comp Text Updates
  - Full End-to-End Execution Time (from script startup to exit).
- **🛡️ Multi-Level Resolve Connection**: Robust connector that resolves:
  1. Internal global `resolve` object (when run from inside Resolve).
  2. Standard external `DaVinciResolveScript` module.
  3. Windows dynamic DLL fallback (`fusionscript.dll`).
- **📂 Offline & Fallback SRT Support**: If Whisper or PyTorch is unavailable, the script seamlessly detects and reads pre-existing `.srt` files on disk without failing.
- **🖥️ Safe Interactive Exit**: Detects interactive TTY sessions (`sys.stdin.isatty()`) to prevent the terminal window from abruptly closing on Windows when double-clicked.

---

## 📋 Prerequisites

### 1. DaVinci Resolve Studio or FREE version
* **DaVinci Resolve Studio  21+** (External Python scripting requires the Studio edition).
* Navigate to **DaVinci Resolve > Preferences > System > General** and ensure **External scripting using** is set to **Local** or **Network**.

### 2. Python Environment (64-bit Python 3.8 – 3.12)
Install the required dependencies:
```bash
pip install openai-whisper torch
```
*(Optional: For GPU acceleration on Windows, ensure CUDA-enabled PyTorch is installed).*

### 3. Media Pool Template
Ensure your target Fusion title template (default: **`TFx-Caption`**) is loaded inside your DaVinci Resolve **Media Pool** (in the root `Master` bin or any subfolder).

---

## ⚙️ Configuration & Script Parameters

Open `davinci_caption_automation_norender_v2.py` and modify the execution block at the bottom of the script:

```python
if __name__ == "__main__":
    file_path = r"<YOUR PATH TO VIDEO>"
    video_file = os.path.join(file_path, "<YOUR DRAFT VIDEO.mp4")
    srt_file = os.path.join(file_path, "captions.srt")

    run_caption_workflow_norender(
        video_path=video_file,          # Path to source video file
        output_srt=srt_file,            # Path for exported/fallback SRT
        template_name="TFx-Caption",    # Template clip name in Media Pool
        fps=30,                         # Target frame rate fallback
        model_size="base",              # Whisper model: tiny, base, small, medium, large
        lines_per_caption=2,            # 1 for single-line, 2 for dual-line
        words_per_line=4,               # Target word count per line
        max_chars_per_line=24,          # Character limit per line before wrapping
    )
```

### Parameter Reference

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `video_path` | `str` | *(Required)* | Full path to the `.mp4` or `.mov` source video. |
| `output_srt` | `str` | `None` | Path where generated SRT is saved. Defaults to `<video_name>.srt`. |
| `template_name` | `str` | `"TFx-Caption"` | Name of the Fusion Title template in your Media Pool. |
| `fps` | `float/int` | `30` | Fallback frame rate if timeline settings cannot be queried. |
| `model_size` | `str` | `"base"` | OpenAI Whisper model size. |
| `words_per_line` | `int` | `4` | Maximum words allowed per caption line. |
| `max_chars_per_line`| `int` | `24` | Maximum character length allowed before triggering a wrap. |
| `lines_per_caption` | `int` | `2` | Number of visible lines per subtitle card. |

---

## 🚀 How to Run

1. Launch **DaVinci Resolve Studio** and open your project.
2. Run the script from your terminal:
   ```bash
   python davinci_caption_automation_norender_v2.py
   ```
3. Watch the console diagnostics as Resolve automatically:
   - Transcribes the audio via Whisper.
   - Creates a new timeline named `<video_name>_Subtitled`.
   - Populates the title template across Video Track 3.
   - Saves your project.

---

## 🖥️ Console Output Example

```text
==================================================
  [STARTUP] DaVinci Caption Automation (No Render)
==================================================
Start Time        : 2026-11-22 19:00:00
Python Executable : C:\Python311\python.exe
Python Version    : 3.11.8
Current Directory : D:\Projects\Captions
--------------------------------------------------

[1/4] Checking PyTorch & Whisper library availability...
  ✅ OpenAI Whisper library is imported successfully.

--- STEP 1: WHISPER TRANSCRIPTION ---
🎙️ Loading Whisper Model ('base')...
Transcribing audio with word-level timestamps...
✅ Exported SRT successfully to: 'D:\Projects\Captions\clip1.srt'
⏱️ Step 1 Duration (Whisper Audio Transcription): 14.82s (0m 14.8s)

--- STEP 2: CONNECTING TO DAVINCI RESOLVE API ---
✅ Connected via dynamic DLL load of fusionscript.dll
Connected to Active Project: 'Demo_Project'

--- STEP 3: MEDIA POOL & TIMELINE SETUP ---
✅ Found existing clip in Media Pool: 'clip1.mp4'
Activated Timeline: 'clip1_Subtitled'
Active Timeline FPS: 30.0
Found Template Clip: 'TFx-Caption'

--- STEP 4: PLACING CAPTIONS ON TRACK 3 ---
Populating 48 text clips onto Video Track 3...
✅ Appended & Updated 48/48 clips on Video Track 3!
⏱️ Step 4 Duration (Track 3 Placement & Fusion Text Update): 3.41s
💾 Project successfully saved.

==================================================
 🎉 CAPTION CREATION COMPLETE (RENDER SKIPPED)    
   Project              : 'Demo_Project'
   Timeline             : 'clip1_Subtitled'
   Captions Placed      : 48 clips on Video Track 3
   🎙️ Whisper Duration  : 14.82s (0m 14.8s)
   🧩 Placement Duration: 3.41s
   ⏳ Workflow Duration : 18.23s (0m 18.2s)
==================================================

==================================================
  🏁 EXECUTION FINISHED
  ⏱️ TOTAL TIME (START TO FINISH): 19.05s (0m 19.1s)
==================================================
```

---

## 🛠️ Troubleshooting

* **`fusionscript.dll loaded, but scriptapp('Resolve') returned None`**:
  * Make sure DaVinci Resolve Studio is open and finished loading before running the script.
  * Check **Preferences > System > General** to confirm external scripting is enabled.
* **`Title template 'TFx-Caption' not found in Media Pool`**:
  * Ensure the exact template name matches what is shown in your Media Pool bins.
* **Whisper Runs Slowly on CPU**:
  * Install PyTorch with CUDA support:
    ```bash
    pip install torch --index-url https://download.pytorch.org/whl/cu121
    ```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
