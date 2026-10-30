"""Point d'entrée : `python main.py`"""
import logging

import config
from core.bot import Bot


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    missing = config.missing_settings()
    if missing:
        raise SystemExit(f"❌ Variables manquantes dans le .env : {', '.join(missing)}")

    Bot().run(config.DISCORD_TOKEN, log_handler=None)  # logging déjà configuré ci-dessus


if __name__ == "__main__":
    main()
