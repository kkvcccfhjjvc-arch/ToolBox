import base64
import html
import json
import re
import uuid
from urllib.parse import quote, unquote
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None


def json_format(text):
    data = json.loads(text)
    return json.dumps(data, ensure_ascii=False, indent=2)


def json_minify(text):
    data = json.loads(text)
    return json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def json_validate(text):
    json.loads(text)
    return True


def json_to_yaml(text):
    if yaml is None:
        raise ValueError("PyYAML نصب نیست.")
    data = json.loads(text)
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
    )


def yaml_to_json(text):
    if yaml is None:
        raise ValueError("PyYAML نصب نیست.")
    data = yaml.safe_load(text)
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )


def json_to_csv(text):
    import csv
    import io

    data = json.loads(text)

    if not isinstance(data, list):
        data = [data]

    if not data:
        return ""

    fields = set()

    for item in data:
        if isinstance(item, dict):
            fields.update(item.keys())

    fields = list(fields)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fields,
        extrasaction="ignore",
    )

    writer.writeheader()

    for item in data:
        if isinstance(item, dict):
            writer.writerow(item)

    return output.getvalue()


def csv_to_json(text):
    import csv
    import io

    reader = csv.DictReader(
        io.StringIO(text.strip())
    )

    rows = list(reader)

    return json.dumps(
        rows,
        ensure_ascii=False,
        indent=2,
    )


def regex_test(pattern, text):
    regex = re.compile(pattern)

    matches = []

    for match in regex.finditer(text):
        matches.append({
            "match": match.group(0),
            "start": match.start(),
            "end": match.end(),
            "groups": list(match.groups()),
        })

    return matches


def text_diff(a, b):
    import difflib

    diff = difflib.unified_diff(
        a.splitlines(),
        b.splitlines(),
        fromfile="text1",
        tofile="text2",
        lineterm="",
    )

    return "\n".join(diff)


def base64_encode(text):
    return base64.b64encode(
        text.encode("utf-8")
    ).decode("ascii")


def base64_decode(text):
    return base64.b64decode(
        text.strip()
    ).decode("utf-8")


def url_encode(text):
    return quote(text, safe="")


def url_decode(text):
    return unquote(text)


def html_encode(text):
    return html.escape(text)


def html_decode(text):
    return html.unescape(text)


def number_convert(value, source, target):
    value = value.strip().lower()

    bases = {
        "binary": 2,
        "decimal": 10,
        "hex": 16,
        "octal": 8,
    }

    number = int(value, bases[source])

    if target == "decimal":
        return str(number)

    if target == "binary":
        return bin(number)[2:]

    if target == "hex":
        return hex(number)[2:].upper()

    if target == "octal":
        return oct(number)[2:]

    raise ValueError("نوع تبدیل نامعتبر است.")


def unix_to_datetime(timestamp):
    dt = datetime.fromtimestamp(
        int(timestamp),
        timezone.utc,
    )

    return dt.strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def datetime_to_unix(text):
    dt = datetime.fromisoformat(
        text.replace("Z", "+00:00")
    )

    return str(int(dt.timestamp()))


def color_convert(value):
    value = value.strip().lstrip("#")

    if len(value) != 6:
        raise ValueError(
            "رنگ باید به شکل #RRGGBB باشد."
        )

    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)

    return {
        "hex": f"#{value.upper()}",
        "rgb": f"rgb({r}, {g}, {b})",
        "decimal": str(
            (r << 16) + (g << 8) + b
        ),
    }


def generate_uuid():
    return str(uuid.uuid4())


def jwt_decode(token):
    parts = token.strip().split(".")

    if len(parts) != 3:
        raise ValueError(
            "JWT معتبر نیست؛ باید 3 بخش داشته باشد."
        )

    def decode_part(part):
        padding = "=" * (-len(part) % 4)
        raw = base64.urlsafe_b64decode(
            part + padding
        )
        return json.loads(
            raw.decode("utf-8")
        )

    return {
        "header": decode_part(parts[0]),
        "payload": decode_part(parts[1]),
        "signature": parts[2],
    }


def cron_explain(expression):
    parts = expression.strip().split()

    if len(parts) != 5:
        raise ValueError(
            "Cron باید دقیقاً 5 بخش داشته باشد."
        )

    names = [
        "دقیقه",
        "ساعت",
        "روز ماه",
        "ماه",
        "روز هفته",
    ]

    return "\n".join(
        f"• {names[i]}: {parts[i]}"
        for i in range(5)
    )
