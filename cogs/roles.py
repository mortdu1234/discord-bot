"""Menu de sélection de rôles par boutons."""
import discord
from discord.ext import commands

import config
from core.utils import safe_delete
from ui.role_selection import RoleSelectionView


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Réenregistre la vue persistante pour que les anciens boutons refonctionnent après un redémarrage
        self.bot.add_view(RoleSelectionView())

    @commands.command(name="ServerRoleSelection")
    @commands.has_permissions(administrator=True)
    async def role_selection(self, ctx: commands.Context):
        """!ServerRoleSelection — (Admin) Affiche le menu de sélection de rôles."""
        embed = discord.Embed(
            title="Sélection de rôles",
            description="Clique sur un bouton pour obtenir ou retirer un rôle.\nTu peux en avoir plusieurs !",
            color=0x5865F2,
        )
        for role_info in config.ROLE_SERVER_CHOICES:
            embed.add_field(name=role_info["name"], value=role_info["description"], inline=False)
        embed.set_footer(text="Cliquer à nouveau sur un rôle déjà obtenu le retire.")

        await safe_delete(ctx)
        await ctx.send(embed=embed, view=RoleSelectionView())


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
