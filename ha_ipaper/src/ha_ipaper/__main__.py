"""
ha_ipaper - entry point
Uso: python -m ha_ipaper -config config.yaml
"""
from __future__ import annotations

import argparse
import logging
import logging.config
import sys

import uvicorn

from .config import load_config
from .server import create_app


def main():
    parser = argparse.ArgumentParser(description="HA-IPaper filtered fork")
    parser.add_argument(
        "-config",
        default="config.yaml",
        help="Percorso al file config.yaml (default: config.yaml)",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    # Configura il logging
    if cfg.loggercfg:
        logging.config.dictConfig(cfg.loggercfg)
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(module)26s: %(levelname)-8s %(message)s",
        )

    logger = logging.getLogger(__name__)
    logger.info("Starting HA-IPaper (filtered fork)")

    app = create_app(cfg)

    uvicorn.run(
        app,
        host=cfg.server.bind_addr,
        port=cfg.server.bind_port,
        log_level="debug" if cfg.server.debug else "info",
    )


if __name__ == "__main__":
    main()
