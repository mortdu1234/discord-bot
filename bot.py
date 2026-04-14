from http import server

import discord
from discord.ext import commands
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PTERODACTYL_URL = os.getenv("PTERODACTYL_URL")         # ex: http://192.168.1.50:80
PTERODACTYL_API_KEY = os.getenv("PTERODACTYL_API_KEY") # Client API Key (ptlc_...)

# Charge les IPs depuis le .env : "Survival=192.168.1.50:25565,Creative=192.168.1.50:25566"
def load_server_ips() -> dict:
    raw = os.getenv("SERVER_IPS", "")
    ips = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if "=" in entry:
            name, ip = entry.split("=", 1)
            ips[name.strip().lower()] = ip.strip()
    return ips

SERVER_IPS = load_server_ips()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Helpers API Pterodactyl ──────────────────────────────────────────────────   
def ptero_headers():
    return {
        "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

async def get_all_servers():
    """Retourne la liste de tous les serveurs accessibles par le compte."""
    url = f"{PTERODACTYL_URL}/api/client"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=ptero_headers()) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("data", [])
        
async def _read_server_file(identifier: str, path: str) -> str | None:
    url = f"{PTERODACTYL_URL}/api/client/servers/{identifier}/files/contents"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=ptero_headers(), params={"file": path}) as resp:
            if resp.status != 200:
                return None
            return await resp.text()
        
async def find_server(name: str):
    """Cherche un serveur par nom (insensible à la casse)."""
    servers = await get_all_servers()
    if servers is None:
        return None, "Impossible de contacter le panel Pterodactyl."
    name_lower = name.lower()
    for server in servers:
        attr = server["attributes"]
        if attr["name"].lower() == name_lower:
            return attr, None
    return None, f"Aucun serveur trouvé avec le nom **{name}**."

async def get_server_resources(identifier: str):
    """Retourne les ressources (état, RAM, CPU) d'un serveur."""
    url = f"{PTERODACTYL_URL}/api/client/servers/{identifier}/resources"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=ptero_headers()) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("attributes", {})

async def send_power_action(identifier: str, action: str):
    """Envoie une action de puissance : start, stop, restart, kill."""
    url = f"{PTERODACTYL_URL}/api/client/servers/{identifier}/power"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=ptero_headers(), json={"signal": action}) as resp:
            return resp.status == 204

async def send_console_command(identifier: str, command: str):
    """Envoie une commande console au serveur Minecraft."""
    url = f"{PTERODACTYL_URL}/api/client/servers/{identifier}/command"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=ptero_headers(), json={"command": command}) as resp:
            return resp.status == 204

async def get_server_version(identifier: str) -> str:
    """Retourne la version du serveur Minecraft (ex: 1.19.2) grâce à une lecture dans le fichier infos.txt"""
    import re
    text = await _read_server_file(identifier, "infos.txt")
    if not text:
        return "?"
    match = re.search(r"version:\s*([\d.]+)\s+(\w+)", text, re.IGNORECASE)
    if match:
        version = match.group(1)
        loader = match.group(2)
        return f"{version} ({loader})"
    return "?"

async def get_server_state(identifier: str) -> str:
    """Retourne l'état actuel du serveur (running, offline, etc.)."""
    resources = await get_server_resources(identifier)
    state_info = {
        "running":  ("🟢", "En ligne"),
        "starting": ("🟡", "Démarrage"),
        "stopping": ("🟠", "Arrêt"),
        "offline":  ("🔴", "Hors ligne"),
        "unknown":  ("⚪", "Inconnu")
    }
    if resources is None:
        resources = "unknown"
    current_state = (resources or {}).get("current_state", "unknown")
    emoji, label = state_info.get(current_state, state_info["unknown"])
    return f"{emoji} {label}"

async def get_host_and_port(identifier: str) -> tuple[str, int] | None:
    """Récupère l'IP et le port du serveur depuis les allocations de Pterodactyl."""
    servers = await get_all_servers()
    if not servers:
        return None

    server = next((s for s in servers if s["attributes"]["identifier"] == identifier), None)
    if not server:
        return None

    allocations = server["attributes"].get("relationships", {}).get("allocations", {}).get("data", [])
    
    # Prendre l'allocation par défaut, sinon la première disponible
    alloc = next((a for a in allocations if a["attributes"].get("is_default")), allocations[0] if allocations else None)
    if not alloc:
        return None

    attr = alloc["attributes"]
    host = attr.get("ip", "")
    port = int(attr.get("port", 25565))
    return host, port
    
