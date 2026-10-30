"""Ping d'un serveur Minecraft Java via mcstatus."""
import logging
from dataclasses import dataclass

from mcstatus import JavaServer

log = logging.getLogger(__name__)


@dataclass
class McStatus:
    online: int
    max: int
    players: list[str]
    latency: float  # ms

    @property
    def player_count(self) -> str:
        return f"{self.online}/{self.max}"


async def ping(host: str, port: int, timeout: float = 3) -> McStatus | None:
    """Un seul appel réseau pour récupérer joueurs + latence. None en cas d'échec."""
    try:
        server = JavaServer(host, port, timeout=timeout)
        status = await server.async_status()
    except Exception as e:
        log.warning("Ping Minecraft échoué pour %s:%s → %s", host, port, e)
        return None

    sample = status.players.sample or []
    return McStatus(
        online=status.players.online,
        max=status.players.max,
        players=[p.name for p in sample],
        latency=round(status.latency, 1),
    )
