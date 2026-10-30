"""Associations serveur Minecraft ↔ salons Discord, sauvegardées dans un fichier JSON.

Relation plusieurs-à-plusieurs : un serveur peut notifier plusieurs salons,
et un salon peut recevoir les notifications de plusieurs serveurs.
(Aucun code Discord ici : on ne manipule que des identifiants.)

Format du fichier :
    {"<identifiant Pterodactyl>": {"name": "Survival", "channels": [123456789, ...]}}
"""
import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)


class ServerLinks:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._data: dict[str, dict] = {}
        self._load()

    # ─── Persistance ─────────────────────────────────────────────────────────
    def _load(self) -> None:
        try:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (json.JSONDecodeError, OSError):
            # On garde une copie du fichier abîmé plutôt que de l'écraser au prochain enregistrement
            backup = self.path.with_suffix(".corrupt")
            log.exception("Fichier %s illisible, copie conservée dans %s", self.path, backup)
            try:
                os.replace(self.path, backup)
            except OSError:
                pass
            self._data = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)  # écriture atomique : jamais de fichier à moitié écrit

    # ─── Modification ────────────────────────────────────────────────────────
    def add(self, identifier: str, name: str, channel_id: int) -> bool:
        """Associe le salon au serveur. False si c'était déjà le cas."""
        entry = self._data.setdefault(identifier, {"name": name, "channels": []})
        entry["name"] = name  # suit un éventuel renommage dans le panel
        if channel_id in entry["channels"]:
            self._save()
            return False
        entry["channels"].append(channel_id)
        self._save()
        return True

    def remove(self, identifier: str, channel_id: int) -> bool:
        """Retire l'association. False si elle n'existait pas."""
        entry = self._data.get(identifier)
        if not entry or channel_id not in entry["channels"]:
            return False
        entry["channels"].remove(channel_id)
        if not entry["channels"]:
            del self._data[identifier]
        self._save()
        return True

    # ─── Lecture ─────────────────────────────────────────────────────────────
    def identifiers(self) -> list[str]:
        return list(self._data)

    def name(self, identifier: str) -> str | None:
        entry = self._data.get(identifier)
        return entry["name"] if entry else None

    def channels_for(self, identifier: str) -> list[int]:
        entry = self._data.get(identifier)
        return list(entry["channels"]) if entry else []

    def all_links(self) -> list[tuple[str, list[int]]]:
        """[(nom du serveur, [ids des salons])], trié par nom."""
        return sorted((e["name"], list(e["channels"])) for e in self._data.values())

    def names_for_channel(self, channel_id: int) -> list[str]:
        return sorted(e["name"] for e in self._data.values() if channel_id in e["channels"])

    def find(self, name: str, channel_id: int) -> str | None:
        """Identifiant du serveur associé à ce salon sous ce nom (insensible à la casse)."""
        name = name.lower()
        for identifier, entry in self._data.items():
            if channel_id in entry["channels"] and entry["name"].lower() == name:
                return identifier
        return None
