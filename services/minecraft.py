"""
Wrapper autour de mcstatus pour interroger directement les serveurs Minecraft
(ping, joueurs connectés) via leur IP/port publics.
"""
from __future__ import annotations

from mcstatus import JavaServer

STATE_LABELS = {
    "running":  ("🟢", "En ligne"),
    "starting": ("🟡", "Démarrage"),
    "stopping": ("🟠", "Arrêt"),
    "offline":  ("🔴", "Hors ligne"),
    "unknown":  ("⚪", "Inconnu"),
}


def format_state(current_state: str) -> str:
    """Traduit l'état brut Pterodactyl (ex: 'running') en libellé affichable."""
    emoji, label = STATE_LABELS.get(current_state, STATE_LABELS["unknown"])
    return f"{emoji} {label}"


async def _query(host: str, port: int, timeout: float = 3):
    server = JavaServer.lookup(f"{host}:{port}", timeout=timeout)
    return await server.async_status()


async def get_player_count(host: str, port: int) -> str:
    """Retourne '{online}/{max}', ou '?/?' en cas d'échec."""
    try:
        status = await _query(host, port)
        return f"{status.players.online}/{status.players.max}"
    except Exception as e:
        print(f"[MC Ping] Erreur get_player_count {host}:{port} → {e}")
        return "?/?"


async def get_online_players(host: str, port: int) -> list[str] | None:
    """Retourne la liste des pseudos connectés, ou None si personne/erreur."""
    try:
        status = await _query(host, port)
        if status.players.online == 0:
            return None
        sample = status.players.sample or []
        return [p.name for p in sample]
    except Exception as e:
        print(f"[MC Ping] Erreur get_online_players {host}:{port} → {e}")
        return None


async def get_ping(host: str, port: int) -> float | None:
    """Retourne la latence en ms, ou None en cas d'erreur."""
    try:
        server = JavaServer.lookup(f"{host}:{port}", timeout=3)
        latency = await server.async_ping()
        return round(latency, 1)
    except Exception as e:
        print(f"[MC Ping] Erreur get_ping {host}:{port} → {e}")
        return None
