import time
import whisper

SCRIPT_START_TIME = time.perf_counter()


def extract_word_chunks(
    result,
    fps=30,
    lines_per_caption=2,
    words_per_line=4,
    max_chars_per_line=24,
):
    """Splits Whisper word-level timestamps into chunks based on:

- Character limit: at most max_chars_per_line (24) characters per line.
- Word count limits: at most words_per_line (4) words per line.
- Caption lines limit: at most lines_per_caption (1 or 2) lines per caption.
- Natural punctuation breaks after the 6th word (. , ? !).
- Silence gaps exceeding 8 frames between words.
    """
    all_words = []
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            clean_word = w["word"].strip()
            if clean_word:
                all_words.append(
                    {
                        "word": clean_word,
                        "start": w["start"],
                        "end": w["end"],
                    }
                )

    if not all_words:
        return []

    punctuation_marks = (".", ",", "?", "!")
    max_silence_duration = 8.0 / fps  # 8 frames converted to seconds

    chunks = []
    i = 0
    total_words = len(all_words)

    while i < total_words:
        lines = []
        current_line_words = []
        current_line_chars = 0
        caption_words = []

        while i < total_words:
            word_obj = all_words[i]
            word_text = word_obj["word"]
            word_len = len(word_text)

            # 1. Check for silence gap before this word (> 8 frames)
            if caption_words:
                prev_end = caption_words[-1]["end"]
                gap = word_obj["start"] - prev_end
                if gap > max_silence_duration:
                    break

            # 2. Calculate length if adding word to current line
            needed_chars = (
                word_len
                if not current_line_words
                else current_line_chars + 1 + word_len
            )

            # Check if current line exceeds words_per_line OR max_chars_per_line
            if len(current_line_words) >= words_per_line or needed_chars > max_chars_per_line:
                if current_line_words:
                    lines.append(" ".join(current_line_words))
                    current_line_words = []
                    current_line_chars = 0

                # If we've reached the line limit for this caption block, finalize it
                if len(lines) >= lines_per_caption:
                    break

                needed_chars = word_len

            # Add word to current line and caption tracking
            current_line_words.append(word_text)
            current_line_chars = needed_chars
            caption_words.append(word_obj)
            i += 1

            # 3. Check for early break on punctuation after the 6th word onwards
            if lines_per_caption == 2 and len(caption_words) >= 6:
                if word_text.endswith(punctuation_marks):
                    break

        # Flush remaining words in the active line
        if current_line_words:
            lines.append(" ".join(current_line_words))

        if caption_words:
            chunks.append(
                {
                    "start": caption_words[0]["start"],
                    "end": caption_words[-1]["end"],
                    "text": "\n".join(lines),
                }
            )

    return chunks


def format_timestamp(seconds):
    """Converts seconds into SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    if milliseconds >= 1000:
        milliseconds = 999
        secs += 1
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def export_chunks_to_srt(chunks, output_srt="captions.srt"):
    """Writes formatted word chunks into a standard SRT subtitle file."""
    with open(output_srt, "w", encoding="utf-8") as f:
        for idx, chunk in enumerate(chunks, start=1):
            start_str = format_timestamp(chunk["start"])
            end_str = format_timestamp(chunk["end"])
            text = chunk["text"]

            f.write(f"{idx}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{text}\n\n")

    print(f"SRT file generated: {output_srt}")


def format_duration(seconds):
    """Formats elapsed seconds into a human-readable string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs:.2f}s"
    if minutes > 0:
        return f"{minutes}m {secs:.2f}s"
    return f"{secs:.2f}s"


def log_total_time(start_time):
    """Logs total elapsed time from start_time to now."""
    elapsed = time.perf_counter() - start_time
    print(f"Total time taken: {format_duration(elapsed)} ({elapsed:.2f}s)")


def generate_srt_from_whisper(
    video_path,
    output_srt="captions.srt",
    fps=30,
    model_size="base",
    lines_per_caption=2,
    words_per_line=4,
    max_chars_per_line=24,
):
    print("Transcribing audio with Whisper...")
    model = whisper.load_model(model_size)
    result = model.transcribe(video_path, word_timestamps=True)

    chunks = extract_word_chunks(
        result,
        fps=fps,
        lines_per_caption=lines_per_caption,
        words_per_line=words_per_line,
        max_chars_per_line=max_chars_per_line,
    )

    if not chunks:
        print("No speech detected.")
        return

    # Export directly to SRT
    export_chunks_to_srt(chunks, output_srt)


if __name__ == "__main__":
    try:
        file_path = r"C:\\REPLACE_TO_YOUR_PATH_TO_VIDEO"
        generate_srt_from_whisper(
            video_path=file_path + "Rhiannon.mp4",
            output_srt=file_path + "captions.srt",
            fps=30,
            lines_per_caption=2,     # 1 for single line, 2 for double line
            words_per_line=4,        # Up to 4 words per line
            max_chars_per_line=24,   # Up to 24 characters per line
        )
    finally:
        log_total_time(SCRIPT_START_TIME)
