"""Vue avec boutons pour démarrer/arrêter/redémarrer un serveur Minecraft."""
from __future__ import annotations

import discord

from services.server_service import ServerService

ACTION_LABELS = {"start": "démarrage", "stop": "arrêt", "restart": "redémarrage"}


class PowerButton(discord.ui.Button):
    def __init__(
        self,
        label: str,
        action: str,
        style: discord.ButtonStyle,
        identifier: str,
        server_service: ServerService,
    ):
        super().__init__(label=label, style=style)
        self.action = action
        self.identifier = identifier
        self.server_service = server_service

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        success = await self.server_service.set_power(self.identifier, self.action)

        if success:
            await interaction.followup.send(
                f"✅ Commande de **{ACTION_LABELS.get(self.action, self.action)}** envoyée avec succès !"
            )
        else:
            await interaction.followup.send("❌ Échec de l'envoi de la commande.")

        for item in self.view.children:
            item.disabled = True
        await interaction.message.edit(view=self.view)


class ServerControlView(discord.ui.View):
    def __init__(self, identifier: str, current_state: str, server_service: ServerService):
        super().__init__(timeout=120)

        if "En ligne" in current_state:
            self.add_item(PowerButton("🔁 Redémarrer", "restart", discord.ButtonStyle.primary, identifier, server_service))
            self.add_item(PowerButton("⏹️ Arrêter", "stop", discord.ButtonStyle.danger, identifier, server_service))
        else:
            self.add_item(PowerButton("▶️ Démarrer", "start", discord.ButtonStyle.success, identifier, server_service))
