<<<<<<< HEAD
# Bot Discord – Gestion de serveurs Minecraft (Pterodactyl)
=======
# Bot Discord — Gestion serveurs Minecraft

## Structure du projet

```
minecraft-bot/
├── main.py                    # Point d'entrée : lance le bot, charge les cogs
├── config.py                  # Variables d'environnement, rôles, IPs des serveurs
├── requirements.txt
├── .env.example                # Modèle du fichier .env à créer
│
├── services/                  # Logique métier (aucun code Discord ici)
│   ├── pterodactyl.py          # Client API Pterodactyl (session réutilisée)
│   ├── minecraft.py            # Ping direct des serveurs (mcstatus)
│   └── server_service.py       # Combine les deux : construit un statut complet
│
├── views/                     # Composants d'interface Discord (boutons)
│   ├── server_control.py       # Boutons start/stop/restart
│   └── role_selection.py       # Boutons de rôles + création automatique
│
└── cogs/                      # Commandes Discord, regroupées par thème
    ├── server_commands.py       # !status, !servers, !whitelist
    └── role_commands.py         # !ServerRoleSelection
```

## Pourquoi cette organisation ?

- **`config.py`** : toutes les valeurs modifiables (rôles, IPs, tokens) sont à un seul endroit.
- **`services/`** : la logique "métier" (appels API, ping Minecraft) est totalement indépendante
  de Discord. Elle pourrait être testée ou réutilisée ailleurs sans discord.py.
- **`views/`** : chaque composant d'interface (boutons) est isolé dans son propre fichier.
- **`cogs/`** : chaque commande Discord ne fait plus qu'appeler `server_service` et construire
  l'embed. Toute la complexité (Pterodactyl, mcstatus) est cachée derrière.

Avantage concret : pour ajouter une commande, tu écris un fichier dans `cogs/` qui utilise
`ServerService` — pas besoin de comprendre comment fonctionne l'API Pterodactyl.

## Nouveauté : création automatique des rôles

Avant, si un rôle défini dans `ROLE_CHOICES` n'existait pas sur le serveur, le bot affichait
une erreur ("crée-le d'abord"). Maintenant :

- Quand un admin lance `!ServerRoleSelection`, le bot vérifie chaque rôle de la config
  (`views/role_selection.py::ensure_roles_exist`) et **crée automatiquement** ceux qui manquent,
  avec la couleur définie dans `config.py`.
- En filet de sécurité, si un rôle est supprimé *après* l'affichage du menu (entre le moment où
  le menu est affiché et le clic sur le bouton), il est recréé à la volée.

Pour ajouter un rôle : il suffit d'ajouter une ligne dans `ROLE_CHOICES` (`config.py`), rien
d'autre à toucher.

```python
ROLE_CHOICES: list[RoleChoice] = [
    RoleChoice("StonksVillien", "Joueur du serveur Stonks Ville"),
    RoleChoice("NouveauRole", "Description du nouveau rôle", color=0xFF0000),
]
```

## Installation
>>>>>>> 94f5a8d7946fd71b7dd35daace29094c052087ac

## Installation
```bash
<<<<<<< HEAD
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
=======
pip install -r requirements.txt
cp .env.example .env
# Remplir .env avec ton token Discord, l'URL du panel et la clé API Pterodactyl

python main.py
```

## Commandes disponibles

| Commande | Description |
|---|---|
| `!status <NomServeur>` | Affiche le statut détaillé d'un serveur (IP, joueurs, whitelist, boutons start/stop/restart) |
| `!servers` | Liste tous les serveurs avec un résumé rapide |
| `!whitelist add\|remove <NomServeur> <Pseudo>` | Ajoute/retire un joueur de la whitelist |
| `!ServerRoleSelection` | (Admin) Crée les rôles manquants + affiche le menu de sélection de rôles |

## Points d'attention

- Le token Discord et la clé API Pterodactyl doivent rester dans `.env` (jamais commités).
- Le bot doit avoir la permission **"Gérer les rôles"** sur le serveur Discord pour pouvoir créer
  des rôles automatiquement, et son propre rôle doit être positionné au-dessus des rôles qu'il crée.
>>>>>>> 94f5a8d7946fd71b7dd35daace29094c052087ac
