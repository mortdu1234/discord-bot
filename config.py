<<<<<<< HEAD
"""Configuration centrale : variables d'environnement et constantes du bot."""
import os
=======
"""
Configuration centralisée du bot : variables d'environnement, rôles auto-attribuables,
et adresses publiques des serveurs Minecraft.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
>>>>>>> 94f5a8d7946fd71b7dd35daace29094c052087ac

from dotenv import load_dotenv

load_dotenv()

<<<<<<< HEAD
# ─── Variables d'environnement ───────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

PTERODACTYL_URL = (os.getenv("PTERODACTYL_URL") or "").rstrip("/")
PTERODACTYL_API_KEY = os.getenv("PTERODACTYL_API_KEY")


def _parse_server_ips(raw: str) -> dict[str, str]:
    """'Survival=1.2.3.4:25565,Creative=1.2.3.4:25566' -> {'survival': '1.2.3.4:25565', ...}"""
    ips = {}
=======

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
    RoleChoice("Palworld", "Joueur du serveur Palworld"),
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
>>>>>>> 94f5a8d7946fd71b7dd35daace29094c052087ac
    for entry in raw.split(","):
        entry = entry.strip()
        if "=" in entry:
            name, ip = entry.split("=", 1)
            ips[name.strip().lower()] = ip.strip()
    return ips


<<<<<<< HEAD
SERVER_IPS = _parse_server_ips(os.getenv("SERVER_IPS", ""))

# ─── Constantes du bot ───────────────────────────────────────────────────────
# Rôles proposés dans le menu de sélection (commande ServerRoleSelection)
ROLE_SERVER_CHOICES = [
    {"name": "StonksVillien", "description": "Joueur du server Stonks Ville"},
    {"name": "StonksModien", "description": "Joueur du server Stonks Mod"},
    {"name": "Cavien", "description": "Joueur du server de la Cave"},
    {"name": "HelperAdmin", "description": "Joueur pour aider au developpement du bot et la gestion des serveurs"},
]


def missing_settings() -> list[str]:
    """Liste les variables obligatoires non renseignées."""
=======
SERVER_IPS: dict[str, str] = _load_server_ips()


def validate_config() -> None:
    """Vérifie que les variables obligatoires sont présentes, avec un message d'erreur clair."""
>>>>>>> 94f5a8d7946fd71b7dd35daace29094c052087ac
    required = {
        "DISCORD_TOKEN": DISCORD_TOKEN,
        "PTERODACTYL_URL": PTERODACTYL_URL,
        "PTERODACTYL_API_KEY": PTERODACTYL_API_KEY,
    }
<<<<<<< HEAD
    return [name for name, value in required.items() if not value]
=======
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            f"Variables d'environnement manquantes dans le .env : {', '.join(missing)}"
        )
>>>>>>> 94f5a8d7946fd71b7dd35daace29094c052087ac
