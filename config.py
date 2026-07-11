"""
Configuration centralisée du bot : variables d'environnement, rôles auto-attribuables,
et adresses publiques des serveurs Minecraft.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class RoleChoice:
    name: str
    description: str
    color: int = 0x5865F2  # couleur par défaut (Discord Blurple)


# Rôles proposés par la commande !ServerRoleSelection.
# S'ils n'existent pas encore sur le serveur, le bot les crée automatiquement.
ROLE_CHOICES: list[RoleChoice] = [
    RoleChoice("StonksVillien", "Joueur du serveur Stonks Ville"),
    RoleChoice("StonksModien", "Joueur du serveur Stonks Mod"),
    RoleChoice("Cavien", "Joueur du serveur de la Cave"),
    RoleChoice("HelperAdmin", "Aide au développement du bot et à la gestion des serveurs"),
]

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

PTERODACTYL_URL = os.getenv("PTERODACTYL_URL")           # ex: http://192.168.1.50:80
PTERODACTYL_API_KEY = os.getenv("PTERODACTYL_API_KEY")   # Client API Key (ptlc_...)


def _load_server_ips() -> dict[str, str]:
    """
    Charge les IPs publiques depuis la variable d'environnement SERVER_IPS.
    Format attendu : "Survival=192.168.1.50:25565,Creative=192.168.1.50:25566"
    """
    raw = os.getenv("SERVER_IPS", "")
    ips: dict[str, str] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if "=" in entry:
            name, ip = entry.split("=", 1)
            ips[name.strip().lower()] = ip.strip()
    return ips


SERVER_IPS: dict[str, str] = _load_server_ips()


def validate_config() -> None:
    """Vérifie que les variables obligatoires sont présentes, avec un message d'erreur clair."""
    required = {
        "DISCORD_TOKEN": DISCORD_TOKEN,
        "PTERODACTYL_URL": PTERODACTYL_URL,
        "PTERODACTYL_API_KEY": PTERODACTYL_API_KEY,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            f"Variables d'environnement manquantes dans le .env : {', '.join(missing)}"
        )
