#!/usr/bin/env python3
"""
DaVinci Resolve Caption Automation Script (No-Render Edition v2)
===============================================================
Based on davinci_caption_automation_v14.py / davinci_caption_automation_norender.py

Key Enhancements in v2:
- Added comprehensive execution timer logging:
  * Measures total elapsed time from script start to completion.
  * Tracks sub-stage durations (Whisper transcription & Track 3 placement).
  * Formats elapsed duration cleanly in seconds and minutes (e.g. 45.20s / 0.75 min).
- Keeps the no-render workflow intact (no background render queue triggered).
"""

import os
import sys
import re
import time
import datetime
import traceback
import xml.etree.ElementTree as ET

# Overall execution start timestamp
SCRIPT_START_TIME = time.time()

# Immediate stdout notification
print("==================================================", flush=True)
print("  [STARTUP] DaVinci Caption Automation (No Render)", flush=True)
print("==================================================", flush=True)
print(f"Start Time        : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
print(f"Python Executable : {sys.executable}", flush=True)
print(f"Python Version    : {sys.version.split()[0]}", flush=True)
print(f"Current Directory : {os.getcwd()}", flush=True)
print("--------------------------------------------------\n", flush=True)

# Safe Import for Whisper
print("[1/4] Checking PyTorch & Whisper library availability...", flush=True)
WHISPER_AVAILABLE = False
try:
    import whisper
    WHISPER_AVAILABLE = True
    print("  ✅ OpenAI Whisper library is imported successfully.", flush=True)
except ImportError:
    print("  ⚠️ OpenAI Whisper library is NOT installed in this Python environment.", flush=True)
    print("     To install: pip install openai-whisper torch", flush=True)
except Exception as e:
    print(f"  ⚠️ Warning: Failed to import Whisper ({e})", flush=True)


def format_duration(seconds):
    """Formats seconds into readable string with minutes and seconds."""
    mins = int(seconds // 60)
    secs = seconds % 60
    if mins > 0:
        return f"{seconds:.2f}s ({mins}m {secs:.1f}s)"
    return f"{seconds:.2f}s"


def run_environment_diagnostics(video_path, output_srt, template_name):
    """Prints a detailed audit of system environment and target files."""
    print("\n--- SYSTEM & ENVIRONMENT DIAGNOSTICS ---", flush=True)
    print(f"Platform           : {sys.platform}", flush=True)
    print(f"RESOLVE_SCRIPT_API : {os.getenv('RESOLVE_SCRIPT_API', 'Not Set')}", flush=True)
    print(f"RESOLVE_SCRIPT_LIB : {os.getenv('RESOLVE_SCRIPT_LIB', 'Not Set')}", flush=True)
    print(f"PYTHONPATH         : {os.getenv('PYTHONPATH', 'Not Set')}", flush=True)

    norm_video = os.path.normpath(os.path.abspath(video_path))
    norm_srt = os.path.normpath(os.path.abspath(output_srt))

    print(f"\n--- TARGET FILES AUDIT ---", flush=True)
    print(f"Target Video Path  : {norm_video}", flush=True)
    if os.path.exists(norm_video):
        try:
            size_mb = os.path.getsize(norm_video) / (1024 * 1024)
            print(f"  ✅ Video Status   : EXISTS ({size_mb:.2f} MB)", flush=True)
        except Exception as e:
            print(f"  ⚠️ Video Status   : EXISTS (Size check failed: {e})", flush=True)
    else:
        print(f"  ❌ Video Status   : DOES NOT EXIST ON DISK!", flush=True)
        print("     Please check drive letter, path spelling, and folder structure.", flush=True)

    print(f"Target SRT Path    : {norm_srt}", flush=True)
    if os.path.exists(norm_srt):
        print(f"  ℹ️ SRT Status     : EXISTS (Will serve as fallback or overwrite)", flush=True)
    else:
        print(f"  ℹ️ SRT Status     : DOES NOT EXIST YET (Will be generated)", flush=True)

    print(f"Title Template Name: '{template_name}'", flush=True)
    print("-----------------------------------------\n", flush=True)


def extract_word_chunks(
    result,
    fps=30.0,
    lines_per_caption=2,
    words_per_line=4,
    max_chars_per_line=24,
):
    """Splits Whisper word-level timestamps into formatted subtitle chunks."""
    all_words = []
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            word_str = w.get("word", "").strip()
            if word_str:
                all_words.append({
                    "word": word_str,
                    "start": w.get("start", 0.0),
                    "end": w.get("end", 0.0)
                })

    if not all_words:
        return []

    max_silence_gap = 8.0 / float(fps)
    chunks = []
    current_chunk_words = []

    def finalize_chunk(words_list):
        if not words_list:
            return
        start_time = words_list[0]["start"]
        end_time = words_list[-1]["end"]

        lines = []
        cur_line = []
        cur_char_count = 0

        for w_item in words_list:
            w_text = w_item["word"]
            test_char_count = cur_char_count + (1 if cur_line else 0) + len(w_text)

            if len(cur_line) >= words_per_line or test_char_count > max_chars_per_line:
                if cur_line:
                    lines.append(" ".join(cur_line))
                    cur_line = [w_text]
                    cur_char_count = len(w_text)
                else:
                    lines.append(w_text)
                    cur_line = []
                    cur_char_count = 0
            else:
                cur_line.append(w_text)
                cur_char_count = test_char_count

            if w_text[-1] in ".?!":
                if cur_line:
                    lines.append(" ".join(cur_line))
                    cur_line = []
                    cur_char_count = 0

        if cur_line:
            lines.append(" ".join(cur_line))

        if len(lines) > lines_per_caption:
            top_lines = lines[:lines_per_caption - 1]
            remaining = " ".join(lines[lines_per_caption - 1:])
            lines = top_lines + [remaining]

        full_text = "\n".join(lines)
        chunks.append({
            "start": start_time,
            "end": end_time,
            "text": full_text
        })

    prev_word = None
    for w_item in all_words:
        if prev_word is not None:
            gap = w_item["start"] - prev_word["end"]
            is_silence_gap = gap > max_silence_gap
            is_chunk_full = len(current_chunk_words) >= (lines_per_caption * words_per_line)
            is_punct_break = prev_word["word"][-1] in ".?!"

            if is_silence_gap or is_chunk_full or is_punct_break:
                finalize_chunk(current_chunk_words)
                current_chunk_words = []

        current_chunk_words.append(w_item)
        prev_word = w_item

    if current_chunk_words:
        finalize_chunk(current_chunk_words)

    return chunks


def export_chunks_to_srt(chunks, output_srt):
    """Exports chunk dictionaries to an SRT file."""
    def seconds_to_srt_timecode(seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        if millis >= 1000:
            secs += 1
            millis = 0
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    out_dir = os.path.dirname(os.path.abspath(output_srt))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_srt, "w", encoding="utf-8") as f:
        for idx, chunk in enumerate(chunks, start=1):
            start_tc = seconds_to_srt_timecode(chunk["start"])
            end_tc = seconds_to_srt_timecode(chunk["end"])
            f.write(f"{idx}\n")
            f.write(f"{start_tc} --> {end_tc}\n")
            f.write(f"{chunk['text']}\n\n")

    print(f"✅ Exported SRT successfully to: '{output_srt}'", flush=True)


def generate_srt_from_whisper(
    video_path,
    output_srt="captions.srt",
    fps=30,
    model_size="base",
    lines_per_caption=2,
    words_per_line=4,
    max_chars_per_line=24,
):
    """Transcribes audio using OpenAI Whisper and exports formatted SRT file."""
    print(f"\n--- STEP 1: WHISPER TRANSCRIPTION ---", flush=True)
    if not os.path.exists(video_path):
        print(f"❌ ERROR: Input video file does NOT exist on disk:\n   '{video_path}'", flush=True)
        return False

    if not WHISPER_AVAILABLE:
        print("⚠️ Whisper library not available in Python environment.", flush=True)
        if os.path.exists(output_srt):
            print(f"ℹ️ Found pre-existing fallback SRT file at '{output_srt}'. Skipping Whisper transcription.", flush=True)
            return True
        else:
            print("❌ Cannot transcribe video because Whisper is not installed and no fallback SRT exists.", flush=True)
            return False

    print(f"🎙️ Loading Whisper Model ('{model_size}')...", flush=True)
    try:
        model = whisper.load_model(model_size)
        print("Transcribing audio with word-level timestamps...", flush=True)
        result = model.transcribe(video_path, word_timestamps=True)
    except Exception as e:
        print(f"❌ Error during Whisper transcription: {e}", flush=True)
        traceback.print_exc()
        return False

    chunks = extract_word_chunks(
        result,
        fps=fps,
        lines_per_caption=lines_per_caption,
        words_per_line=words_per_line,
        max_chars_per_line=max_chars_per_line,
    )

    if not chunks:
        print("⚠️ Warning: No speech detected in video audio stream.", flush=True)
        return False

    export_chunks_to_srt(chunks, output_srt)
    return True


def get_resolve_object():
    """Connects to running DaVinci Resolve instance or returns active global."""
    print("\n--- STEP 2: CONNECTING TO DAVINCI RESOLVE API ---", flush=True)

    # 1. Check if running inside Resolve (menu script / console)
    res = globals().get("resolve")
    if res is not None and hasattr(res, "GetProjectManager"):
        print("✅ Connected via internal global 'resolve' object", flush=True)
        return res

    # 2. Check standard external import
    try:
        import DaVinciResolveScript as dvr_script
        res = dvr_script.scriptapp("Resolve")
        if res:
            print("✅ Connected via 'import DaVinciResolveScript'", flush=True)
            return res
    except ImportError:
        print("  ℹ️ 'DaVinciResolveScript' module not found in standard sys.path. Trying DLL loader...", flush=True)

    # 3. Dynamic Windows DLL loader fallback
    if os.name == "win32":
        path_lib = os.getenv(
            "RESOLVE_SCRIPT_LIB",
            r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
        )
        print(f"  Checking DLL path: '{path_lib}'...", flush=True)
        if os.path.exists(path_lib):
            try:
                import imp
                s_module = imp.load_dynamic("fusionscript", path_lib)
                res = s_module.scriptapp("Resolve")
                if res:
                    print("✅ Connected via dynamic DLL load of fusionscript.dll", flush=True)
                    return res
                else:
                    print("❌ fusionscript.dll loaded, but scriptapp('Resolve') returned None.", flush=True)
            except Exception as e:
                print(f"❌ Error during dynamic DLL load: {e}", flush=True)
        else:
            print(f"❌ fusionscript.dll not found at '{path_lib}'", flush=True)

    return None


def find_clip_recursive(folder, target_name):
    """Recursively searches Media Pool folders for a clip matching target_name."""
    clips = folder.GetClipList() or []
    for clip in clips:
        if clip.GetName() == target_name or os.path.splitext(clip.GetName())[0] == target_name:
            return clip

    subfolders = folder.GetSubFolderList() or []
    for sf in subfolders:
        found = find_clip_recursive(sf, target_name)
        if found:
            return found
    return None


def parse_srt(srt_path, fps=30.0):
    """Parses an SRT file into a list of timing and text dictionaries."""
    def timecode_to_frames(tc_str, fps_val):
        tc_clean = tc_str.strip().replace(',', '.')
        parts = tc_clean.split(':')
        h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
        total_seconds = h * 3600 + m * 60 + s
        return int(round(total_seconds * fps_val))

    subtitles = []
    if not os.path.exists(srt_path):
        print(f"[SRT] Error: File not found at '{srt_path}'", flush=True)
        return subtitles

    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    entries = re.split(r'\n\s*\n', content)
    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) >= 3 and '-->' in lines[1]:
            time_parts = lines[1].split('-->')
            start_tc = time_parts[0]
            end_tc = time_parts[1]
            start_frame = timecode_to_frames(start_tc, fps)
            end_frame = timecode_to_frames(end_tc, fps)
            duration = max(1, end_frame - start_frame)
            raw_text = " ".join(lines[2:])
            subtitles.append({
                "start_frame": start_frame,
                "end_frame": end_frame,
                "duration_frames": duration,
                "text": raw_text
            })
    return subtitles


def format_caption_text(text, words_per_line=4, max_chars_per_line=24, lines_per_caption=2):
    """Ensures long subtitle text adheres to multi-line wrapping rules."""
    words = text.split()
    if not words:
        return ""

    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        if len(current_line) >= words_per_line or len(test_line) > max_chars_per_line:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
        else:
            current_line.append(word)

    if current_line:
        lines.append(" ".join(current_line))

    if len(lines) > lines_per_caption:
        top_lines = lines[:lines_per_caption - 1]
        remaining = " ".join(lines[lines_per_caption - 1:])
        lines = top_lines + [remaining]

    return "\n".join(lines)


def import_video_with_fallbacks(resolve, media_pool, root_folder, video_path):
    """Imports or locates video clip in Media Pool."""
    norm_path = os.path.normpath(os.path.abspath(video_path))
    filename = os.path.basename(norm_path)
    name_no_ext = os.path.splitext(filename)[0]

    if not os.path.exists(norm_path):
        print(f"❌ Error: Video file does not exist on disk at path: {norm_path}", flush=True)
        return None

    existing_clip = find_clip_recursive(root_folder, filename) or find_clip_recursive(root_folder, name_no_ext)
    if existing_clip:
        print(f"✅ Found existing clip in Media Pool: '{existing_clip.GetName()}'", flush=True)
        return existing_clip

    try:
        imported = media_pool.ImportMedia([{"FilePath": norm_path}])
        if imported and len(imported) > 0:
            print(f"✅ Successfully imported via ImportMedia(dict): '{imported[0].GetName()}'", flush=True)
            return imported[0]
    except Exception:
        pass

    try:
        imported = media_pool.ImportMedia([norm_path])
        if imported and len(imported) > 0:
            print(f"✅ Successfully imported via ImportMedia(string): '{imported[0].GetName()}'", flush=True)
            return imported[0]
    except Exception:
        pass

    try:
        media_storage = resolve.GetMediaStorage()
        if media_storage:
            imported = media_storage.AddItemListToMediaPool([norm_path])
            if imported and len(imported) > 0:
                clip_obj = imported[0] if isinstance(imported, list) else list(imported.values())[0]
                print(f"✅ Successfully imported via MediaStorage: '{clip_obj.GetName()}'", flush=True)
                return clip_obj
    except Exception:
        pass

    return find_clip_recursive(root_folder, filename) or find_clip_recursive(root_folder, name_no_ext)


def run_caption_workflow_norender(
    video_path,
    output_srt=None,
    template_name="TFx-Caption2",
    fps=30,
    model_size="base",
    words_per_line=4,
    max_chars_per_line=24,
    lines_per_caption=2
):
    """
    Automates complete subtitle generation and timeline placement WITHOUT rendering,
    logging detailed elapsed timings for each stage and total execution.
    """
    workflow_start_time = time.time()

    clean_video_path = os.path.normpath(os.path.abspath(video_path))
    target_dir = os.path.dirname(clean_video_path)
    base_name = os.path.splitext(os.path.basename(clean_video_path))[0]

    if not output_srt:
        output_srt = os.path.join(target_dir, f"{base_name}.srt")
    else:
        output_srt = os.path.normpath(os.path.abspath(output_srt))

    run_environment_diagnostics(clean_video_path, output_srt, template_name)

    # 1. Step A: Generate SRT via Whisper
    t_whisper_start = time.time()
    srt_created = generate_srt_from_whisper(
        video_path=clean_video_path,
        output_srt=output_srt,
        fps=fps,
        model_size=model_size,
        lines_per_caption=lines_per_caption,
        words_per_line=words_per_line,
        max_chars_per_line=max_chars_per_line
    )
    t_whisper_elapsed = time.time() - t_whisper_start
    print(f"⏱️ Step 1 Duration (Whisper Audio Transcription): {format_duration(t_whisper_elapsed)}", flush=True)

    if not srt_created and not os.path.exists(output_srt):
        print("\n❌ CRITICAL: SRT file could not be created and no fallback SRT exists.", flush=True)
        print("   Aborting workflow.", flush=True)
        return False

    # 2. Step B: Connect to Resolve
    resolve = get_resolve_object()
    if not resolve:
        print("❌ Error: Could not connect to DaVinci Resolve instance.", flush=True)
        print("   Please ensure DaVinci Resolve is open and running on your desktop.", flush=True)
        return False

    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    if not project:
        print("❌ Error: No open project found in DaVinci Resolve.", flush=True)
        return False

    print(f"Connected to Active Project: '{project.GetName()}'", flush=True)
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()

    # 3. Step C: Import Video & Build Timeline
    print("\n--- STEP 3: MEDIA POOL & TIMELINE SETUP ---", flush=True)
    video_clip = import_video_with_fallbacks(resolve, media_pool, root_folder, clean_video_path)
    if not video_clip:
        print(f"❌ Fatal Error: Failed to acquire video clip for '{clean_video_path}'", flush=True)
        return False

    timeline_name = f"{base_name}_Subtitled"
    timeline = media_pool.CreateTimelineFromClips(timeline_name, [video_clip])
    if not timeline:
        print(f"❌ Error: Failed to create timeline '{timeline_name}' from clip.", flush=True)
        return False

    project.SetCurrentTimeline(timeline)
    print(f"Activated Timeline: '{timeline_name}'", flush=True)

    fps_setting = timeline.GetSetting("timelineFrameRate") or project.GetSetting("timelineFrameRate") or "30"
    try:
        active_fps = float(str(fps_setting).split()[0])
    except Exception:
        active_fps = float(fps)

    print(f"Active Timeline FPS: {active_fps}", flush=True)

    timeline_start = timeline.GetStartFrame()
    video_track_items = timeline.GetItemListInTrack("video", 1) or []
    video_start = video_track_items[0].GetStart() if video_track_items else timeline_start

    print(f"Timeline Start Frame   : {timeline_start}", flush=True)
    print(f"Video Track 1 Clip Start: {video_start}", flush=True)

    while timeline.GetTrackCount("video") < 3:
        timeline.AddTrack("video")

    target_clip = find_clip_recursive(root_folder, template_name)
    if not target_clip:
        print(f"❌ Error: Title template '{template_name}' not found in Media Pool.", flush=True)
        return False
    print(f"Found Template Clip: '{target_clip.GetName()}'", flush=True)

    sub_items_on_track = timeline.GetItemListInTrack("subtitle", 1) or []
    caption_jobs = []

    if sub_items_on_track:
        print(f"\n🎯 Direct Subtitle Track Mode: Found {len(sub_items_on_track)} clips on Subtitle Track 1!", flush=True)
        for item in sub_items_on_track:
            caption_jobs.append({
                "recordFrame": item.GetStart(),
                "duration_frames": item.GetDuration(),
                "raw_text": item.GetName()
            })
    else:
        print(f"\n📄 Parsing SRT File '{os.path.basename(output_srt)}' with FPS ({active_fps})...", flush=True)
        subtitles = parse_srt(output_srt, fps=active_fps)
        if not subtitles:
            print("❌ Warning: No valid captions found in SRT file.", flush=True)
            return False

        first_sub_start = subtitles[0]["start_frame"]
        has_large_srt_offset = first_sub_start > 10000

        for sub in subtitles:
            sub_offset = (sub["start_frame"] - first_sub_start) if has_large_srt_offset else sub["start_frame"]
            caption_jobs.append({
                "recordFrame": video_start + sub_offset,
                "duration_frames": sub["duration_frames"],
                "raw_text": sub["text"]
            })

    # 4. Step D: Placing Captions on Track 3
    t_track3_start = time.time()
    print(f"\n--- STEP 4: PLACING CAPTIONS ON TRACK 3 ---", flush=True)
    print(f"Populating {len(caption_jobs)} text clips onto Video Track 3...", flush=True)
    created_count = 0

    for idx, job in enumerate(caption_jobs, start=1):
        formatted_text = format_caption_text(
            job["raw_text"],
            words_per_line=words_per_line,
            max_chars_per_line=max_chars_per_line,
            lines_per_caption=lines_per_caption
        )

        clip_info = {
            "mediaPoolItem": target_clip,
            "startFrame": 0,
            "endFrame": job["duration_frames"],
            "recordFrame": job["recordFrame"],
            "trackIndex": 3,
            "mediaType": 1
        }

        append_result = media_pool.AppendToTimeline([clip_info])
        if not append_result or len(append_result) == 0:
            print(f"⚠️ Warning: Failed to append template clip for caption #{idx}", flush=True)
            continue

        new_item = append_result[0]

        if new_item.GetFusionCompCount() > 0:
            comp = new_item.GetFusionCompByIndex(1)
            if comp:
                text_tool = (
                    comp.FindTool("Template") or 
                    comp.FindTool("TextPlus1") or 
                    comp.FindTool("TextPlus")
                )

                if not text_tool:
                    tools = comp.GetToolList().values()
                    for t in tools:
                        if t.GetAttrs().get("TOOLS_RegID") in ("TextPlus", "Template"):
                            text_tool = t
                            break

                if text_tool:
                    text_tool.SetInput("StyledText", formatted_text)
                    created_count += 1

    t_track3_elapsed = time.time() - t_track3_start
    print(f"✅ Appended & Updated {created_count}/{len(caption_jobs)} clips on Video Track 3!", flush=True)
    print(f"⏱️ Step 4 Duration (Track 3 Placement & Fusion Text Update): {format_duration(t_track3_elapsed)}", flush=True)

    # Save Project
    project_manager.SaveProject()
    print("💾 Project successfully saved.", flush=True)

    total_workflow_elapsed = time.time() - workflow_start_time

    print("\n==================================================", flush=True)
    print(" 🎉 CAPTION CREATION COMPLETE (RENDER SKIPPED)    ", flush=True)
    print(f"   Project              : '{project.GetName()}'", flush=True)
    print(f"   Timeline             : '{timeline.GetName()}'", flush=True)
    print(f"   Captions Placed      : {created_count} clips on Video Track 3", flush=True)
    print(f"   🎙️ Whisper Duration  : {format_duration(t_whisper_elapsed)}", flush=True)
    print(f"   🧩 Placement Duration: {format_duration(t_track3_elapsed)}", flush=True)
    print(f"   ⏳ Workflow Duration : {format_duration(total_workflow_elapsed)}", flush=True)
    print("==================================================", flush=True)
    return True


if __name__ == "__main__":
    try:
        file_path = r"D:\m-edits\LiveDemo\drs-caption-automation\video"
        video_file = os.path.join(file_path, "Rhiannon.mp4")
        srt_file = os.path.join(file_path, "captions.srt")

        run_caption_workflow_norender(
            video_path=video_file,
            output_srt=srt_file,
            template_name="MyCaption",
            fps=30,
            model_size="base",
            lines_per_caption=2,     # 1 for single line, 2 for double line
            words_per_line=4,        # Up to 4 words per line
            max_chars_per_line=24,   # Up to 24 characters per line
        )
    except Exception as err:
        print(f"\n💥 CRITICAL EXCEPTION IN SCRIPT EXECUTION:\n{err}", flush=True)
        traceback.print_exc()
    finally:
        total_script_elapsed = time.time() - SCRIPT_START_TIME
        print("\n==================================================", flush=True)
        print(f"  🏁 EXECUTION FINISHED", flush=True)
        print(f"  ⏱️ TOTAL TIME (START TO FINISH): {format_duration(total_script_elapsed)}", flush=True)
        print("==================================================", flush=True)
        if sys.stdin and sys.stdin.isatty():
            input("Press Enter to exit...")
