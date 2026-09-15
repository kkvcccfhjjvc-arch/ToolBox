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
    """
    Robust QR decoder:
    1. OpenCV QRCodeDetector
    2. OpenCV multi QR detection
    3. Several resized/gray/threshold variants
    4. pyzbar/ZBar fallback
    """
    try:
        import cv2
        import numpy as np
    except Exception:
        cv2 = None
        np = None

    # ---------- OpenCV ----------
    if cv2 is not None:
        try:
            image = cv2.imread(str(path))

            if image is not None:
                h, w = image.shape[:2]

                variants = [image]

                # Upscale small images
                if max(w, h) < 1800:
                    scale = 2.5
                    up = cv2.resize(
                        image,
                        None,
                        fx=scale,
                        fy=scale,
                        interpolation=cv2.INTER_CUBIC,
                    )
                    variants.append(up)

                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                variants.append(gray)

                # Contrast / threshold variants
                clahe = cv2.createCLAHE(
                    clipLimit=2.0,
                    tileGridSize=(8, 8),
                )
                enhanced = clahe.apply(gray)
                variants.append(enhanced)

                _, threshold = cv2.threshold(
                    enhanced,
                    0,
                    255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU,
                )
                variants.append(threshold)

                adaptive = cv2.adaptiveThreshold(
                    enhanced,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    31,
                    5,
                )
                variants.append(adaptive)

                detector = cv2.QRCodeDetector()

                for img in variants:
                    try:
                        # Single QR
                        data, points, _ = detector.detectAndDecode(img)

                        if data and data.strip():
                            return data.strip()
                    except Exception:
                        pass

                    try:
                        # Multiple QR codes
                        ok, decoded_info, points, _ = (
                            detector.detectAndDecodeMulti(img)
                        )

                        if ok and decoded_info:
                            values = [
                                x.strip()
                                for x in decoded_info
                                if x and x.strip()
                            ]

                            if values:
                                return "\n".join(values)
                    except Exception:
                        pass

                # Try rotated images
                for angle in (90, 180, 270):
                    try:
                        if angle == 90:
                            rotated = cv2.rotate(
                                image,
                                cv2.ROTATE_90_CLOCKWISE,
                            )
                        elif angle == 180:
                            rotated = cv2.rotate(
                                image,
                                cv2.ROTATE_180,
                            )
                        else:
                            rotated = cv2.rotate(
                                image,
                                cv2.ROTATE_90_COUNTERCLOCKWISE,
                            )

                        data, points, _ = detector.detectAndDecode(rotated)

                        if data and data.strip():
                            return data.strip()
                    except Exception:
                        pass

        except Exception:
            pass

    # ---------- pyzbar / ZBar fallback ----------
    try:
        from pyzbar.pyzbar import decode
        from PIL import Image, ImageOps, ImageEnhance, ImageFilter

        original = Image.open(path).convert("RGB")
        variants = [original]

        gray = ImageOps.grayscale(original)
        variants.append(gray)

        contrast = ImageEnhance.Contrast(gray).enhance(2.5)
        variants.append(contrast)

        sharp = contrast.filter(ImageFilter.SHARPEN)
        variants.append(sharp)

        w, h = original.size

        if max(w, h) < 2000:
            up = original.resize(
                (w * 3, h * 3),
                Image.Resampling.LANCZOS,
            )
            variants.append(up)
            variants.append(ImageOps.grayscale(up))

        for img in variants:
            try:
                results = decode(img)

                values = []

                for result in results:
                    data = result.data.decode(
                        "utf-8",
                        errors="replace",
                    ).strip()

                    if data:
                        values.append(data)

                if values:
                    return "\n".join(values)

            except Exception:
                pass

    except Exception:
        pass

    return None

