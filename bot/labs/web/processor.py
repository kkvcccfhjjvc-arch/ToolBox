from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
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

    # Remove duplicates while preserving order
    seen = set()
    result = []

    for text in paragraphs:
        if text not in seen:
            seen.add(text)
            result.append(text)

    return title, "\n\n".join(result[:100])


def wikipedia_search(query):
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
        headers=HEADERS,
        timeout=15,
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
    response = requests.get(
        "https://en.wikipedia.org/api/rest_v1/page/summary/"
        + requests.utils.quote(query),
        headers=HEADERS,
        timeout=15,
    )

    if response.status_code != 200:
        raise ValueError("صفحه Wikipedia پیدا نشد.")

    data = response.json()

    return {
        "title": data.get("title", query),
        "extract": data.get(
            "extract",
            "توضیحی پیدا نشد.",
        ),
        "url": (
            data.get("content_urls", {})
            .get("desktop", {})
            .get("page", "")
        ),
    }


def web_search(query):
    response = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers=HEADERS,
        timeout=15,
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

    return results


def get_weather(city):
    response = requests.get(
        f"https://wttr.in/{requests.utils.quote(city)}",
        params={"format": "j1"},
        headers=HEADERS,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    current = data["current_condition"][0]

    return {
        "city": city,
        "temp": current.get("temp_C"),
        "feels": current.get("FeelsLikeC"),
        "humidity": current.get("humidity"),
        "wind": current.get("windspeedKmph"),
        "description": (
            current.get("weatherDesc", [{}])[0]
            .get("value", "")
        ),
    }


def get_news():
    response = requests.get(
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        headers=HEADERS,
        timeout=15,
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


def dns_info(host):
    host = host.strip()

    if re.match(r"^https?://", host, re.I):
        host = urlparse(host).hostname or host

    result = {
        "host": host,
        "ipv4": [],
        "aliases": [],
    }

    try:
        data = socket.gethostbyname_ex(host)

        result["aliases"] = data[1]
        result["ipv4"] = data[2]

    except Exception:
        pass

    return result


def webpage_to_pdf(url):
    title, text = article_reader(url)

    if not text:
        raise ValueError(
            "متن قابل استخراج از صفحه پیدا نشد."
        )

    output = new_file(".pdf")

    styles = getSampleStyleSheet()

    body = styles["BodyText"]
    body.fontSize = 10
    body.leading = 15
    body.alignment = TA_LEFT

    heading = styles["Heading1"]

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    story = []

    if title:
        story.append(
            Paragraph(
                escape(title),
                heading,
            )
        )
        story.append(Spacer(1, 15))

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        story.append(
            Paragraph(
                escape(paragraph),
                body,
            )
        )
        story.append(Spacer(1, 8))

    doc.build(story)

    return output