async def get_whitelist(identifier: str):
    """Lit le fichier whitelist.json du serveur via l'API fichiers de Pterodactyl."""
    url = f"{PTERODACTYL_URL}/api/client/servers/{identifier}/files/contents?file=/whitelist.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=ptero_headers()) as resp:
            if resp.status != 200:
                return None
            try:
                text = await resp.text()
                data = json.loads(text)
                # whitelist.json : liste de {"uuid": "...", "name": "..."}
                return [entry.get("name", "?") for entry in data if isinstance(entry, dict)]
            except Exception:
                return None
            
async def get_player_count(identifier: str) -> str:
    """
    Ping le serveur Minecraft et retourne le nombre de joueurs connectés
    sous la forme '{online}/{max}'. Retourne '?/?' en cas d'échec.
    """
    from mcstatus import JavaServer

    result = await get_host_and_port(identifier)
    if result is None:
        return "?/?"

    host, port = result

    try:
        server = JavaServer.lookup(f"{host}:{port}", timeout=3)
        status = await server.async_status()
        return f"{status.players.online}/{status.players.max}"
    except Exception as e:
        print(f"[MC Ping] Erreur pour {host}:{port} → {e}")
        return "?/?"

async def get_server_ip(serverName: str) -> str:
    """Retourne l'IP publique du serveur Minecraft (depuis .env ou allocations)."""
    return SERVER_IPS.get(serverName.lower(), "Non configurée")

async def get_online_players(identifier: str) -> list[str] | None:
    """
    Retourne la liste des joueurs connectés sous forme de string.
    Ex: "Player1, Player2" ou "Aucun joueur connecté" ou "?" en cas d'erreur.
    """
    from mcstatus import JavaServer

    result = await get_host_and_port(identifier)
    if result is None:
        return None

    host, port = result

    try:
        server = JavaServer.lookup(f"{host}:{port}", timeout=3)
        status = await server.async_status()

        online = status.players.online
        player_list = status.players.sample or []

        if online == 0:
            return None
        return [player.name for player in player_list]  

    except Exception as e:
        print(f"[MC Ping] Erreur get_online_players {host}:{port} → {e}")
        return None

async def get_server_ping(identifier: str) -> float | None:
    """
    Retourne la latence du serveur en ms (float).
    Retourne None en cas d'erreur.
    """
    from mcstatus import JavaServer

    result = await get_host_and_port(identifier)
    if result is None:
        return None

    host, port = result

    try:
        server = JavaServer.lookup(f"{host}:{port}", timeout=3)
        latency = await server.async_ping()
        return round(latency, 1)

    except Exception as e:
        print(f"[MC Ping] Erreur get_server_ping {host}:{port} → {e}")
        return None

# ─── Commandes Discord ────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()

@bot.command(name="status")
async def status(ctx, *, server_name: str | None = None):
    """!status [NomDuServeur] — Affiche le statut d'un serveur Minecraft."""
    if not server_name:
        await ctx.send("❌ Usage : `!status [NomDuServeur]`")
        return

    async with ctx.typing():
        attr, error = await find_server(server_name)
        if error:
            embed = discord.Embed(title="❌ Serveur introuvable", description=error, color=0xe74c3c)
            await ctx.send(embed=embed)
            return

        server_name = attr["name"] # type: ignore
        identifier = attr["identifier"] # type: ignore
        server_state = await get_server_state(identifier)
        server_ip = await get_server_ip(server_name) # type: ignore

        if server_state.__contains__("En ligne"):
            player_count = await get_player_count(identifier)
            online_players = await get_online_players(identifier)
            server_ping = await get_server_ping(identifier)
            version = await get_server_version(identifier)
        else:
            player_count = "—"
            online_players = "—"
            server_ping = "—"
            version = "—"
        
        # online
        if online_players is None:
            online_players = "Aucun joueur connecté"
        else:
            online_players = "\n".join(
                "  ".join(f"`{p}`" for p in sorted(online_players)[i:i+3])
                for i in range(0, len(online_players), 3)
            )

        # Whitelist (lecture du fichier)
        wl_players = await get_whitelist(identifier)
        if wl_players is None:
            wl_text = "*Impossible de lire la whitelist*"
        elif len(wl_players) == 0:
            wl_text = "*Aucun joueur whitelisté*"
        else:
            wl_text = "\n".join(
                "  ".join(f"`{p}`" for p in sorted(wl_players)[i:i+3])
                for i in range(0, len(wl_players), 3)
            )

        embed = discord.Embed(title=f"{server_name}", description=f"**État :** {server_state}")
        embed.add_field(name=f"🌐 IP : `{server_ip}`", value="", inline=True)
        embed.add_field(name="👥 En ligne", value=online_players, inline=False)
        embed.add_field(name="⏱️ Latence", value=f"{server_ping} ms", inline=True)
        embed.add_field(name="🛠️ Version", value=version, inline=True)
        embed.add_field(name=f"🎮 Joueurs connectés {player_count}", value="", inline=True)
        embed.add_field(
            name=f"📋 Whitelist ({len(wl_players) if wl_players else 0} joueur(s))",
            value=wl_text,
            inline=False
        )
        embed.set_footer(text=f"Pterodactyl • ID: {identifier}")

        view = ServerControlView(identifier, server_name, server_state)
        await ctx.send(embed=embed, view=view)


