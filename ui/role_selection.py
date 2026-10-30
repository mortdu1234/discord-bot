"""Menu persistant de sélection de rôles (survit aux redémarrages du bot)."""
import discord

import config


class RoleButton(discord.ui.Button):
    def __init__(self, role_info: dict):
        super().__init__(
            label=role_info["name"],
            style=discord.ButtonStyle.secondary,
            custom_id=f"role_{role_info['name']}",
        )
        self.role_name = role_info["name"]

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.role_name)
        if role is None:
            await interaction.response.send_message(
                f"❌ Le rôle **{self.role_name}** n'existe pas sur ce serveur. Crée-le d'abord !",
                ephemeral=True,
            )
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"✅ Rôle **{self.role_name}** retiré.", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"✅ Rôle **{self.role_name}** ajouté.", ephemeral=True)


class RoleSelectionView(discord.ui.View):
    def __init__(self, roles_choices=config.ROLE_SERVER_CHOICES):
        super().__init__(timeout=None)  # persistant : pas de timeout
        for role_info in roles_choices:
            self.add_item(RoleButton(role_info))
