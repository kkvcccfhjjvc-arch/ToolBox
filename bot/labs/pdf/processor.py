from pathlib import Path
import os
import shutil
import subprocess

from pypdf import PdfReader, PdfWriter
from PIL import Image


def images_to_pdf(files, output):
    images = []

    for path in files:
        im = Image.open(path).convert("RGB")
        images.append(im)

    if not images:
        raise RuntimeError("هیچ تصویری وجود ندارد")

    images[0].save(
        output,
        "PDF",
        resolution=100.0,
        save_all=True,
        append_images=images[1:],
    )

    return output


def pdf_to_text(src, output):
    reader = PdfReader(src)

    text_parts = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        text_parts.append(f"--- Page {i} ---\n{text}")

    with open(output, "w", encoding="utf-8") as f:
        f.write("\n\n".join(text_parts))

    return output


def merge_pdfs(files, output):
    writer = PdfWriter()

    for path in files:
        reader = PdfReader(path)

        if reader.is_encrypted:
            raise RuntimeError(
                f"فایل PDF رمزگذاری شده است: {Path(path).name}"
            )

        for page in reader.pages:
            writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def split_pdf(src, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(src)
    results = []

    for i, page in enumerate(reader.pages, 1):
        writer = PdfWriter()
        writer.add_page(page)

        output = output_dir / f"page_{i}.pdf"

        with open(output, "wb") as f:
            writer.write(f)

        results.append(str(output))

    return results


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
        raise RuntimeError("رمز PDF اشتباه است")

    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def watermark_pdf(src, output, text="@ByteTunnel"):
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import grey
    from pypdf import PdfReader, PdfWriter

    temp = str(Path(output).with_suffix(".watermark.pdf"))

    reader = PdfReader(src)

    width = float(reader.pages[0].mediabox.width)
    height = float(reader.pages[0].mediabox.height)

    c = canvas.Canvas(temp, pagesize=(width, height))
    c.setFillColor(grey)
    c.setFont("Helvetica", 28)
    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(35)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.save()

    watermark = PdfReader(temp)
    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(watermark.pages[0])
        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    try:
        os.remove(temp)
    except Exception:
        pass

    return output


def add_watermark(src, output, text="@ByteTunnel"):
    return watermark_pdf(src, output, text)


def rotate_pdf(src, output, degrees=90):
    reader = PdfReader(src)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(degrees)
        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def crop_pdf(src, output, left=0, bottom=0, right=None, top=None):
    reader = PdfReader(src)
    writer = PdfWriter()

    for page in reader.pages:
        box = page.mediabox

        if right is None:
            right = float(box.right)

        if top is None:
            top = float(box.top)

        page.mediabox.lower_left = (left, bottom)
        page.mediabox.upper_right = (right, top)

        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def extract_images(src, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(src)
    results = []

    for page_number, page in enumerate(reader.pages, 1):
        try:
            images = page.images
        except Exception:
            images = []

        for index, image in enumerate(images, 1):
            output = output_dir / (
                f"page_{page_number}_image_{index}{Path(image.name).suffix or '.png'}"
            )

            with open(output, "wb") as f:
                f.write(image.data)

            results.append(str(output))

    return results


def pdf_to_images(src, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prefix = output_dir / "page"

    result = subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-r",
            "150",
            src,
            str(prefix),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "تبدیل PDF به تصویر انجام نشد"
        )

    return [
        str(x)
        for x in sorted(output_dir.glob("page-*.png"))
    ]


def ocr_pdf(src, output):
    """
    فعلاً متن PDF را استخراج می‌کند.
    اگر PDF اسکن‌شده باشد، OCR تصویری در مرحله بعد اضافه می‌شود.
    """

    return pdf_to_text(src, output)


def get_metadata(src):
    reader = PdfReader(src)

    metadata = reader.metadata or {}

    return {
        "pages": len(reader.pages),
        "title": metadata.get("/Title", "-"),
        "author": metadata.get("/Author", "-"),
        "subject": metadata.get("/Subject", "-"),
        "creator": metadata.get("/Creator", "-"),
        "producer": metadata.get("/Producer", "-"),
        "creation_date": metadata.get("/CreationDate", "-"),
    }


def metadata(src):
    return get_metadata(src)


def set_metadata(src, output, title=None, author=None, subject=None):
    reader = PdfReader(src)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    meta = {}

    if title:
        meta["/Title"] = title

    if author:
        meta["/Author"] = author

    if subject:
        meta["/Subject"] = subject

    if meta:
        writer.add_metadata(meta)

    with open(output, "wb") as f:
        writer.write(f)

    return output


def reorder_pages(src, output, order):
    reader = PdfReader(src)
    writer = PdfWriter()

    for number in order:
        index = int(number) - 1

        if index < 0 or index >= len(reader.pages):
            raise RuntimeError(f"شماره صفحه نامعتبر است: {number}")

        writer.add_page(reader.pages[index])

    with open(output, "wb") as f:
        writer.write(f)

    return output
