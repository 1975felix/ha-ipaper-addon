ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip bash

WORKDIR /app
COPY src/ src/
COPY pyproject.toml .

RUN pip3 install --no-cache-dir --break-system-packages \
    aiohttp \
    fastapi \
    "uvicorn[standard]" \
    jinja2 \
    pyyaml \
    && pip3 install --no-cache-dir --break-system-packages -e .

COPY rootfs/ /
