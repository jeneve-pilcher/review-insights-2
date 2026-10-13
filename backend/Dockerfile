FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch first. The default Linux wheel bundles GPU libraries (several GB) that a web host never uses,
# which makes builds slow and the image huge. requirements.txt's "torch>=2.2" is then already satisfied.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download NLTK data and the zero-shot classification model at build
# time so the first real request isn't slow/network-dependent in production.
RUN python -c "import nltk; nltk.download('vader_lexicon')"
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='MoritzLaurer/deberta-v3-xsmall-zeroshot-v1.1-all-33')"

EXPOSE 8000

# Hosts such as Render tell the app which port to use through $PORT; locally it stays 8000.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
