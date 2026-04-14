FROM python:3.12-alpine

# Dipendenze di sistema
RUN apk add --no-cache bash curl

# Installa dipendenze Python
RUN pip install --no-cache-dir \
    aiohttp \
    fastapi \
    "uvicorn[standard]" \
    jinja2 \
    pyyaml

# Copia il codice
WORKDIR /app
COPY src/ src/
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Script di avvio
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
