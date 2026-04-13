# 🤖 Bot Discord — Minecraft Pterodactyl

Bot Discord pour monitorer et contrôler tes serveurs Minecraft hébergés sur Pterodactyl.

---

## 📦 Installation

```bash
# 1. Cloner / copier les fichiers dans un dossier
cd /opt/minecraft-bot

# 2. Créer un environnement virtuel Python
python3 -m venv venv
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer le .env
cp .env.example .env
nano .env
```

---

## ⚙️ Configuration du `.env`

| Variable              | Description                                                  |
|-----------------------|--------------------------------------------------------------|
| `DISCORD_TOKEN`       | Token de ton bot Discord (portail developer Discord)         |
| `PTERODACTYL_URL`     | URL de ton panel Pterodactyl (ex: `https://panel.exemple.com`) |
| `PTERODACTYL_API_KEY` | **Client** API Key (dans Account > API Credentials)          |

> ⚠️ Utilise bien une **Client API Key** (`ptlc_...`), pas une Application Key.

---

## 🚀 Lancement

```bash
# Manuel
source venv/bin/activate
python bot.py

# Ou avec systemd (recommandé sur Proxmox/VM)
```

### Service systemd (optionnel)

Crée `/etc/systemd/system/minecraft-bot.service` :

```ini
[Unit]
Description=Discord Minecraft Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/minecraft-bot
ExecStart=/opt/minecraft-bot/venv/bin/python bot.py
Restart=always
RestartSec=5
User=www-data

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now minecraft-bot
systemctl status minecraft-bot
```

---

## 🎮 Commandes

| Commande                       | Description                                      |
|--------------------------------|--------------------------------------------------|
| `!status [NomDuServeur]`       | Affiche l'état + ressources du serveur           |
| `!servers`                     | Liste tous les serveurs disponibles              |

### Exemple

```
!status Survival
!status Creative_2
```

Le bot affichera un embed avec :
- 🟢 État (En ligne / Hors ligne / Démarrage…)
- RAM, CPU, Disque utilisés
- Uptime
- Boutons **Démarrer / Arrêter / Redémarrer** selon l'état actuel

---

## 🔒 Sécurité

- Restreins les commandes à un canal spécifique si besoin en ajoutant une vérification `ctx.channel.id`.
- Ne partage jamais ton `.env`.
