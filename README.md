# Bot Discord – Gestion de serveurs Minecraft (Pterodactyl)

## Installation
```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # puis remplis les valeurs
python main.py
```

## Docker
```bash
cp .env.example .env     # puis remplis les valeurs
docker compose up -d --build
docker compose logs -f   # voir les logs
docker compose down      # arrêter
```
Le `.env` n'est jamais copié dans l'image : il est injecté au lancement du conteneur.
Après avoir modifié le code ou ajouté un cog, relance avec `docker compose up -d --build`.

## Structure
```
main.py            Point d'entrée
config.py          Variables .env + constantes (rôles proposés, etc.)
core/              Le bot (chargement auto des cogs) + utilitaires
services/          Accès aux API externes (Pterodactyl, ping Minecraft) – sans code Discord
cogs/              UNE FONCTIONNALITÉ = UN FICHIER (commandes Discord)
ui/                Vues et boutons Discord réutilisables
```

## Notifications de serveurs (admin)
| Commande | Effet |
|---|---|
| `!setServer "NomDuServeur"` | Associe **ce salon** au serveur (un serveur peut avoir plusieurs salons, un salon plusieurs serveurs) |
| `!removeServer "NomDuServeur"` | Retire l'association pour ce salon (alias : `!unsetServer`) |

Une fois associé, le salon reçoit : ouverture (avec la mention de la personne qui a cliqué sur ▶️ Démarrer),
fermeture, et connexion d'un joueur. Le bot écoute le websocket de Pterodactyl (temps réel, pas de polling).
Les associations sont sauvegardées dans `data/server_links.json` (volume Docker `bot-data`).

## Ajouter une fonctionnalité
1. `cp cogs/_template.py cogs/ma_fonction.py`
2. Modifie la classe et ajoute tes commandes
3. Relance le bot : le fichier est détecté et chargé tout seul.

Pour désactiver une fonctionnalité sans la supprimer : renomme son fichier avec un `_` devant
(`cogs/roles.py` → `cogs/_roles.py`).

## Règle d'or
- `services/` : parle aux API, ne connaît pas Discord.
- `cogs/` : reçoit les commandes, appelle les services, construit les messages.
- `ui/` : boutons / menus partagés entre plusieurs cogs.
