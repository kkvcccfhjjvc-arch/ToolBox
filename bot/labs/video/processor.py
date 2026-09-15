from pathlib import Path
import asyncio
import uuid


TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


def new_file(ext: str) -> Path:
    return TEMP_DIR / f"video_{uuid.uuid4().hex}{ext}"


async def run_cmd(args):
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(stderr.decode(errors="ignore")[-3000:])

    return stdout.decode(errors="ignore")


async def ffprobe(path: str):
    return await run_cmd([
        "ffprobe",
        "-v", "error",
        "-show_entries",
        "format=filename,duration,size,bit_rate,format_name",
        "-show_entries",
        "stream=index,codec_name,codec_type,width,height,r_frame_rate",
        "-of", "default=noprint_wrappers=1",
        path,
    ])


async def video_info(src: str):
    return await ffprobe(src)


async def thumbnail(src: str, output: str):
    await run_cmd([
        "ffmpeg", "-y",
        "-ss", "00:00:01",
        "-i", src,
        "-frames:v", "1",
        "-q:v", "2",
        output,
    ])


async def screenshot(src: str, output: str, timestamp="00:00:01"):
    await run_cmd([
        "ffmpeg", "-y",
        "-ss", timestamp,
        "-i", src,
        "-frames:v", "1",
        "-q:v", "2",
        output,
    ])


async def sample_video(src: str, output: str):
    await run_cmd([
        "ffmpeg", "-y",
        "-ss", "00:00:00",
        "-i", src,
        "-t", "10",
        "-c", "copy",
        output,
    ])


async def trim(src: str, output: str, start: str, duration: str):
    await run_cmd([
        "ffmpeg", "-y",
        "-ss", start,
        "-i", src,
        "-t", duration,
        "-c", "copy",
        output,
    ])


async def watermark(src: str, output: str, text: str):
    safe_text = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    await run_cmd([
        "ffmpeg", "-y",
        "-i", src,
        "-vf",
        f"drawtext=text='{safe_text}':"
        "x=20:y=h-th-20:"
        "fontsize=28:"
        "fontcolor=white:"
        "box=1:"
        "boxcolor=black@0.55:"
        "boxborderw=8",
        "-c:a", "copy",
        output,
    ])


async def extract_subtitles(src: str, output: str):
    result = await run_cmd([
        "ffmpeg",
        "-i", src,
        "-map", "0:s:0",
        "-f", "srt",
        output,
    ])
    return result


async def process_subtitle_extract(src: str, output: str):
    try:
        await extract_subtitles(src, output)
        return True
    except Exception:
        return False
