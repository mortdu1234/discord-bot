"""Commande !whitelist add/remove."""
import re

import discord
from discord.ext import commands

from core.utils import error_embed, safe_delete
from services.pterodactyl import PterodactylError

# Évite d'injecter d'autres commandes dans la console via le pseudo
VALID_PSEUDO = re.compile(r"^[A-Za-z0-9_.]{1,32}$")


class Whitelist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="whitelist")
    async def whitelist(self, ctx: commands.Context, action: str | None = None,
                        server_name: str | None = None, pseudo: str | None = None):
        """!whitelist [add/remove] [NomServeur] [Pseudo] — Ajoute ou retire un joueur de la whitelist."""
        await safe_delete(ctx)
        if action not in ("add", "remove") or not server_name or not pseudo:
            await ctx.send("❌ Usage : `!whitelist [add/remove] [NomDuServeur] [PseudoMinecraft]`")
            return
        if not VALID_PSEUDO.match(pseudo):
            await ctx.send("❌ Pseudo invalide.")
            return

        ptero = self.bot.ptero
        async with ctx.typing():
            try:
                attr = await ptero.find_server(server_name)
            except PterodactylError as e:
                await ctx.send(embed=error_embed("Panel inaccessible", str(e)))
                return
            if attr is None:
                await ctx.send(embed=error_embed(
                    "Serveur introuvable", f"Aucun serveur trouvé avec le nom **{server_name}**."))
                return

            identifier = attr["identifier"]
            if await ptero.get_state(identifier) != "running":
                await ctx.send(embed=error_embed(
                    "Serveur hors ligne",
                    f"Le serveur **{attr['name']}** doit être **en ligne** pour modifier la whitelist."))
                return

            if await ptero.send_command(identifier, f"whitelist {action} {pseudo}"):
                verb = "ajouté" if action == "add" else "retiré"
                embed = discord.Embed(
                    title="✅ Whitelist mise à jour",
                    description=f"**{pseudo}** a été {verb} de la whitelist de **{attr['name']}**.",
                )
                embed.set_footer(text=f"Commande exécutée par {ctx.author.display_name}")
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Impossible d'envoyer la commande au serveur.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Whitelist(bot))
