"""Commandes liées à la gestion des serveurs Minecraft : !status, !servers, !whitelist."""
from __future__ import annotations

import discord
from discord.ext import commands

from services.server_service import ServerService
from views.server_control import ServerControlView


def _format_player_columns(players: list[str], per_row: int = 3) -> str:
    """Affiche une liste de pseudos en colonnes de `per_row`, triée et backtickée."""
    ordered = sorted(players)
    return "\n".join(
        "  ".join(f"`{p}`" for p in ordered[i:i + per_row])
        for i in range(0, len(ordered), per_row)
    )


class ServerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, server_service: ServerService):
        self.bot = bot
        self.server_service = server_service

    @commands.command(name="status")
    async def status(self, ctx: commands.Context, *, server_name: str | None = None):
        """!status [NomDuServeur] — Affiche le statut détaillé d'un serveur Minecraft."""
        await ctx.message.delete()
        if not server_name:
            await ctx.send("❌ Usage : `!status [NomDuServeur]`")
            return

        async with ctx.typing():
            attr, error = await self.server_service.find(server_name)
            if error or attr is None:
                await ctx.send(embed=discord.Embed(title="❌ Serveur introuvable", description=error, color=0xE74C3C))
                return

            status = await self.server_service.get_full_status(attr)

            online_players_text = (
                _format_player_columns(status.online_players)
                if status.online_players else "Aucun joueur connecté"
            )

            if status.whitelist is None:
                whitelist_text = "*Impossible de lire la whitelist*"
            elif len(status.whitelist) == 0:
                whitelist_text = "*Aucun joueur whitelisté*"
            else:
                whitelist_text = _format_player_columns(status.whitelist)

            embed = discord.Embed(title=status.name, description=f"**État :** {status.state}")
            embed.add_field(name=f"🌐 IP : `{status.ip}`", value="", inline=True)
            embed.add_field(name="👥 En ligne", value=online_players_text, inline=False)
            embed.add_field(name="⏱️ Latence", value=f"{status.ping} ms" if status.ping is not None else "—", inline=True)
            embed.add_field(name="🛠️ Version", value=status.version, inline=True)
            embed.add_field(name=f"🎮 Joueurs connectés {status.player_count}", value="", inline=True)
            embed.add_field(
                name=f"📋 Whitelist ({len(status.whitelist) if status.whitelist else 0} joueur(s))",
                value=whitelist_text,
                inline=False,
            )
            embed.set_footer(text=f"Pterodactyl • ID: {status.identifier}")

            view = ServerControlView(status.identifier, status.state, self.server_service)
            await ctx.send(embed=embed, view=view)

    @commands.command(name="servers")
    async def list_servers(self, ctx: commands.Context):
        """!servers — Liste tous les serveurs disponibles avec un résumé rapide."""
        await ctx.message.delete()
        async with ctx.typing():
            servers = await self.server_service.list_all()
            if not servers:
                await ctx.send("❌ Aucun serveur trouvé ou panel inaccessible.")
                return

            embed = discord.Embed(title="Serveurs Minecraft")
            for s in servers:
                attr = s["attributes"]
                status = await self.server_service.get_full_status(attr)
                players = status.player_count if status.is_online else "—"
                embed.add_field(
                    name=attr["name"],
                    value=f"IP: `{status.ip}`\n{status.state}\n{status.version}\nJoueurs: {players}",
                    inline=False,
                )
            await ctx.send(embed=embed)

    @commands.command(name="whitelist")
    async def whitelist(
        self,
        ctx: commands.Context,
        action: str | None = None,
        server_name: str | None = None,
        pseudo: str | None = None,
    ):
        """!whitelist [add/remove] [NomServeur] [Pseudo] — Ajoute ou retire un joueur de la whitelist."""
        await ctx.message.delete()
        if action not in ("add", "remove") or not server_name or not pseudo:
            await ctx.send("❌ Usage : `!whitelist [add/remove] [NomDuServeur] [PseudoMinecraft]`")
            return

        async with ctx.typing():
            attr, error = await self.server_service.find(server_name)
            if error or attr is None:
                await ctx.send(embed=discord.Embed(title="❌ Serveur introuvable", description=error, color=0xE74C3C))
                return

            identifier = attr["identifier"]
            state = await self.server_service.get_state(identifier)
            if "En ligne" not in state:
                await ctx.send(embed=discord.Embed(
                    title="❌ Serveur hors ligne",
                    description=f"Le serveur **{attr['name']}** doit être **en ligne** pour modifier la whitelist.",
                ))
                return

            success = await self.server_service.update_whitelist(identifier, action, pseudo)
            if success:
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
    # bot.server_service est injecté dans main.py avant le chargement des cogs.
    await bot.add_cog(ServerCommands(bot, bot.server_service))
