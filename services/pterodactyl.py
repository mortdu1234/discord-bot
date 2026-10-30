<<<<<<< HEAD
"""Client pour l'API Client de Pterodactyl (une seule session HTTP partagée)."""
import asyncio
=======
"""
Client HTTP pour l'API Pterodactyl (panel de gestion des serveurs Minecraft).

Toutes les requêtes passent par cette classe afin de :
- centraliser les headers et l'authentification,
- réutiliser une seule session aiohttp (au lieu d'en ouvrir une par appel),
- garder la logique HTTP séparée des commandes Discord.
"""
from __future__ import annotations

>>>>>>> 94f5a8d7946fd71b7dd35daace29094c052087ac
import json
import re

import aiohttp

<<<<<<< HEAD
STATE_DISPLAY = {
    "running":  "🟢 En ligne",
    "starting": "🟡 Démarrage",
    "stopping": "🟠 Arrêt",
    "offline":  "🔴 Hors ligne",
    "unknown":  "⚪ Inconnu",
}


def format_state(state: str) -> str:
    return STATE_DISPLAY.get(state, STATE_DISPLAY["unknown"])


def address_from_attributes(attr: dict) -> tuple[str, int] | None:
    """Extrait (ip, port) de l'allocation par défaut d'un serveur."""
    allocations = attr.get("relationships", {}).get("allocations", {}).get("data", [])
    alloc = next(
        (a for a in allocations if a["attributes"].get("is_default")),
        allocations[0] if allocations else None,
    )
    if not alloc:
        return None
    a = alloc["attributes"]
    return a.get("ip", ""), int(a.get("port", 25565))


class PterodactylError(Exception):
    """Le panel est injoignable ou a répondu avec une erreur."""


class PterodactylClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._session: aiohttp.ClientSession | None = None

    # ─── Bas niveau ──────────────────────────────────────────────────────────
    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=15),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/client{path}"

    async def _get_json(self, path: str) -> dict:
        try:
            async with self.session.get(self._url(path)) as resp:
                if resp.status != 200:
                    raise PterodactylError(f"Le panel a répondu HTTP {resp.status}.")
                return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise PterodactylError("Impossible de contacter le panel Pterodactyl.") from e

    async def _post_ok(self, path: str, payload: dict) -> bool:
        """POST qui renvoie True si le panel répond 204 (succès sans contenu)."""
        try:
            async with self.session.post(self._url(path), json=payload) as resp:
                return resp.status == 204
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    # ─── Serveurs ────────────────────────────────────────────────────────────
    async def get_all_servers(self) -> list[dict]:
        """Tous les serveurs accessibles par la clé API. Lève PterodactylError."""
        return (await self._get_json("")).get("data", [])

    async def find_server(self, name: str) -> dict | None:
        """Retourne les attributs du serveur (insensible à la casse), ou None."""
        name = name.lower()
        for server in await self.get_all_servers():
            if server["attributes"]["name"].lower() == name:
                return server["attributes"]
        return None

    async def get_state(self, identifier: str) -> str:
        """'running', 'offline', 'starting', 'stopping' ou 'unknown'."""
        try:
            data = await self._get_json(f"/servers/{identifier}/resources")
        except PterodactylError:
            return "unknown"
        return data.get("attributes", {}).get("current_state", "unknown")

    async def send_power_action(self, identifier: str, action: str) -> bool:
        """action : start, stop, restart, kill."""
        return await self._post_ok(f"/servers/{identifier}/power", {"signal": action})

    async def send_command(self, identifier: str, command: str) -> bool:
        """Envoie une commande dans la console du serveur."""
        return await self._post_ok(f"/servers/{identifier}/command", {"command": command})

    # ─── Fichiers ────────────────────────────────────────────────────────────
    async def read_file(self, identifier: str, path: str) -> str | None:
        try:
            async with self.session.get(
                self._url(f"/servers/{identifier}/files/contents"), params={"file": path}
            ) as resp:
                if resp.status != 200:
                    return None
                return await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

    async def get_version(self, identifier: str) -> str:
        """Lit infos.txt et retourne par ex. '1.19.2 (forge)', ou '?'."""
        text = await self.read_file(identifier, "infos.txt")
        if text:
            match = re.search(r"version:\s*([\d.]+)\s+(\w+)", text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} ({match.group(2)})"
        return "?"

    async def get_whitelist(self, identifier: str) -> list[str] | None:
        """Pseudos présents dans whitelist.json, ou None si illisible."""
        text = await self.read_file(identifier, "/whitelist.json")
        if text is None:
            return None
        try:
            return [e.get("name", "?") for e in json.loads(text) if isinstance(e, dict)]
