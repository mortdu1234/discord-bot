"""Commande d'administration : menu de sélection de rôles auto-attribuables."""
from __future__ import annotations

import discord
from discord.ext import commands

from config import ROLE_CHOICES
from views.role_selection import RoleSelectionView, ensure_roles_exist


class RoleCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ServerRoleSelection")
    @commands.has_permissions(administrator=True)
    async def role_selection(self, ctx: commands.Context):
        """!ServerRoleSelection — (Admin) Crée les rôles manquants, puis affiche le menu de sélection."""
        await ctx.message.delete()

        async with ctx.typing():
            # Crée automatiquement sur le serveur tout rôle défini dans la config
            # qui n'existe pas encore, avant d'afficher les boutons.
            roles = await ensure_roles_exist(ctx.guild)

        embed = discord.Embed(
            title="Sélection de rôles",
            description="Clique sur un bouton pour obtenir ou retirer un rôle.\nTu peux en avoir plusieurs !",
            color=0x5865F2,
        )
        for role_info in ROLE_CHOICES:
            embed.add_field(name=role_info.name, value=role_info.description, inline=False)
        embed.set_footer(text="Cliquer à nouveau sur un rôle déjà obtenu le retire.")

        await ctx.send(embed=embed, view=RoleSelectionView())
        print(f"[RoleMenu] Rôles vérifiés/créés sur « {ctx.guild.name} » : {[r.name for r in roles]}")

    @role_selection.error
    async def role_selection_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.", delete_after=5)


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleCommands(bot))
