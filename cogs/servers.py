"""Commandes !status et !servers (infos des serveurs Minecraft via Pterodactyl)."""
import asyncio

import discord
from discord.ext import commands

import config
from core.utils import error_embed, format_name_grid, safe_delete
from services import minecraft
from services.pterodactyl import PterodactylError, address_from_attributes, format_state
from ui.server_control import ServerControlView


class Servers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def ptero(self):
        return self.bot.ptero

    @commands.command(name="status")
    async def status(self, ctx: commands.Context, *, server_name: str | None = None):
        """!status [NomDuServeur] — Affiche le statut d'un serveur Minecraft."""
        await safe_delete(ctx)
        if not server_name:
            await ctx.send("❌ Usage : `!status [NomDuServeur]`")
            return

        async with ctx.typing():
            try:
                attr = await self.ptero.find_server(server_name)
            except PterodactylError as e:
                await ctx.send(embed=error_embed("Panel inaccessible", str(e)))
                return
            if attr is None:
                await ctx.send(embed=error_embed(
                    "Serveur introuvable", f"Aucun serveur trouvé avec le nom **{server_name}**."))
                return

            name, identifier = attr["name"], attr["identifier"]
            state = await self.ptero.get_state(identifier)
            running = state == "running"
            ip = config.SERVER_IPS.get(name.lower(), "Non configurée")

            mc, version = None, "—"
            if running:
                address = address_from_attributes(attr)
                mc, version = await asyncio.gather(
                    minecraft.ping(*address) if address else self._none(),
                    self.ptero.get_version(identifier),
                )

            if not running:
                online_text = latency_text = player_count = "—"
            else:
                player_count = mc.player_count if mc else "?/?"
                latency_text = f"{mc.latency} ms" if mc else "?"
                online_text = format_name_grid(mc.players) if mc and mc.players else "Aucun joueur connecté"

            whitelist = await self.ptero.get_whitelist(identifier)
            if whitelist is None:
                wl_text = "*Impossible de lire la whitelist*"
            elif not whitelist:
                wl_text = "*Aucun joueur whitelisté*"
            else:
                wl_text = format_name_grid(whitelist)

            embed = discord.Embed(title=name, description=f"**État :** {format_state(state)}")
            embed.add_field(name="🌐 IP", value=f"`{ip}`", inline=True)
            embed.add_field(name="⏱️ Latence", value=latency_text, inline=True)
            embed.add_field(name="🛠️ Version", value=version, inline=True)
            embed.add_field(name=f"👥 En ligne {player_count}", value=online_text, inline=False)
            embed.add_field(name=f"📋 Whitelist ({len(whitelist or [])} joueur(s))", value=wl_text, inline=False)
            embed.set_footer(text=f"Pterodactyl • ID: {identifier}")

            await ctx.send(embed=embed, view=ServerControlView(self.ptero, identifier, running))

    @commands.command(name="servers")
    async def list_servers(self, ctx: commands.Context):
        """!servers — Liste tous les serveurs disponibles."""
        await safe_delete(ctx)
        async with ctx.typing():
            try:
                servers = await self.ptero.get_all_servers()
            except PterodactylError as e:
                await ctx.send(embed=error_embed("Panel inaccessible", str(e)))
                return
            if not servers:
                await ctx.send("❌ Aucun serveur trouvé.")
                return

            # Tous les serveurs sont interrogés en parallèle
            lines = await asyncio.gather(*(self._summary(s["attributes"]) for s in servers))

            embed = discord.Embed(title="Serveurs Minecraft")
            for name, text in lines:
                embed.add_field(name=name, value=text, inline=False)
            await ctx.send(embed=embed)

    async def _summary(self, attr: dict) -> tuple[str, str]:
        identifier = attr["identifier"]
        state, version = await asyncio.gather(
            self.ptero.get_state(identifier), self.ptero.get_version(identifier))

        players = "—"
        if state == "running":
            address = address_from_attributes(attr)
            mc = await minecraft.ping(*address) if address else None
            players = mc.player_count if mc else "?/?"

        ip = config.SERVER_IPS.get(attr["name"].lower(), "Non configurée")
        return attr["name"], f"IP: `{ip}`\n{format_state(state)}\n{version}\nJoueurs: {players}"

    @staticmethod
    async def _none():
        return None


async def setup(bot: commands.Bot):
    await bot.add_cog(Servers(bot))
