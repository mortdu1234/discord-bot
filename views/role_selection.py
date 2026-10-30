"""
Vue de sélection de rôles auto-attribuables.

Fonctionnalité clé : si un rôle défini dans config.ROLE_CHOICES n'existe pas
encore sur le serveur, il est créé automatiquement (voir ensure_roles_exist),
au lieu de simplement afficher une erreur à l'utilisateur.
"""
from __future__ import annotations

import discord

from config import ROLE_CHOICES, RoleChoice


async def ensure_roles_exist(guild: discord.Guild) -> list[discord.Role]:
    """
    Vérifie que chaque rôle de ROLE_CHOICES existe sur le serveur.
    Crée les rôles manquants (avec leur couleur définie dans la config) et
    retourne la liste complète des rôles Discord correspondants.
    """
    roles: list[discord.Role] = []
    for choice in ROLE_CHOICES:
        role = discord.utils.get(guild.roles, name=choice.name)
        if role is None:
            role = await guild.create_role(
                name=choice.name,
                color=discord.Color(choice.color),
                reason="Création automatique par le bot (menu de sélection de rôles)",
            )
        roles.append(role)
    return roles


class RoleButton(discord.ui.Button):
    def __init__(self, role_info: RoleChoice):
        super().__init__(
            label=role_info.name,
            style=discord.ButtonStyle.secondary,
            custom_id=f"role_{role_info.name}",
        )
        self.role_name = role_info.name

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        role = discord.utils.get(guild.roles, name=self.role_name)
        if role is None:
            # Filet de sécurité : le rôle a pu être supprimé entre la création
            # du menu et le clic sur le bouton. On le recrée à la volée.
            role = await guild.create_role(
                name=self.role_name,
                reason="Recréation automatique (rôle manquant lors de l'attribution)",
            )

        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"✅ Rôle **{self.role_name}** retiré.", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"✅ Rôle **{self.role_name}** ajouté.", ephemeral=True)


class RoleSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistant, pas de timeout
        for role_info in ROLE_CHOICES:
            self.add_item(RoleButton(role_info))
