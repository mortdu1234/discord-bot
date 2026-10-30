"""Écoute en direct d'un serveur via le websocket de Pterodactyl (aucun code Discord).

Remonte deux évènements :
  - on_status(identifier, state)   : 'running', 'offline', 'starting', 'stopping'...
  - on_join(identifier, pseudo)    : un joueur vient de rejoindre (lu dans la console)
"""
import asyncio
import logging
import re
import time
from typing import Awaitable, Callable

import aiohttp
from yarl import URL

from services.pterodactyl import PterodactylClient

log = logging.getLogger(__name__)

RECONNECT_MIN = 5    # secondes avant de retenter après une coupure
RECONNECT_MAX = 120  # plafond du délai (il double à chaque échec consécutif)

_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
# Vanilla / Forge / Paper : "[12:00:00] [Server thread/INFO]: Steve joined the game"
# Le "]: " collé au pseudo exclut les messages de chat ("<Bob> Steve joined the game").
_JOIN = re.compile(r"\]: ([A-Za-z0-9_.]{1,32}) joined the game$")


class ServerWatcher:
    def __init__(
        self,
        ptero: PterodactylClient,
        identifier: str,
        on_status: Callable[[str, str], Awaitable[None]],
        on_join: Callable[[str, str], Awaitable[None]],
    ) -> None:
        self.ptero = ptero
        self.identifier = identifier
        self._on_status = on_status
        self._on_join = on_join
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name=f"watch-{self.identifier}")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    # ─── Boucle de reconnexion ───────────────────────────────────────────────
    async def _run(self) -> None:
        delay = RECONNECT_MIN
        while True:
            started = time.monotonic()
            try:
                await self._session_once()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("Websocket de %s interrompu : %s", self.identifier, e)
            # Une connexion restée stable repart du délai minimal, sinon on espace les tentatives
            delay = RECONNECT_MIN if time.monotonic() - started > 60 else min(delay * 2, RECONNECT_MAX)
            await asyncio.sleep(delay)

    async def _session_once(self) -> None:
        creds = await self.ptero.get_websocket_credentials(self.identifier)
        # Wings vérifie l'Origin : même format qu'un navigateur (sans port par défaut)
        origin = str(URL(self.ptero.base_url).origin())
        # Session séparée : on n'envoie pas la clé API du panel à l'adresse du daemon
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(creds["socket"], headers={"Origin": origin}, heartbeat=30) as ws:
                await ws.send_json({"event": "auth", "args": [creds["token"]]})
                log.info("Websocket connecté : %s", self.identifier)
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.ERROR:
                        raise ws.exception() or ConnectionError("Erreur websocket")
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle(ws, msg.json())

    # ─── Évènements ──────────────────────────────────────────────────────────
    async def _handle(self, ws: aiohttp.ClientWebSocketResponse, payload: dict) -> None:
        event = payload.get("event")
        args = payload.get("args") or []

        if event == "status" and args:
            await self._call(self._on_status, args[0])
        elif event == "console output" and args:
            line = _ANSI.sub("", str(args[0])).strip()
            match = _JOIN.search(line)
            if match:
                await self._call(self._on_join, match.group(1))
        elif event == "token expiring":
            creds = await self.ptero.get_websocket_credentials(self.identifier)
            await ws.send_json({"event": "auth", "args": [creds["token"]]})
        elif event in ("token expired", "jwt error"):
            raise ConnectionError(f"Authentification refusée ({event}) : {args}")

    async def _call(self, callback, value: str) -> None:
        """Une erreur dans un callback ne doit pas couper l'écoute."""
        try:
            await callback(self.identifier, value)
        except Exception:
            log.exception("Erreur dans le traitement d'un évènement de %s", self.identifier)
