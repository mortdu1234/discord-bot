"""Gestion centralisée des erreurs de commandes."""
import logging

from discord.ext import commands

log = logging.getLogger(__name__)


class Errors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande.", delete_after=5)
            return
        if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.send("❌ Arguments invalides.", delete_after=8)
            return

        log.error("Erreur dans la commande %s", ctx.command, exc_info=error)
        await ctx.send("❌ Une erreur inattendue est survenue.", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(Errors(bot))
