from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pathlib import Path
import uuid
import os
import math
import subprocess

TMP = Path("temp/image")
TMP.mkdir(parents=True, exist_ok=True)

def new_file(ext):
    if not ext.startswith("."):
        ext = "." + ext
    return str(TMP / f"{uuid.uuid4().hex}{ext}")

def load(path):
    return Image.open(path)

def save(img, output):
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    img.save(output)
    return output

def crop(src, output, left=0, top=0, right=None, bottom=None):
    img = load(src)
    w, h = img.size
    right = right or w
    bottom = bottom or h
    result = img.crop((left, top, right, bottom))
    return save(result, output)

def draw(src, output):
    img = load(src).convert("RGB")
    d = ImageDraw.Draw(img)

    w, h = img.size
    margin = max(10, min(w, h) // 20)

    d.rectangle(
        (margin, margin, w - margin, h - margin),
        outline="red",
        width=max(3, min(w, h) // 100)
    )

    return save(img, output)

def blur(src, output):
    img = load(src)
    return save(img.filter(ImageFilter.GaussianBlur(8)), output)

def pixelate(src, output):
    img = load(src)
    w, h = img.size

    small_w = max(1, w // 30)
    small_h = max(1, h // 30)

    small = img.resize((small_w, small_h), Image.Resampling.NEAREST)
    result = small.resize((w, h), Image.Resampling.NEAREST)

    return save(result, output)

def get_font(size=36):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()

def watermark(src, output, text="@ByteTunnel"):
    img = load(src).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    font = get_font(max(20, min(img.size) // 20))

    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = img.width - tw - 25
    y = img.height - th - 25

    d.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 160))
    d.text((x, y), text, font=font, fill=(255, 255, 255, 210))

    return save(Image.alpha_composite(img, overlay), output)

def stamp(src, output, text="TOOL BOX"):
    img = load(src).convert("RGBA")
    d = ImageDraw.Draw(img)

    font = get_font(max(24, min(img.size) // 15))
    bbox = d.textbbox((0, 0), text, font=font)

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (img.width - tw) // 2
    y = (img.height - th) // 2

    padding = 15

    d.rounded_rectangle(
        (
            x - padding,
            y - padding,
            x + tw + padding,
            y + th + padding
        ),
        radius=12,
        fill=(0, 0, 0, 150)
    )

    d.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return save(img, output)

def timestamp(src, output):
    from datetime import datetime

    img = load(src).convert("RGBA")
    d = ImageDraw.Draw(img)

    text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    font = get_font(max(20, min(img.size) // 25))

    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = 20
    y = img.height - th - 20

    d.rounded_rectangle(
        (x - 8, y - 8, x + tw + 8, y + th + 8),
        radius=8,
        fill=(0, 0, 0, 170)
    )

    d.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return save(img, output)

def stitch(files, output):
    images = [load(x).convert("RGB") for x in files]

    width = max(x.width for x in images)
    total_height = sum(
        int(x.height * width / x.width)
        for x in images
    )

    canvas = Image.new("RGB", (width, total_height), "white")

    y = 0

    for img in images:
        new_h = int(img.height * width / img.width)
        resized = img.resize((width, new_h), Image.Resampling.LANCZOS)
        canvas.paste(resized, (0, y))
        y += new_h

    return save(canvas, output)

def split(src, output_dir):
    img = load(src)
    w, h = img.size

    half = h // 2

    outputs = []

    for i, box in enumerate([
        (0, 0, w, half),
        (0, half, w, h)
    ], 1):
        out = str(Path(output_dir) / f"part_{i}.jpg")
        img.crop(box).convert("RGB").save(out, quality=95)
        outputs.append(out)

    return outputs

def exif_view(src):
    img = load(src)
    data = img.getexif()

    if not data:
        return "❌ اطلاعات EXIF پیدا نشد."

    lines = ["📋 EXIF Information"]

    for key, value in data.items():
        lines.append(f"{key}: {value}")

    return "\n".join(lines[:100])

def exif_remove(src, output):
    img = load(src)

    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))

    return save(clean, output)

def palette(src, output):
    img = load(src).convert("RGB")
    img.thumbnail((500, 500))

    quant = img.quantize(colors=8).convert("RGB")
    colors = quant.getcolors(maxcolors=256)

    colors = sorted(colors, reverse=True)[:8]

    box_w = 180
    box_h = 100

    result = Image.new("RGB", (box_w * 4, box_h * 2), "white")
    d = ImageDraw.Draw(result)

    for i, (_, color) in enumerate(colors):
        x = (i % 4) * box_w
        y = (i // 4) * box_h

        d.rectangle(
            (x, y, x + box_w, y + box_h),
            fill=color
        )

        text = "#%02X%02X%02X" % color
        d.text((x + 10, y + 65), text, font=get_font(20), fill="white")

    return save(result, output)

def ascii_art(src, output):
    img = load(src).convert("L")

    width = 100
    ratio = img.height / img.width
    height = max(1, int(width * ratio * 0.5))

    img = img.resize((width, height))

    chars = "@%#*+=-:. "

    lines = []

    for y in range(img.height):
        line = ""

        for x in range(img.width):
            pixel = img.getpixel((x, y))
            index = pixel * (len(chars) - 1) // 255
            line += chars[index]

        lines.append(line)

    Path(output).write_text("\n".join(lines), encoding="utf-8")

    return output

def document_scan(src, output):
    img = load(src).convert("RGB")
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)

    # افزایش خوانایی متن
    img = img.filter(ImageFilter.SHARPEN)

    return save(img, output)

def contact_sheet(files, output):
    images = []

    for path in files:
        img = load(path).convert("RGB")
        img.thumbnail((400, 300))
        images.append(img.copy())

    if not images:
        raise RuntimeError("No images")

    columns = 2
    rows = math.ceil(len(images) / columns)

    cell_w = 420
    cell_h = 330

    sheet = Image.new(
        "RGB",
        (columns * cell_w, rows * cell_h),
        "white"
    )

    for i, img in enumerate(images):
        x = (i % columns) * cell_w
        y = (i // columns) * cell_h

        px = x + (cell_w - img.width) // 2
        py = y + 10

        sheet.paste(img, (px, py))

    return save(sheet, output)
