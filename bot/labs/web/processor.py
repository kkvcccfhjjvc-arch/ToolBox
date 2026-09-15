from pathlib import Path
from urllib.parse import urlparse, parse_qs
import socket
import re
import uuid

import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from xml.sax.saxutils import escape


TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Android 15; Mobile) "
        "AppleWebKit/537.36 Chrome/140 Safari/537.36"
    )
}


def new_file(ext=".pdf"):
    return TEMP_DIR / f"web_{uuid.uuid4().hex}{ext}"


def fetch_url(url, timeout=15):
    url = url.strip()

    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=timeout,
        allow_redirects=True,
    )

    response.raise_for_status()
    return response


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def url_info(url):
    parsed = urlparse(
        url if re.match(r"^https?://", url, re.I)
        else "https://" + url
    )

    host = parsed.hostname or ""

    try:
        ip = socket.gethostbyname(host)
    except Exception:
        ip = "نامشخص"

    return {
        "scheme": parsed.scheme,
        "host": host,
        "port": parsed.port or (
            443 if parsed.scheme == "https" else 80
        ),
        "path": parsed.path or "/",
        "query": parsed.query,
        "fragment": parsed.fragment,
        "ip": ip,
    }


def parse_url(url):
    parsed = urlparse(
        url if re.match(r"^https?://", url, re.I)
        else "https://" + url
    )

    params = parse_qs(parsed.query)

    return {
        "scheme": parsed.scheme,
        "username": parsed.username or "",
        "password": parsed.password or "",
        "hostname": parsed.hostname or "",
        "port": parsed.port or "",
        "path": parsed.path or "/",
        "query": parsed.query,
        "fragment": parsed.fragment,
        "parameters": params,
    }


def link_preview(url):
    response = fetch_url(url)

    soup = BeautifulSoup(response.text, "html.parser")

    title = ""
    description = ""
    image = ""

    og_title = soup.find(
        "meta",
        attrs={"property": "og:title"},
    )

    og_description = soup.find(
        "meta",
        attrs={"property": "og:description"},
    )

    og_image = soup.find(
        "meta",
        attrs={"property": "og:image"},
    )

    if og_title:
        title = og_title.get("content", "")

    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)

    if og_description:
        description = og_description.get("content", "")

    if not description:
        meta = soup.find(
            "meta",
            attrs={"name": "description"},
        )
        if meta:
            description = meta.get("content", "")

    if og_image:
        image = og_image.get("content", "")

    return {
        "url": response.url,
        "status": response.status_code,
        "content_type": response.headers.get(
            "content-type",
            ""
        ),
        "title": clean_text(title),
        "description": clean_text(description),
        "image": image,
    }


def article_reader(url):
    response = fetch_url(url)

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "header",
            "form",
            "aside",
        ]
    ):
        tag.decompose()

    title = ""

    if soup.title:
        title = clean_text(
            soup.title.get_text(" ", strip=True)
        )

    article = (
        soup.find("article")
        or soup.find("main")
        or soup.body
    )

    if not article:
        return title, ""

    paragraphs = []

    for p in article.find_all(
        ["p", "h1", "h2", "h3"]
    ):
        text = clean_text(
            p.get_text(" ", strip=True)
        )

        if len(text) >= 30:
            paragraphs.append(text)

    seen = set()
    result = []

    for text in paragraphs:
        if text not in seen:
            seen.add(text)
            result.append(text)

    return title, "\n\n".join(result[:100])


# =========================================================
# WIKIPEDIA
# =========================================================

def wikipedia_search(query):
    query = query.strip()

    if not query:
        return []

    response = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": 5,
        },
        headers={
            **HEADERS,
            "Accept": "application/json",
        },
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("query", {}).get(
        "search", []
    ):
        title = item.get("title", "")

        snippet = BeautifulSoup(
            item.get("snippet", ""),
            "html.parser",
        ).get_text(" ", strip=True)

        results.append({
            "title": title,
            "snippet": snippet,
            "url": (
                "https://en.wikipedia.org/wiki/"
                + title.replace(" ", "_")
            ),
        })

    return results


def wikipedia_summary(query):
    query = query.strip()

    # اول جستجوی API معمولی
    results = wikipedia_search(query)

    if not results:
        return None

    # بهترین نتیجه را انتخاب کن
    title = results[0]["title"]

    response = requests.get(
        "https://en.wikipedia.org/api/rest_v1/page/summary/"
        + requests.utils.quote(title),
        headers={
            **HEADERS,
            "Accept": "application/json",
        },
        timeout=20,
    )

    if response.status_code != 200:
        return {
            "title": title,
            "extract": results[0].get(
                "snippet",
                "توضیحی پیدا نشد.",
            ),
            "url": results[0]["url"],
        }

    data = response.json()

    return {
        "title": data.get("title", title),
        "extract": data.get(
            "extract",
            results[0].get(
                "snippet",
                "توضیحی پیدا نشد.",
            ),
        ),
        "url": (
            data.get("content_urls", {})
            .get("desktop", {})
            .get("page", "")
        ) or results[0]["url"],
    }


# =========================================================
# WEB SEARCH
# =========================================================

