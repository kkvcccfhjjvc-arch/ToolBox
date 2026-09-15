from pathlib import Path
import hashlib
import mimetypes
import zipfile
import shutil
import os


def file_info(path):
    p = Path(path)
    size = p.stat().st_size

    if size < 1024:
        size_text = f"{size} B"
    elif size < 1024 ** 2:
        size_text = f"{size / 1024:.2f} KB"
    elif size < 1024 ** 3:
        size_text = f"{size / (1024 ** 2):.2f} MB"
    else:
        size_text = f"{size / (1024 ** 3):.2f} GB"

    mime = mimetypes.guess_type(str(p))[0] or "unknown"

    return {
        "name": p.name,
        "size": size,
        "size_text": size_text,
        "extension": p.suffix or "none",
        "mime": mime,
        "path": str(p),
    }


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def create_zip(files, output):
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for file in files:
            p = Path(file)
            z.write(file, arcname=p.name)

    return output


def extract_zip(src, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(src, "r") as z:
        z.extractall(output)

    return output


def inspect_zip(path):
    with zipfile.ZipFile(path, "r") as z:
        return z.namelist()


def rename_file(src, new_name):
    src = Path(src)
    destination = src.parent / Path(new_name).name
    src.rename(destination)
    return str(destination)


def analyze_file(path):
    info = file_info(path)

    result = {
        "name": info["name"],
        "size": info["size_text"],
        "extension": info["extension"],
        "mime": info["mime"],
        "md5": md5(path),
        "sha256": sha256(path),
    }

    return result


def is_zip(path):
    return zipfile.is_zipfile(path)
