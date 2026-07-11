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

```bash
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