=======
from config import PTERODACTYL_API_KEY, PTERODACTYL_URL


class PterodactylClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or PTERODACTYL_URL or "").rstrip("/")
        self.api_key = api_key or PTERODACTYL_API_KEY
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        """À appeler une seule fois au démarrage du bot."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self._headers())

    async def close(self) -> None:
        """À appeler à l'arrêt du bot pour fermer proprement la session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, **kwargs) -> dict | None:
        async with self._session.get(f"{self.base_url}{path}", **kwargs) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

    async def _get_text(self, path: str, **kwargs) -> str | None:
        async with self._session.get(f"{self.base_url}{path}", **kwargs) as resp:
            if resp.status != 200:
                return None
            return await resp.text()

    async def _post(self, path: str, json_body: dict) -> bool:
        async with self._session.post(f"{self.base_url}{path}", json=json_body) as resp:
            return resp.status == 204

    # ─── Serveurs ─────────────────────────────────────────────────────────

    async def get_all_servers(self) -> list[dict] | None:
        """Retourne la liste de tous les serveurs accessibles par le compte."""
        data = await self._get("/api/client")
        return data.get("data", []) if data else None

    async def find_server(self, name: str) -> tuple[dict | None, str | None]:
        """Cherche un serveur par nom (insensible à la casse)."""
        servers = await self.get_all_servers()
        if servers is None:
            return None, "Impossible de contacter le panel Pterodactyl."
        name_lower = name.lower()
        for server in servers:
            attr = server["attributes"]
            if attr["name"].lower() == name_lower:
                return attr, None
        return None, f"Aucun serveur trouvé avec le nom **{name}**."

    async def get_resources(self, identifier: str) -> dict:
        """Retourne les ressources (état, RAM, CPU) d'un serveur."""
        data = await self._get(f"/api/client/servers/{identifier}/resources")
        return data.get("attributes", {}) if data else {}

    async def get_allocation(self, identifier: str) -> tuple[str, int] | None:
        """Récupère l'IP et le port du serveur depuis les allocations Pterodactyl."""
        servers = await self.get_all_servers()
        if not servers:
            return None

        server = next((s for s in servers if s["attributes"]["identifier"] == identifier), None)
        if not server:
            return None

        allocations = server["attributes"].get("relationships", {}).get("allocations", {}).get("data", [])
        alloc = next(
            (a for a in allocations if a["attributes"].get("is_default")),
            allocations[0] if allocations else None,
        )
        if not alloc:
            return None

        attr = alloc["attributes"]
        return attr.get("ip", ""), int(attr.get("port", 25565))

    # ─── Actions ──────────────────────────────────────────────────────────

    async def send_power_action(self, identifier: str, action: str) -> bool:
        """Envoie une action de puissance : start, stop, restart, kill."""
        return await self._post(f"/api/client/servers/{identifier}/power", {"signal": action})

    async def send_console_command(self, identifier: str, command: str) -> bool:
        """Envoie une commande console au serveur Minecraft."""
        return await self._post(f"/api/client/servers/{identifier}/command", {"command": command})

    # ─── Fichiers ─────────────────────────────────────────────────────────

    async def read_file(self, identifier: str, path: str) -> str | None:
        return await self._get_text(f"/api/client/servers/{identifier}/files/contents", params={"file": path})

    async def get_version(self, identifier: str) -> str:
        """Lit infos.txt pour trouver la version du serveur (ex: '1.19.2 (Forge)')."""
        text = await self.read_file(identifier, "infos.txt")
        if not text:
            return "?"
        match = re.search(r"version:\s*([\d.]+)\s+(\w+)", text, re.IGNORECASE)
        if not match:
            return "?"
        return f"{match.group(1)} ({match.group(2)})"

    async def get_whitelist(self, identifier: str) -> list[str] | None:
        """Lit whitelist.json (liste de {'uuid', 'name'}) et retourne les pseudos."""
        text = await self.read_file(identifier, "/whitelist.json")
        if not text:
            return None
        try:
            data = json.loads(text)
            return [entry.get("name", "?") for entry in data if isinstance(entry, dict)]
>>>>>>> 94f5a8d7946fd71b7dd35daace29094c052087ac
        except (json.JSONDecodeError, TypeError):
            return None
