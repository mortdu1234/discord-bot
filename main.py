"""
Point d'entrée du bot Discord.

Architecture :
- config.py               → variables d'environnement, rôles, IPs
- services/pterodactyl.py → appels bruts à l'API Pterodactyl
- services/minecraft.py   → ping direct des serveurs Minecraft (mcstatus)
- services/server_service.py → couche métier qui combine les deux ci-dessus
- views/                  → boutons Discord (contrôle serveur, sélection de rôles)
- cogs/                   → commandes Discord (!status, !servers, !whitelist, !ServerRoleSelection)
"""
from __future__ import annotations

import discord
from discord.ext import commands

import config
from services.pterodactyl import PterodactylClient
from services.server_service import ServerService
from views.role_selection import RoleSelectionView


class MinecraftBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=config.COMMAND_PREFIX, intents=intents)

        self.ptero_client = PterodactylClient()
        self.server_service = ServerService(self.ptero_client)

    async def setup_hook(self):
        # Session aiohttp ouverte une seule fois (au lieu d'une par requête).
        await self.ptero_client.start()

        # Vue persistante : nécessaire pour que les boutons de rôles continuent
        # de fonctionner après un redémarrage du bot.
        self.add_view(RoleSelectionView())

        await self.load_extension("cogs.server_commands")
        await self.load_extension("cogs.role_commands")

    async def close(self):
        await self.ptero_client.close()
        await super().close()


bot = MinecraftBot()


@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user} (ID: {bot.user.id})")


if __name__ == "__main__":
    config.validate_config()
    bot.run(config.DISCORD_TOKEN)
