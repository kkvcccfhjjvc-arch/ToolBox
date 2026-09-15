import asyncio
import json
import os
import uuid
from pathlib import Path


TMP = Path("temp/audio")
TMP.mkdir(parents=True, exist_ok=True)


def new_file(ext):
    if not ext.startswith("."):
        ext = "." + ext
    return str(TMP / f"{uuid.uuid4().hex}{ext}")


async def run_ffmpeg(args):
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        *map(str, args),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error = stderr.decode(errors="ignore").strip()
        raise RuntimeError(error[-3000:] or "FFmpeg error")

    return stdout.decode(errors="ignore")


async def ffprobe(path):
    process = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError("Unable to read media information")

    return json.loads(stdout.decode(errors="ignore"))


async def convert(src, output):
    output = str(output)
    ext = Path(output).suffix.lower()

    codecs = {
        ".mp3": ["-c:a", "libmp3lame", "-q:a", "3"],
        ".ogg": ["-c:a", "libopus", "-b:a", "128k"],
        ".wav": ["-c:a", "pcm_s16le"],
        ".flac": ["-c:a", "flac"],
        ".m4a": ["-c:a", "aac", "-b:a", "192k"],
    }

    await run_ffmpeg([
        "-i", src,
        "-vn",
        *codecs.get(ext, ["-c:a", "copy"]),
        output,
    ])

    return output


async def cut(src, output, start, duration):
    await run_ffmpeg([
        "-ss", str(start),
        "-i", src,
        "-t", str(duration),
        "-vn",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        output,
    ])

    return output


async def merge(files, output):
    listing = Path(new_file(".txt"))

    with open(listing, "w", encoding="utf-8") as f:
        for path in files:
            safe = str(Path(path).resolve()).replace("'", "'\\''")
            f.write(f"file '{safe}'\n")

    try:
        await run_ffmpeg([
            "-f", "concat",
            "-safe", "0",
            "-i", str(listing),
            "-c:a", "libmp3lame",
            "-q:a", "3",
            output,
        ])
    finally:
        try:
            listing.unlink()
        except OSError:
            pass

    return output


async def speed(src, output, value):
    value = float(value)

    filters = []

    while value > 2:
        filters.append("atempo=2")
        value /= 2

    while value < 0.5:
        filters.append("atempo=0.5")
        value /= 0.5

    filters.append(f"atempo={value}")

    await run_ffmpeg([
        "-i", src,
        "-af", ",".join(filters),
        "-c:a", "libmp3lame",
        "-q:a", "3",
        output,
    ])

    return output


async def change_volume(src, output, value):
    value = float(value)

    await run_ffmpeg([
        "-i", src,
        "-af", f"volume={value}",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        output,
    ])

    return output


async def pitch(src, output, semitones):
    semitones = float(semitones)

    factor = 2 ** (semitones / 12)
    rate = int(44100 * factor)

    await run_ffmpeg([
        "-i", src,
        "-af", f"asetrate={rate},aresample=44100",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        output,
    ])

    return output


async def silence_remove(src, output):
    await run_ffmpeg([
        "-i", src,
        "-af",
        "silenceremove="
        "start_periods=1:"
        "start_duration=0.5:"
        "start_threshold=-45dB:"
        "stop_periods=-1:"
        "stop_duration=0.5:"
        "stop_threshold=-45dB",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        output,
    ])

    return output


async def reverse(src, output):
    await run_ffmpeg([
        "-i", src,
        "-af", "areverse",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        output,
    ])

    return output


async def waveform(src, output):
    await run_ffmpeg([
        "-i", src,
        "-filter_complex", "showwavespic=s=1600x400",
        "-frames:v", "1",
        output,
    ])

    return output


async def spectrogram(src, output):
    await run_ffmpeg([
        "-i", src,
        "-lavfi",
        "showspectrumpic=s=1600x900:legend=disabled",
        "-frames:v", "1",
        output,
    ])

    return output


async def compress(src, output):
    await run_ffmpeg([
        "-i", src,
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "96k",
        output,
    ])

    return output


async def extract_audio(src, output):
    await run_ffmpeg([
        "-i", src,
        "-vn",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        output,
    ])

    return output


def metadata(info):
    fmt = info.get("format", {})
    tags = fmt.get("tags", {})

    return tags


def format_info(info):
    fmt = info.get("format", {})
    streams = info.get("streams", [])

    lines = [
        f"📁 Format: {fmt.get('format_name', 'Unknown')}",
        f"⏱️ Duration: {fmt.get('duration', 'Unknown')} sec",
        f"📦 Size: {fmt.get('size', 'Unknown')} bytes",
        f"💾 Bitrate: {fmt.get('bit_rate', 'Unknown')}",
    ]

    for stream in streams:
        if stream.get("codec_type") == "audio":
            lines.extend([
                f"🎵 Codec: {stream.get('codec_name', 'Unknown')}",
                f"🔊 Sample rate: {stream.get('sample_rate', 'Unknown')}",
                f"🎚️ Channels: {stream.get('channels', 'Unknown')}",
            ])
            break

    return "\n".join(lines)
