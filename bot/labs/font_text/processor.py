import html
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote, unquote

from PIL import Image, ImageDraw, ImageFont


def fancy_fonts(text):
    normal = text

    bold = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
        "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    )

    italic = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻"
    )

    fraktur = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷"
    )

    script = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏"
    )

    fullwidth = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
        "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９"
    )

    return {
        "Normal": normal,
        "Bold": text.translate(bold),
        "Italic": text.translate(italic),
        "Fraktur": text.translate(fraktur),
        "Script": text.translate(script),
        "Full-width": text.translate(fullwidth),
    }


def circled(text):
    result = []

    for ch in text:
        if "A" <= ch <= "Z":
            result.append(chr(0x24B6 + ord(ch) - ord("A")))
        elif "a" <= ch <= "z":
            result.append(chr(0x24D0 + ord(ch) - ord("a")))
        elif "0" <= ch <= "9":
            result.append("⓪①②③④⑤⑥⑦⑧⑨"[ord(ch) - 48])
        else:
            result.append(ch)

    return "".join(result)


def squared(text):
    result = []

    for ch in text:
        if "A" <= ch <= "Z":
            result.append(chr(0x1F130 + ord(ch) - ord("A")))
        elif "a" <= ch <= "z":
            result.append(ch.upper())
        else:
            result.append(ch)

    return "".join(result)


def reverse_text(text):
    return text[::-1]


def clean_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def count_text(text):
    chars = len(text)
    chars_no_spaces = len(re.sub(r"\s", "", text))
    words = len(text.split())
    lines = len(text.splitlines()) if text else 0

    return {
        "characters": chars,
        "characters_no_spaces": chars_no_spaces,
        "words": words,
        "lines": lines,
    }


def unicode_encode(text):
    return " ".join(f"U+{ord(ch):04X}" for ch in text)


def unicode_decode(text):
    values = re.findall(r"U\+([0-9A-Fa-f]{2,6})", text)

    if not values:
        raise ValueError("Unicode format پیدا نشد")

    return "".join(chr(int(value, 16)) for value in values)


def url_encode(text):
    return quote(text, safe="")


def url_decode(text):
    return unquote(text)


def html_encode(text):
    return html.escape(text)


def html_decode(text):
    return html.unescape(text)


def format_text(text, style):
    if style == "bold":
        return f"<b>{html.escape(text)}</b>"

    if style == "italic":
        return f"<i>{html.escape(text)}</i>"

    if style == "underline":
        return f"<u>{html.escape(text)}</u>"

    if style == "strike":
        return f"<s>{html.escape(text)}</s>"

    if style == "spoiler":
        return f"<tg-spoiler>{html.escape(text)}</tg-spoiler>"

    if style == "code":
        return f"<code>{html.escape(text)}</code>"

    if style == "quote":
        return f"<blockquote>{html.escape(text)}</blockquote>"

    return html.escape(text)


def text_to_image(
    text,
    output,
    font_size=42,
    padding=50,
    line_spacing=15,
    align="left",
):
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]

    font_path = next(
        (x for x in font_candidates if Path(x).exists()),
        None,
    )

    if not font_path:
        raise RuntimeError("فونت مناسب پیدا نشد")

    font = ImageFont.truetype(font_path, font_size)

    lines = text.splitlines() or [""]

    dummy = Image.new("RGB", (100, 100), "white")
    draw = ImageDraw.Draw(dummy)

    widths = []
    heights = []

    for line in lines:
        box = draw.textbbox((0, 0), line or " ", font=font)
        widths.append(box[2] - box[0])
        heights.append(box[3] - box[1])

    width = max(widths, default=100) + padding * 2
    height = sum(heights) + line_spacing * max(0, len(lines) - 1) + padding * 2

    image = Image.new("RGB", (max(width, 200), max(height, 100)), "white")
    draw = ImageDraw.Draw(image)

    y = padding

    for line, line_width, line_height in zip(lines, widths, heights):
        if align == "center":
            x = (image.width - line_width) // 2
        elif align == "right":
            x = image.width - padding - line_width
        else:
            x = padding

        draw.text((x, y), line, fill="black", font=font)
        y += line_height + line_spacing

    image.save(output, "PNG")
    return output
