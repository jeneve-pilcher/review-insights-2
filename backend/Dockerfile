FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download NLTK data and the zero-shot classification model at build
# time so the first real request isn't slow/network-dependent in production.
RUN python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('stopwords')"
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33')"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