def web_search(query):
    query = query.strip()

    if not query:
        return []

    # موتور اول: DuckDuckGo HTML
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=HEADERS,
            timeout=20,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        results = []

        for item in soup.select(".result")[:8]:
            a = item.select_one(".result__a")
            snippet = item.select_one(
                ".result__snippet"
            )

            if not a:
                continue

            href = a.get("href", "")

            title = clean_text(
                a.get_text(" ", strip=True)
            )

            text = clean_text(
                snippet.get_text(" ", strip=True)
                if snippet
                else ""
            )

            if title:
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": text,
                })

        if results:
            return results

    except Exception:
        pass

    # Fallback: Bing HTML
    try:
        response = requests.get(
            "https://www.google.com/search",
            params={
                "q": query,
                "num": 8,
            },
            headers=HEADERS,
            timeout=20,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        results = []

        for block in soup.select("div.MjjYud")[:8]:
            a = block.select_one("a")
            h3 = block.select_one("h3")

            if not a or not h3:
                continue

            href = a.get("href", "")

            if not href.startswith("http"):
                continue

            title = clean_text(
                h3.get_text(" ", strip=True)
            )

            parent_text = clean_text(
                block.get_text(" ", strip=True)
            )

            if title:
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": parent_text,
                })

        return results

    except Exception:
        return []


# =========================================================
# WEATHER - OPEN METEO
# =========================================================

def get_weather(city):
    city = city.strip()

    if not city:
        raise ValueError("نام شهر وارد نشده است.")

    # پیدا کردن مختصات شهر
    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city,
            "count": 1,
            "language": "fa",
            "format": "json",
        },
        headers=HEADERS,
        timeout=20,
    )

    geo_response.raise_for_status()

    geo_data = geo_response.json()

    locations = geo_data.get("results", [])

    if not locations:
        # دوباره با زبان انگلیسی امتحان کن
        geo_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            headers=HEADERS,
            timeout=20,
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()
        locations = geo_data.get("results", [])

    if not locations:
        raise ValueError(
            f"شهر «{city}» پیدا نشد."
        )

    location = locations[0]

    latitude = location["latitude"]
    longitude = location["longitude"]

    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "wind_speed_10m,"
                "weather_code"
            ),
            "timezone": "auto",
        },
        headers=HEADERS,
        timeout=20,
    )

    weather_response.raise_for_status()

    weather_data = weather_response.json()
    current = weather_data.get("current", {})

    code = current.get("weather_code")

    descriptions = {
        0: "صاف",
        1: "عمدتاً صاف",
        2: "نیمه ابری",
        3: "ابری",
        45: "مه",
        48: "مه یخ‌زن",
        51: "نم‌نم باران",
        53: "باران خفیف",
        55: "باران",
        61: "باران خفیف",
        63: "باران متوسط",
        65: "باران شدید",
        71: "برف خفیف",
        73: "برف متوسط",
        75: "برف شدید",
        80: "رگبار خفیف",
        81: "رگبار متوسط",
        82: "رگبار شدید",
        95: "رعدوبرق",
        96: "رعدوبرق و تگرگ",
        99: "رعدوبرق و تگرگ شدید",
    }

    return {
        "city": location.get("name", city),
        "temp": current.get("temperature_2m"),
        "feels": current.get("apparent_temperature"),
        "humidity": current.get(
            "relative_humidity_2m"
        ),
        "wind": current.get("wind_speed_10m"),
        "description": descriptions.get(
            code,
            "نامشخص",
        ),
    }


# =========================================================
# NEWS
# =========================================================

def get_news():
    response = requests.get(
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.content,
        "xml",
    )

    results = []

    for item in soup.find_all("item")[:10]:
        title = clean_text(
            item.title.get_text()
            if item.title
            else ""
        )

        link = (
            item.link.get_text(strip=True)
            if item.link
            else ""
        )

        pub = clean_text(
            item.pubDate.get_text()
            if item.pubDate
            else ""
        )

        if title:
            results.append({
                "title": title,
                "url": link,
                "date": pub,
            })

    return results


# =========================================================
# WEBPAGE -> PDF
# =========================================================

def webpage_to_pdf(url):
    response = fetch_url(url)

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
        ]
    ):
        tag.decompose()

    title = (
        soup.title.get_text(
            " ",
            strip=True,
        )
        if soup.title
        else url
    )

    text = clean_text(
        soup.get_text(" ", strip=True)
    )

    output = new_file(".pdf")

    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
    )

    story = [
        Paragraph(
            escape(title),
            styles["Title"],
        ),
        Spacer(1, 12),
        Paragraph(
            escape(text[:30000]),
            styles["BodyText"],
        ),
    ]

    doc.build(story)

    return output


# =========================================================
# URL PARSER HELPERS
# =========================================================

def dns_info(host):
    host = host.strip()

    if not host:
        raise ValueError("دامنه وارد نشده است.")

    try:
        addresses = socket.getaddrinfo(
            host,
            None,
        )

        ips = sorted(
            {
                item[4][0]
                for item in addresses
            }
        )

        return ips

    except Exception:
        return []


def url_unquote(value):
    from urllib.parse import unquote
    return unquote(value)
