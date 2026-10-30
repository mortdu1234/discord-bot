"""Boutons Démarrer / Arrêter / Redémarrer affichés sous !status."""
import discord

from services.pterodactyl import PterodactylClient

ACTION_LABELS = {"start": "démarrage", "stop": "arrêt", "restart": "redémarrage"}


class PowerButton(discord.ui.Button):
    def __init__(self, label: str, action: str, style: discord.ButtonStyle,
                 ptero: PterodactylClient, identifier: str):
        super().__init__(label=label, style=style)
        self.action = action
        self.ptero = ptero
        self.identifier = identifier

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        success = await self.ptero.send_power_action(self.identifier, self.action)
        if success:
            if self.action in ("start", "restart"):
                # Les cogs intéressés (ex. notifications) écoutent `on_server_power`
                interaction.client.dispatch("server_power", self.identifier, self.action, interaction.user)
            await interaction.followup.send(
                f"✅ Commande de **{ACTION_LABELS.get(self.action, self.action)}** envoyée avec succès !"
            )
        else:
            await interaction.followup.send("❌ Échec de l'envoi de la commande.")

        for item in self.view.children:
            item.disabled = True
        await interaction.message.edit(view=self.view)


class ServerControlView(discord.ui.View):
    def __init__(self, ptero: PterodactylClient, identifier: str, is_running: bool):
        super().__init__(timeout=120)
        if is_running:
            self.add_item(PowerButton("🔁 Redémarrer", "restart", discord.ButtonStyle.primary, ptero, identifier))
            self.add_item(PowerButton("⏹️ Arrêter", "stop", discord.ButtonStyle.danger, ptero, identifier))
        else:
            self.add_item(PowerButton("▶️ Démarrer", "start", discord.ButtonStyle.success, ptero, identifier))
