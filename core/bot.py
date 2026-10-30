"""Classe Bot : charge automatiquement tous les cogs du dossier cogs/."""
import logging
from pathlib import Path

import discord
from discord.ext import commands

import config
from services.pterodactyl import PterodactylClient

log = logging.getLogger(__name__)

COGS_DIR = Path(__file__).resolve().parent.parent / "cogs"


class Bot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=config.COMMAND_PREFIX, intents=intents)

        # Services partagés : accessibles dans les cogs via `self.bot.ptero`
        self.ptero = PterodactylClient(config.PTERODACTYL_URL, config.PTERODACTYL_API_KEY)

    async def setup_hook(self) -> None:
        await self.load_all_cogs()
        await self.tree.sync()

    async def load_all_cogs(self) -> None:
        """Charge chaque fichier cogs/*.py (sauf ceux qui commencent par '_')."""
        for path in sorted(COGS_DIR.glob("*.py")):
            if path.stem.startswith("_") or path.stem == "__init__":
                continue
            extension = f"cogs.{path.stem}"
            try:
                await self.load_extension(extension)
                log.info("Cog chargé : %s", extension)
            except Exception:
                # Un cog cassé ne doit pas empêcher le bot de démarrer
                log.exception("Impossible de charger le cog %s", extension)

    async def on_ready(self) -> None:
        log.info("✅ Connecté en tant que %s (ID: %s)", self.user, self.user.id)

    async def close(self) -> None:
        await self.ptero.close()
        await super().close()
