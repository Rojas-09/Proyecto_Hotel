FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p static/facturas static/reportes

ENV FLASK_ENV=production

EXPOSE 5000

CMD gunicorn -w 4 -b 0.0.0.0:5000 run:app \
    --access-logfile - --error-logfile - --timeout 120
