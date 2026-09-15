from pathlib import Path
import uuid
import re

import qrcode
from PIL import Image


TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


def new_file(ext=".png"):
    return TEMP_DIR / f"qr_{uuid.uuid4().hex}{ext}"


def make_qr(data, output, fill_color="black", back_color="white"):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color=fill_color,
        back_color=back_color,
    ).convert("RGB")

    image.save(output, "PNG")
    return output


def make_wifi(ssid, password, security="WPA", hidden=False):
    def esc(value):
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace(":", "\\:")
            .replace('"', '\\"')
        )

    return (
        f"WIFI:T:{security};"
        f"S:{esc(ssid)};"
        f"P:{esc(password)};"
        f"H:{'true' if hidden else 'false'};;"
    )


def make_phone(phone):
    return f"tel:{phone.strip()}"


def make_email(email, subject="", body=""):
    from urllib.parse import quote

    result = f"mailto:{email.strip()}"

    params = []

    if subject:
        params.append(f"subject={quote(subject)}")

    if body:
        params.append(f"body={quote(body)}")

    if params:
        result += "?" + "&".join(params)

    return result


def make_geo(latitude, longitude):
    return f"geo:{latitude},{longitude}"


def make_vcard(name, phone="", email="", organization=""):
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{name}",
    ]

    if phone:
        lines.append(f"TEL:{phone}")

    if email:
        lines.append(f"EMAIL:{email}")

    if organization:
        lines.append(f"ORG:{organization}")

    lines.append("END:VCARD")

    return "\n".join(lines)


def make_barcode_data(value):
    value = value.strip()

    if not value:
        raise ValueError("مقدار خالی است.")

    if not re.fullmatch(r"[0-9A-Za-z .:/_-]+", value):
        raise ValueError("برای Barcode فقط حروف، اعداد و کاراکترهای ساده استفاده کن.")

    return value


def make_barcode(value, output):
    # Code 128 بدون وابستگی خارجی؛ با Pillow یک Barcode ساده ساخته می‌شود.
    value = make_barcode_data(value)

    try:
        from reportlab.graphics.barcode import code128
        from reportlab.graphics import renderPM

        barcode = code128.Code128(value, barHeight=50, barWidth=1.2)
        drawing = barcode

        renderPM.drawToFile(
            drawing,
            str(output),
            fmt="PNG",
        )

        return output

    except Exception:
        # Fallback: QR برای اطمینان از اینکه ابزار کاملاً از کار نیفتد.
        return make_qr(value, output)


def image_to_qr_text(path):
    try:
        import cv2

        image = cv2.imread(str(path))

        if image is None:
            return None

        detector = cv2.QRCodeDetector()
        data, points, _ = detector.detectAndDecode(image)

        return data.strip() if data else None

    except Exception:
        return None
