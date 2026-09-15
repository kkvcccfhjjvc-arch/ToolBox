import ast
import operator
import random
import secrets
import string
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# =========================
# Calculator
# =========================

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate(expression):
    expression = expression.strip()

    if len(expression) > 200:
        raise ValueError("عبارت خیلی طولانی است.")

    tree = ast.parse(expression, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("فقط اعداد مجاز هستند.")

        if isinstance(node, ast.BinOp):
            op = type(node.op)

            if op not in _ALLOWED_OPS:
                raise ValueError("عملگر مجاز نیست.")

            left = evaluate(node.left)
            right = evaluate(node.right)

            if op is ast.Pow and abs(right) > 100:
                raise ValueError("توان بیش از حد بزرگ است.")

            return _ALLOWED_OPS[op](left, right)

        if isinstance(node, ast.UnaryOp):
            op = type(node.op)

            if op not in _ALLOWED_OPS:
                raise ValueError("عملگر مجاز نیست.")

            return _ALLOWED_OPS[op](
                evaluate(node.operand)
            )

        raise ValueError("عبارت نامعتبر است.")

    result = evaluate(tree)

    if isinstance(result, float):
        if result.is_integer():
            return str(int(result))

        return f"{result:.12g}"

    return str(result)


# =========================
# Unit Converter
# =========================

UNIT_GROUPS = {
    "length": {
        "m": 1,
        "km": 1000,
        "cm": 0.01,
        "mm": 0.001,
        "mile": 1609.344,
        "yard": 0.9144,
        "foot": 0.3048,
        "inch": 0.0254,
    },
    "weight": {
        "kg": 1,
        "g": 0.001,
        "mg": 0.000001,
        "lb": 0.45359237,
        "oz": 0.028349523125,
    },
    "volume": {
        "l": 1,
        "ml": 0.001,
        "m3": 1000,
        "gallon": 3.785411784,
        "cup": 0.2365882365,
    },
    "time": {
        "s": 1,
        "min": 60,
        "h": 3600,
        "day": 86400,
    },
}


def convert_unit(value, from_unit, to_unit):
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()

    for group in UNIT_GROUPS.values():
        if from_unit in group and to_unit in group:
            base = float(value) * group[from_unit]
            result = base / group[to_unit]
            return f"{result:.12g}"

    raise ValueError(
        "این دو واحد متعلق به یک گروه نیستند."
    )


def convert_temperature(value, from_unit, to_unit):
    value = float(value)
    from_unit = from_unit.upper()
    to_unit = to_unit.upper()

    if from_unit == "C":
        celsius = value
    elif from_unit == "F":
        celsius = (value - 32) * 5 / 9
    elif from_unit == "K":
        celsius = value - 273.15
    else:
        raise ValueError("واحد دما باید C، F یا K باشد.")

    if to_unit == "C":
        result = celsius
    elif to_unit == "F":
        result = celsius * 9 / 5 + 32
    elif to_unit == "K":
        result = celsius + 273.15
    else:
        raise ValueError("واحد دما باید C، F یا K باشد.")

    return f"{result:.12g}"


# =========================
# Password
# =========================

def generate_password(
    length=16,
    use_upper=True,
    use_lower=True,
    use_digits=True,
    use_symbols=True,
):
    length = int(length)

    if length < 4 or length > 128:
        raise ValueError(
            "طول رمز باید بین 4 تا 128 باشد."
        )

    pools = []

    if use_upper:
        pools.append(string.ascii_uppercase)

    if use_lower:
        pools.append(string.ascii_lowercase)

    if use_digits:
        pools.append(string.digits)

    if use_symbols:
        pools.append("!@#$%^&*_-+=")

    if not pools:
        raise ValueError("حداقل یک نوع کاراکتر انتخاب کنید.")

    chars = [
        secrets.choice(pool)
        for pool in pools
    ]

    all_chars = "".join(pools)

    chars.extend(
        secrets.choice(all_chars)
        for _ in range(length - len(chars))
    )

    random.SystemRandom().shuffle(chars)

    return "".join(chars)


# =========================
# Random
# =========================

def random_number(minimum, maximum):
    return secrets.randbelow(
        maximum - minimum + 1
    ) + minimum


def random_choice(items):
    items = [
        item.strip()
        for item in items
        if item.strip()
    ]

    if not items:
        raise ValueError("لیست خالی است.")

    return secrets.choice(items)


# =========================
# Number Converter
# =========================

def number_convert(value, source, target):
    bases = {
        "binary": 2,
        "decimal": 10,
        "hex": 16,
        "octal": 8,
    }

    source = source.lower()
    target = target.lower()

    if source not in bases or target not in bases:
        raise ValueError("نوع عدد نامعتبر است.")

    number = int(value.strip(), bases[source])

    if target == "binary":
        return bin(number)[2:]

    if target == "decimal":
        return str(number)

    if target == "hex":
        return hex(number)[2:].upper()

    if target == "octal":
        return oct(number)[2:]

    raise ValueError("نوع تبدیل نامعتبر است.")


# =========================
# Timezone
# =========================

def timezone_now(zone):
    try:
        dt = datetime.now(
            ZoneInfo(zone)
        )
    except Exception:
        raise ValueError(
            "Timezone پیدا نشد.\n"
            "مثال: Asia/Tehran"
        )

    return dt.strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )


def timezone_convert(zone_from, zone_to):
    try:
        now = datetime.now(
            ZoneInfo(zone_from)
        )
        converted = now.astimezone(
            ZoneInfo(zone_to)
        )
    except Exception:
        raise ValueError(
            "Timezone نامعتبر است."
        )

    return converted.strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )


# =========================
# Stopwatch helper
# =========================

def format_seconds(seconds):
    seconds = int(seconds)

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []

    if days:
        parts.append(f"{days} روز")

    if hours:
        parts.append(f"{hours} ساعت")

    if minutes:
        parts.append(f"{minutes} دقیقه")

    parts.append(f"{seconds} ثانیه")

    return " و ".join(parts)
