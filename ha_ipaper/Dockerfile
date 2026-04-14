ARG BUILD_FROM=ghcr.io/hassio-addons/base:14.0.0
FROM $BUILD_FROM

# Installa Python e pip
RUN apk add --no-cache python3 py3-pip

# Copia il codice
WORKDIR /app
COPY src/ src/
COPY pyproject.toml .

# Installa dipendenze Python
RUN pip3 install --no-cache-dir --break-system-packages \
    aiohttp \
    fastapi \
    "uvicorn[standard]" \
    jinja2 \
    && pip3 install --no-cache-dir --break-system-packages -e .

# Script di avvio
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
