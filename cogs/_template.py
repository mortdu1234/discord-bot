"""
MODÈLE POUR UNE NOUVELLE FONCTIONNALITÉ
=======================================
Les fichiers qui commencent par '_' sont ignorés par le bot.

Pour créer une fonctionnalité :
  1. Copie ce fichier :  cp cogs/_template.py cogs/ma_fonction.py
  2. Renomme la classe et ajoute tes commandes
  3. Relance le bot : il est chargé automatiquement.

Accès aux services partagés :  self.bot.ptero  (client Pterodactyl)
Config / constantes :           import config
"""
from discord.ext import commands


class Template(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """!ping — Affiche la latence du bot."""
        await ctx.send(f"🏓 Pong ! {round(self.bot.latency * 1000)} ms")

    # Exemple d'écouteur d'évènement :
    # @commands.Cog.listener()
    # async def on_member_join(self, member): ...


async def setup(bot: commands.Bot):
    await bot.add_cog(Template(bot))
