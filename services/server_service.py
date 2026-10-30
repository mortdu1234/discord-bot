"""
Couche métier qui combine Pterodactyl (état, actions, fichiers) et mcstatus
(ping direct du serveur) pour fournir un statut complet, prêt à afficher.

C'est le SEUL module que les commandes Discord (cogs) doivent appeler :
elles n'ont jamais besoin de connaître Pterodactyl ou mcstatus directement.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from config import SERVER_IPS
from services import minecraft
from services.pterodactyl import PterodactylClient


@dataclass
class ServerStatus:
    name: str
    identifier: str
    state: str                                  # ex: "🟢 En ligne"
    ip: str
    version: str = "—"
    player_count: str = "—"
    online_players: list[str] | None = None
    ping: float | None = None
    whitelist: list[str] | None = field(default=None)

    @property
    def is_online(self) -> bool:
        return "En ligne" in self.state


class ServerService:
    """Point d'entrée unique pour toutes les infos/actions sur les serveurs Minecraft."""

    def __init__(self, ptero: PterodactylClient):
        self.ptero = ptero

    async def find(self, name: str) -> tuple[dict | None, str | None]:
        return await self.ptero.find_server(name)

    async def list_all(self) -> list[dict] | None:
        return await self.ptero.get_all_servers()

    async def get_state(self, identifier: str) -> str:
        resources = await self.ptero.get_resources(identifier)
        return minecraft.format_state(resources.get("current_state", "unknown"))

    def get_public_ip(self, server_name: str) -> str:
        return SERVER_IPS.get(server_name.lower(), "Non configurée")

    async def get_full_status(self, attr: dict) -> ServerStatus:
        """Construit un statut complet : état, version, joueurs, ping, whitelist."""
        identifier = attr["identifier"]
        name = attr["name"]

        state = await self.get_state(identifier)
        status = ServerStatus(name=name, identifier=identifier, state=state, ip=self.get_public_ip(name))

        if status.is_online:
            status.version = await self.ptero.get_version(identifier)
            allocation = await self.ptero.get_allocation(identifier)
            if allocation:
                host, port = allocation
                status.player_count = await minecraft.get_player_count(host, port)
                status.online_players = await minecraft.get_online_players(host, port)
                status.ping = await minecraft.get_ping(host, port)

        status.whitelist = await self.ptero.get_whitelist(identifier)
        return status

    async def set_power(self, identifier: str, action: str) -> bool:
        return await self.ptero.send_power_action(identifier, action)

    async def update_whitelist(self, identifier: str, action: str, pseudo: str) -> bool:
        return await self.ptero.send_console_command(identifier, f"whitelist {action} {pseudo}")
