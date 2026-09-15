import asyncio
import json
import os
import uuid

TMP = os.path.expanduser("~/ToolBox/temp")
os.makedirs(TMP, exist_ok=True)


def new_file(ext):
    return os.path.join(TMP, f"{uuid.uuid4().hex}{ext}")


async def run_ffmpeg(args):
    p = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await p.communicate()

    if p.returncode != 0:
        raise RuntimeError(stderr.decode(errors="ignore")[-2000:])

    return stdout.decode(errors="ignore")


async def ffprobe(path):
    p = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await p.communicate()

    if p.returncode != 0:
        raise RuntimeError("Unable to read media information")

    return json.loads(stdout.decode(errors="ignore"))


async def convert(src, ext):
    out = new_file(ext)

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
        *codecs.get(ext, []),
        out
    ])

    return out


async def cut(src, start, duration):
    out = new_file(".mp3")

    await run_ffmpeg([
        "-ss", str(start),
        "-i", src,
        "-t", str(duration),
        "-vn",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        out
    ])

    return out


async def merge(files):
    listing = new_file(".txt")

    with open(listing, "w", encoding="utf-8") as f:
        for path in files:
            f.write(
                "file '{}'\n".format(
                    os.path.abspath(path).replace("'", "'\\''")
                )
            )

    out = new_file(".mp3")

    await run_ffmpeg([
        "-f", "concat",
        "-safe", "0",
        "-i", listing,
        "-c:a", "libmp3lame",
        "-q:a", "3",
        out
    ])

    try:
        os.remove(listing)
    except OSError:
        pass

    return out


async def speed(src, value):
    value = float(value)

    filters = []

    while value > 2:
        filters.append("atempo=2")
        value /= 2

    while value < 0.5:
        filters.append("atempo=0.5")
        value /= 0.5

    filters.append(f"atempo={value}")

    out = new_file(".mp3")

    await run_ffmpeg([
        "-i", src,
        "-af", ",".join(filters),
        "-c:a", "libmp3lame",
        "-q:a", "3",
        out
    ])

    return out


async def change_volume(src, value):
    out = new_file(".mp3")

    await run_ffmpeg([
        "-i", src,
        "-af", f"volume={value}",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        out
    ])

    return out


async def pitch(src, semitones):
    semitones = float(semitones)
    factor = 2 ** (semitones / 12)

    rate = int(44100 * factor)

    out = new_file(".mp3")

    await run_ffmpeg([
        "-i", src,
        "-af", f"asetrate={rate},aresample=44100",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        out
    ])

    return out


async def silence_remove(src):
    out = new_file(".mp3")

    await run_ffmpeg([
        "-i", src,
        "-af",
        "silenceremove=start_periods=1:"
        "start_duration=0.5:"
        "start_threshold=-45dB:"
        "stop_periods=-1:"
        "stop_duration=0.5:"
        "stop_threshold=-45dB",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        out
    ])

    return out


async def reverse(src):
    out = new_file(".mp3")

    await run_ffmpeg([
        "-i", src,
        "-af", "areverse",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        out
    ])

    return out


async def waveform(src):
    out = new_file(".png")

    await run_ffmpeg([
        "-i", src,
        "-filter_complex", "showwavespic=s=1600x400",
        "-frames:v", "1",
        out
    ])

    return out


async def spectrogram(src):
    out = new_file(".png")

    await run_ffmpeg([
        "-i", src,
        "-lavfi",
        "showspectrumpic=s=1600x900:legend=disabled",
        "-frames:v", "1",
        out
    ])

    return out


async def compress(src):
    out = new_file(".mp3")

    await run_ffmpeg([
        "-i", src,
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "96k",
        out
    ])

    return out


async def extract_audio(src):
    out = new_file(".mp3")

    await run_ffmpeg([
        "-i", src,
        "-vn",
        "-c:a", "libmp3lame",
        "-q:a", "3",
        out
    ])

    return out
