"""Entrypoint for the mimamori night-routine monitoring daemon."""

from __future__ import annotations

import asyncio
import logging

from mimamori.app import MimamoriApp
from mimamori.config import Config


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = Config.load()
    app = MimamoriApp(config)
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