@bot.command(name="servers")
async def list_servers(ctx):
    """!servers — Liste tous les serveurs disponibles."""
    async with ctx.typing():
        servers = await get_all_servers()
        if not servers:
            await ctx.send("❌ Aucun serveur trouvé ou panel inaccessible.")
            return

        embed = discord.Embed(title="Serveurs Minecraft")
        for s in servers:
            a = s["attributes"]
            ip = SERVER_IPS.get(a["name"].lower(), "Non configurée")
            server_status = await get_server_state(a["identifier"])
            version = await get_server_version(a["identifier"])
            if server_status.__contains__("En ligne"):
                players = await get_player_count(a["identifier"])
            else:
                players = "—"
            embed.add_field(
                name=a["name"],
                value=f"IP: `{ip}`\n{server_status}\n{version}\nJoueurs: {players}",
                inline=False
            )
        await ctx.send(embed=embed)


@bot.command(name="whitelist")
async def whitelist(ctx, action: str | None = None, server_name: str | None = None, pseudo: str | None = None):
    """!whitelist [add/remove] [NomServeur] [Pseudo] — Ajoute ou retire un joueur de la whitelist."""
    if action not in ["add", "remove"] or not server_name or not pseudo:
        await ctx.send("❌ Usage : `!whitelist [add/remove] [NomDuServeur] [PseudoMinecraft]`")
        return

    async with ctx.typing():
        attr, error = await find_server(server_name)
        if error or attr is None:
            embed = discord.Embed(title="❌ Serveur introuvable", description=error, color=0xe74c3c)
            await ctx.send(embed=embed)
            return

        identifier = attr["identifier"]
        state = await get_server_state(identifier)
        if not state.__contains__("En ligne"):
            embed = discord.Embed(
                title="❌ Serveur hors ligne",
                description=f"Le serveur **{attr['name']}** doit être **en ligne** pour modifier la whitelist."
            )
            await ctx.send(embed=embed)
            return

        success = await send_console_command(identifier, f"whitelist {action} {pseudo}")
        if success:
            embed = discord.Embed(
                title="✅ Whitelist mise à jour",
                description=f"**{pseudo}** a été { 'ajouté' if action == 'add' else 'retiré' } de la whitelist de **{attr['name']}**."
            )
            embed.set_footer(text=f"Commande exécutée par {ctx.author.display_name}")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Impossible d'envoyer la commande au serveur.")


# ─── Vue avec boutons de contrôle ────────────────────────────────────────────

class ServerControlView(discord.ui.View):
    def __init__(self, identifier: str, server_name: str, current_state: str):
        super().__init__(timeout=120)
        self.identifier = identifier
        self.server_name = server_name

        if current_state.__contains__("En ligne"):
            self.add_item(PowerButton("🔁 Redémarrer",  "restart", discord.ButtonStyle.primary,  identifier))
            self.add_item(PowerButton("⏹️ Arrêter",     "stop",    discord.ButtonStyle.danger,   identifier))
        else:
            self.add_item(PowerButton("▶️ Démarrer",    "start",   discord.ButtonStyle.success, identifier))


class PowerButton(discord.ui.Button):
    def __init__(self, label: str, action: str, style: discord.ButtonStyle, identifier: str):
        super().__init__(label=label, style=style)
        self.action = action
        self.identifier = identifier

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        success = await send_power_action(self.identifier, self.action)
        if success:
            labels = {"start": "démarrage", "stop": "arrêt", "restart": "redémarrage"}
            await interaction.followup.send(
                f"✅ Commande de **{labels.get(self.action, self.action)}** envoyée avec succès !"
            )
        else:
            await interaction.followup.send("❌ Échec de l'envoi de la commande.")
        for item in self.view.children:
            item.disabled = True
        await interaction.message.edit(view=self.view)


# ─── Lancement ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)