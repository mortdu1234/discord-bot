"""Commandes !setServer / !removeServer + notifications automatiques dans les salons associés.

Messages envoyés :
  - "@utilisateur vient d'ouvrir le serveur XXX"
  - "Le serveur XXX vient de se fermer"
  - "pseudo vient de rejoindre le serveur XXX"
"""
import asyncio
import logging
import time

import discord
from discord.ext import commands

import config
from core.utils import error_embed, safe_delete
from services.notification_store import ServerLinks
from services.pterodactyl import PterodactylError
from services.pterodactyl_ws import ServerWatcher

log = logging.getLogger(__name__)

# Combien de temps on retient "qui a cliqué sur Démarrer" en attendant que le serveur soit en ligne
STARTER_TTL = 600  # secondes (un serveur Forge peut mettre plusieurs minutes)


def _clean(name: str | None) -> str:
    """'"Stonks Ville"' -> 'Stonks Ville' (guillemets facultatifs)."""
    return (name or "").strip().strip('"“”«»').strip()


class Notifications(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.links = ServerLinks(config.DATA_DIR / "server_links.json")
        self._watchers: dict[str, ServerWatcher] = {}
        self._states: dict[str, str] = {}
        self._starters: dict[str, tuple[discord.abc.User, float]] = {}
        self._startup_task: asyncio.Task | None = None

    # ─── Cycle de vie ────────────────────────────────────────────────────────
    async def cog_load(self):
        self._startup_task = asyncio.create_task(self._start_saved_watchers())

    async def cog_unload(self):
        if self._startup_task:
            self._startup_task.cancel()
        await asyncio.gather(*(w.stop() for w in self._watchers.values()))
        self._watchers.clear()

    async def _start_saved_watchers(self):
        await self.bot.wait_until_ready()
        for identifier in self.links.identifiers():
            await self._ensure_watcher(identifier)

    async def _ensure_watcher(self, identifier: str):
        if identifier in self._watchers:
            return
        # État de départ : sert à détecter les changements (pas de message au démarrage du bot)
        self._states[identifier] = await self.bot.ptero.get_state(identifier)
        watcher = ServerWatcher(self.bot.ptero, identifier, self._on_status, self._on_join)
        self._watchers[identifier] = watcher
        watcher.start()

    async def _drop_watcher(self, identifier: str):
        watcher = self._watchers.pop(identifier, None)
        if watcher:
            await watcher.stop()
        self._states.pop(identifier, None)
        self._starters.pop(identifier, None)

    # ─── Commandes ───────────────────────────────────────────────────────────
    @commands.command(name="setServer")
    @commands.has_permissions(administrator=True)
    async def set_server(self, ctx: commands.Context, *, server_name: str | None = None):
        """!setServer "NomDuServeur" — (Admin) Envoie dans ce salon les notifications du serveur."""
        await safe_delete(ctx)
        name = _clean(server_name)
        if not name:
            await ctx.send('❌ Usage : `!setServer "NomDuServeur"`', delete_after=8)
            return

        async with ctx.typing():
            try:
                attr = await self.bot.ptero.find_server(name)
            except PterodactylError as e:
                await ctx.send(embed=error_embed("Panel inaccessible", str(e)))
                return
            if attr is None:
                await ctx.send(embed=error_embed(
                    "Serveur introuvable", f"Aucun serveur trouvé avec le nom **{name}**."))
                return

            identifier, real_name = attr["identifier"], attr["name"]
            added = self.links.add(identifier, real_name, ctx.channel.id)
            await self._ensure_watcher(identifier)

        if added:
            await ctx.send(f"✅ Les notifications du serveur **{real_name}** seront envoyées dans ce salon.")
        else:
            await ctx.send(f"ℹ️ Le serveur **{real_name}** est déjà associé à ce salon.", delete_after=8)

    @commands.command(name="removeServer", aliases=["unsetServer"])
    @commands.has_permissions(administrator=True)
    async def remove_server(self, ctx: commands.Context, *, server_name: str | None = None):
        """!removeServer "NomDuServeur" — (Admin) Arrête les notifications du serveur dans ce salon."""
        await safe_delete(ctx)
        name = _clean(server_name)
        if not name:
            await ctx.send('❌ Usage : `!removeServer "NomDuServeur"`', delete_after=8)
            return

        identifier = self.links.find(name, ctx.channel.id)
        if identifier is None:
            linked = self.links.names_for_channel(ctx.channel.id)
            hint = f" Serveurs associés à ce salon : {', '.join(f'**{n}**' for n in linked)}." if linked \
                else " Aucun serveur n'est associé à ce salon."
            await ctx.send(embed=error_embed(
                "Serveur non associé", f"**{name}** n'est pas associé à ce salon.{hint}"))
            return

        real_name = self.links.name(identifier)
        self.links.remove(identifier, ctx.channel.id)
        if not self.links.channels_for(identifier):
            await self._drop_watcher(identifier)  # plus aucun salon : on arrête d'écouter ce serveur
        await ctx.send(f"✅ Les notifications du serveur **{real_name}** ne seront plus envoyées dans ce salon.")

    # ─── Évènements ──────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_server_power(self, identifier: str, action: str, user: discord.abc.User):
        """Déclenché par les boutons Démarrer/Redémarrer (ui/server_control.py)."""
        if identifier in self._watchers:
            self._starters[identifier] = (user, time.monotonic())

    async def _on_status(self, identifier: str, state: str):
        previous = self._states.get(identifier)
        self._states[identifier] = state
        name = self.links.name(identifier)
        if name is None:
            return

        if state == "running" and previous in ("offline", "starting"):
            starter = self._pop_starter(identifier)
            if starter:
                text = f"🟢 {starter.mention} vient d'ouvrir le serveur **{name}** !"
            else:  # lancé depuis le panel, ou par quelqu'un que le bot n'a pas vu
                text = f"🟢 Le serveur **{name}** vient de s'ouvrir !"
            await self._broadcast(identifier, text, ping=starter is not None)
        elif state == "offline" and previous in ("running", "starting", "stopping"):
            await self._broadcast(identifier, f"🔴 Le serveur **{name}** vient de se fermer.")

    async def _on_join(self, identifier: str, pseudo: str):
        name = self.links.name(identifier)
        if name is None:
            return
        pseudo = discord.utils.escape_markdown(pseudo)  # les "_" des pseudos casseraient la mise en forme
        await self._broadcast(identifier, f"👋 **{pseudo}** vient de rejoindre le serveur **{name}**.")

    # ─── Envoi ───────────────────────────────────────────────────────────────
    def _pop_starter(self, identifier: str) -> discord.abc.User | None:
        entry = self._starters.pop(identifier, None)
        if entry and time.monotonic() - entry[1] <= STARTER_TTL:
            return entry[0]
        return None

    async def _broadcast(self, identifier: str, text: str, ping: bool = False):
        mentions = discord.AllowedMentions(users=True) if ping else discord.AllowedMentions.none()
        for channel_id in self.links.channels_for(identifier):
            channel = self.bot.get_channel(channel_id)
            try:
                if channel is None:
                    channel = await self.bot.fetch_channel(channel_id)
                await channel.send(text, allowed_mentions=mentions)
            except discord.HTTPException as e:
                # Salon supprimé ou permission retirée : on continue pour les autres salons
                log.warning("Notification impossible dans le salon %s : %s", channel_id, e)


async def setup(bot: commands.Bot):
    await bot.add_cog(Notifications(bot))
