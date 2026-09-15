from pathlib import Path
import os
import uuid
import subprocess
import shutil

from pypdf import PdfReader, PdfWriter, PdfMerger
from PIL import Image

TMP = Path("temp/pdf")
TMP.mkdir(parents=True, exist_ok=True)


def new_file(ext=".pdf"):
    if not ext.startswith("."):
        ext = "." + ext
    return str(TMP / f"{uuid.uuid4().hex}{ext}")


def pdf_info(src):
    reader = PdfReader(src)

    return {
        "pages": len(reader.pages),
        "encrypted": reader.is_encrypted,
        "metadata": dict(reader.metadata or {}),
    }


def images_to_pdf(files, output):
    images = []

    for path in files:
        img = Image.open(path).convert("RGB")
        images.append(img)

    if not images:
        raise RuntimeError("No images")

    first = images[0]
    rest = images[1:]

    first.save(
        output,
        "PDF",
        resolution=100,
        save_all=True,
        append_images=rest,
    )

    return output


def merge_pdfs(files, output):
    merger = PdfMerger()

    for path in files:
        merger.append(path)

    merger.write(output)
    merger.close()

    return output


def split_pdf(src, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(src)
    outputs = []

    for i, page in enumerate(reader.pages, 1):
        writer = PdfWriter()
        writer.add_page(page)

        out = output_dir / f"page_{i}.pdf"

        with open(out, "wb") as f:
            writer.write(f)

        outputs.append(str(out))

    return outputs


def extract_pages(src, start, end, output):
    reader = PdfReader(src)
    writer = PdfWriter()

    start = max(1, int(start))
    end = min(len(reader.pages), int(end))

    for i in range(start - 1, end):
        writer.add_page(reader.pages[i])

    with open(output, "wb") as f:
        writer.write(f)

    return output


def rotate_pdf(src, output, degrees=90):
    reader = PdfReader(src)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(degrees)
        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def crop_pdf(src, output):
    reader = PdfReader(src)
    writer = PdfWriter()

    for page in reader.pages:
        box = page.mediabox

        width = float(box.width)
        height = float(box.height)

        margin_x = width * 0.05
        margin_y = height * 0.05

        box.lower_left = (
            float(box.left) + margin_x,
            float(box.bottom) + margin_y,
        )

        box.upper_right = (
            float(box.right) - margin_x,
            float(box.top) - margin_y,
        )

        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def extract_text(src, output):
    reader = PdfReader(src)

    parts = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""

        parts.append(
            f"===== PAGE {i} =====\n{text}"
        )

    text = "\n\n".join(parts)

    Path(output).write_text(text, encoding="utf-8")

    return output, text


def extract_images(src, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(src)
    outputs = []

    counter = 0

    for page_number, page in enumerate(reader.pages, 1):
        for image in page.images:
            counter += 1

            ext = Path(image.name).suffix or ".png"
            out = output_dir / f"page_{page_number}_{counter}{ext}"

            with open(out, "wb") as f:
                f.write(image.data)

            outputs.append(str(out))

    return outputs


def encrypt_pdf(src, output, password):
    reader = PdfReader(src)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(password)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def decrypt_pdf(src, output, password):
    reader = PdfReader(src)

    if not reader.is_encrypted:
        shutil.copyfile(src, output)
        return output

    if not reader.decrypt(password):
        raise RuntimeError("رمز عبور اشتباه است.")

    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def add_watermark(src, output, text="@ByteTunnel"):
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import Color
    from pypdf import PdfReader, PdfWriter

    watermark = new_file("_watermark.pdf")

    reader = PdfReader(src)
    width = float(reader.pages[0].mediabox.width)
    height = float(reader.pages[0].mediabox.height)

    c = canvas.Canvas(watermark, pagesize=(width, height))
    c.saveState()

    c.setFillColor(Color(0, 0, 0, alpha=0.18))
    c.setFont("Helvetica-Bold", 28)
    c.translate(width / 2, height / 2)
    c.rotate(35)
    c.drawCentredString(0, 0, text)

    c.restoreState()
    c.save()

    wm_reader = PdfReader(watermark)
    wm_page = wm_reader.pages[0]

    pdf_reader = PdfReader(src)
    writer = PdfWriter()

    for page in pdf_reader.pages:
        page.merge_page(wm_page)
        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    try:
        os.remove(watermark)
    except OSError:
        pass

    return output


def metadata(src):
    reader = PdfReader(src)

    data = reader.metadata or {}

    if not data:
        return "ℹ️ Metadata پیدا نشد."

    lines = ["ℹ️ PDF Metadata"]

    for key, value in data.items():
        lines.append(f"{key}: {value}")

    return "\n".join(lines)


def set_metadata(src, output, title=None, author=None, subject=None):
    reader = PdfReader(src)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    metadata = {}

    if title:
        metadata["/Title"] = title

    if author:
        metadata["/Author"] = author

    if subject:
        metadata["/Subject"] = subject

    if metadata:
        writer.add_metadata(metadata)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def reorder_pages(src, output, order):
    reader = PdfReader(src)
    writer = PdfWriter()

    for number in order:
        number = int(number)

        if number < 1 or number > len(reader.pages):
            raise RuntimeError(f"صفحه {number} وجود ندارد.")

        writer.add_page(reader.pages[number - 1])

    with open(output, "wb") as f:
        writer.write(f)

    return output


def compress_pdf(src, output):
    reader = PdfReader(src)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    try:
        writer.compress_identical_objects()
    except Exception:
        pass

    with open(output, "wb") as f:
        writer.write(f)

    return output


def pdf_to_images(src, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prefix = output_dir / "page"

    result = subprocess.run(
        [
            "pdftoppm",
            "-jpeg",
            "-r",
            "150",
            src,
            str(prefix),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr[-2000:] or "pdftoppm error"
        )

    outputs = sorted(
        str(x)
        for x in output_dir.glob("page-*.jpg")
    )

    return outputs


def ocr_pdf(src, output):
    reader = PdfReader(src)

    pages_text = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""

        if text.strip():
            pages_text.append(
                f"===== PAGE {i} =====\n{text}"
            )

    text = "\n\n".join(pages_text)

    Path(output).write_text(text, encoding="utf-8")

    return output, text
