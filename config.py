"""Configuration centrale : variables d'environnement et constantes du bot."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ─── Variables d'environnement ───────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

PTERODACTYL_URL = (os.getenv("PTERODACTYL_URL") or "").rstrip("/")
PTERODACTYL_API_KEY = os.getenv("PTERODACTYL_API_KEY")


def _parse_server_ips(raw: str) -> dict[str, str]:
    """'Survival=1.2.3.4:25565,Creative=1.2.3.4:25566' -> {'survival': '1.2.3.4:25565', ...}"""
    ips = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if "=" in entry:
            name, ip = entry.split("=", 1)
            ips[name.strip().lower()] = ip.strip()
    return ips


SERVER_IPS = _parse_server_ips(os.getenv("SERVER_IPS", ""))

# Dossier où le bot garde ses fichiers de données (associations salon ↔ serveur, etc.)
DATA_DIR = Path(os.getenv("DATA_DIR") or Path(__file__).resolve().parent / "data")

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
    required = {
        "DISCORD_TOKEN": DISCORD_TOKEN,
        "PTERODACTYL_URL": PTERODACTYL_URL,
        "PTERODACTYL_API_KEY": PTERODACTYL_API_KEY,
    }
    return [name for name, value in required.items() if not value]
