FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    poppler-utils \
    libzbar0 \
    tesseract-ocr \
    tesseract-ocr-fas \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/temp /app/data

RUN echo "=== TESSERACT ===" && tesseract --list-langs

RUN echo "=== PDF TOOLS ===" && pdftoppm -v 2>&1 | head -1

CMD ["python", "-m", "bot.main"]
